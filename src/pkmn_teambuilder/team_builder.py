import sqlite3

from pkmn_teambuilder.db import get_connection
class TeamBuilder:
    FIELD_COLUMNS = {
        "name": "p.name",
        "hp": "p.hp",
        "attack": "p.attack",
        "defense": "p.defense",
        "special_attack": "p.special_attack",
        "special_defense": "p.special_defense",
        "speed": "p.speed",
    }

    ALLOWED_OPS = {"=", "!=", ">", ">=", "<", "<="}

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        cur = self.conn.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def find_pokemon(self, filters: list[dict] | None = None, *, limit: int | None = None, offset: int = 0) -> list[dict]:
        if limit is not None and limit <= 0:
            raise ValueError("limit must be a positive integer")
        if offset < 0:
            raise ValueError("offset must be a non-negative integer")
        sql = (
            "SELECT DISTINCT p.id, p.name, p.hp, p.attack, p.defense, "
            "p.special_attack, p.special_defense, p.speed FROM pokemon p"
        )
        joins: list[str] = []
        conditions: list[str] = []
        params: list = []
        joined_types = False
        joined_moves = False
        type_values: list = []
        move_values: list = []

        for f in filters or []:
            field, op, value = f["field"], f["op"], f["value"]

            if op not in self.ALLOWED_OPS:
                raise ValueError(f"Unsupported operator: {op!r}")

            if field in self.FIELD_COLUMNS:
                column = self.FIELD_COLUMNS[field]
                conditions.append(f"{column} {op} ?")
                params.append(value)

            elif field == "type":
                if op != "=":
                    raise ValueError("'type' filter only supports '='")
                if not joined_types:
                    joins.append("JOIN pokemon_types pt ON p.id = pt.pokemon_id")
                    joins.append("JOIN types t ON pt.type_id = t.id")
                    joined_types = True
                type_values.append(value)

            elif field == "move":
                if op != "=":
                    raise ValueError("'move' filter only supports '='")
                if not joined_moves:
                    joins.append("JOIN pokemon_moves pm ON p.id = pm.pokemon_id")
                    joins.append("JOIN moves m ON pm.move_id = m.id")
                    joined_moves = True
                move_values.append(value)

            else:
                raise ValueError(f"Unsupported field: {field!r}")

        having_parts: list[str] = []

        if type_values:
            placeholders = ",".join("?" for _ in type_values)
            conditions.append(f"t.name IN ({placeholders})")
            params.extend(type_values)
            if len(type_values) > 1:
                having_parts.append("COUNT(DISTINCT t.name) = ?")

        if move_values:
            placeholders = ",".join("?" for _ in move_values)
            conditions.append(f"m.name IN ({placeholders})")
            params.extend(move_values)
            if len(move_values) > 1:
                having_parts.append("COUNT(DISTINCT m.name) = ?")

        if joins:
            sql += " " + " ".join(joins)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        if having_parts:
            sql += " GROUP BY p.id HAVING " + " AND ".join(having_parts)
            if len(type_values) > 1:
                params.append(len(type_values))
            if len(move_values) > 1:
                params.append(len(move_values))
        sql += " ORDER BY p.name"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit if limit is not None else -1, offset])
        return self._query(sql, tuple(params))
    
    def team_type_coverage(self,team: list[int], moves: dict[int, list[str]] | None = None) -> dict:
        if not team:
            raise ValueError("team must contain at least one pokemon id")

        all_types = {row["id"]: row["name"] for row in self._query("SELECT id, name FROM types")}
        matchups = {
            (row["attacker_type_id"], row["defender_type_id"]): row["multiplier"]
            for row in self._query(
                "SELECT attacker_type_id, defender_type_id, multiplier FROM type_matchups"
            )
        }

        defense: dict[int, dict[str, float]] = {}
        members: dict[int, dict] = {}
        offense_types: set[str] = set()

        for pokemon_id in team:
            rows = self._query(
                """SELECT p.name AS pokemon_name, t.id, t.name
                   FROM pokemon p
                   JOIN pokemon_types pt ON pt.pokemon_id = p.id
                   JOIN types t ON pt.type_id = t.id
                   WHERE p.id = ?""",
                (pokemon_id,),
            )
            if not rows:
                raise ValueError(f"No such pokemon id: {pokemon_id}")
            pokemon_name = rows[0]["pokemon_name"]
            own_type_ids = [row["id"] for row in rows]

            # defense (how the pokemon takes damage)
            per_pokemon_defense = {}
            for attacker_id, attacker_name in all_types.items():
                multiplier = 1.0
                for own_id in own_type_ids:
                    multiplier *= matchups.get((attacker_id, own_id), 1.0)
                per_pokemon_defense[attacker_name] = multiplier
            defense[pokemon_id] = per_pokemon_defense

            weak_to = dict(sorted(
                ((t, m) for t, m in per_pokemon_defense.items() if m > 1.0),
                key=lambda kv: (-kv[1], kv[0]),
            ))
            resists = dict(sorted(
                ((t, m) for t, m in per_pokemon_defense.items() if 0.0 < m < 1.0),
                key=lambda kv: (kv[1], kv[0]),
            ))
            immune_to = sorted(t for t, m in per_pokemon_defense.items() if m == 0.0)

            # offense (moves if given, otherwise just STAB)
            chosen = moves.get(pokemon_id) if moves else None
            if chosen:
                attacker_type_ids = self._damaging_move_type_ids(pokemon_id, chosen)
            else:
                attacker_type_ids = set(own_type_ids)

            # Best multiplier across its attacking types, per defending type.
            if attacker_type_ids:
                best = {
                    defender_name: max(
                        matchups.get((a, defender_id), 1.0) for a in attacker_type_ids
                    )
                    for defender_id, defender_name in all_types.items()
                }
            else:
                best = {}

            super_effective = sorted(t for t, m in best.items() if m > 1.0)
            not_very_effective = sorted(t for t, m in best.items() if 0.0 < m < 1.0)
            no_effect = sorted(t for t, m in best.items() if m == 0.0)
            offense_types.update(super_effective)

            members[pokemon_id] = {
                "name": pokemon_name,
                "types": [row["name"] for row in rows],
                "attacking_types": sorted(all_types[a] for a in attacker_type_ids),
                "weak_to": weak_to,
                "resists": resists,
                "immune_to": immune_to,
                "super_effective_against": super_effective,
                "not_very_effective_against": not_very_effective,
                "no_effect_against": no_effect,
            }

        return {"defense": defense, "offense": sorted(offense_types), "members": members}

    def _damaging_move_type_ids(self, pokemon_id: int, move_names: list[str]) -> set[int]:
        placeholders = ",".join("?" for _ in move_names)
        rows = self._query(
            f"""SELECT m.name, m.type_id, m.power
                FROM pokemon_moves pm
                JOIN moves m ON pm.move_id = m.id
                WHERE pm.pokemon_id = ? AND m.name IN ({placeholders})""",
            (pokemon_id, *move_names),
        )
        unknown = set(move_names) - {row["name"] for row in rows}
        if unknown:
            raise ValueError(f"pokemon {pokemon_id} cannot learn: {sorted(unknown)}")
        return {row["type_id"] for row in rows if row["power"] is not None}

    # types the team has no coverage against
    def suggest_coverage_gaps(self,team: list[int],moves: dict[int, list[str]] | None = None) -> list[str]:
        report = self.team_type_coverage(team, moves)
        all_type_names = {row["name"] for row in self._query("SELECT name FROM types")}
        return sorted(all_type_names - set(report["offense"]))
    
if __name__ == "__main__":
    tb = TeamBuilder(get_connection())
    print([p["name"] for p in tb.find_pokemon([{"field": "type", "op": "=", "value": "fire"}, {"field": "type", "op": "=", "value": "flying"}])])
    print(tb.team_type_coverage([6, 1], moves={6: ["flamethrower", "earthquake"]}))  # charizard and mega charizard