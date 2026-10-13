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
    
    def find_pokemon(self, filters: list[dict] | None = None) -> list[dict]:
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

        return self._query(sql, tuple(params))
    
    def team_type_coverage(self, team: list[int]) -> dict:
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
        offense_types: set[str] = set()

        for pokemon_id in team:
            rows = self._query(
                """SELECT t.id, t.name FROM pokemon_types pt
                JOIN types t ON pt.type_id = t.id
                WHERE pt.pokemon_id = ?""",
                (pokemon_id,),
            )
            if not rows:
                raise ValueError(f"No such pokemon id: {pokemon_id}")
            defending_type_ids = [row["id"] for row in rows]

            per_pokemon_defense = {}
            for attacker_id, attacker_name in all_types.items():
                multiplier = 1.0
                for defender_id in defending_type_ids:
                    multiplier *= matchups.get((attacker_id, defender_id), 1.0)
                per_pokemon_defense[attacker_name] = multiplier
            defense[pokemon_id] = per_pokemon_defense
            for attacker_id in defending_type_ids:
                for defender_id, defender_name in all_types.items():
                    if matchups.get((attacker_id, defender_id), 1.0) > 1.0:
                        offense_types.add(defender_name)

        return {"defense": defense, "offense": sorted(offense_types)}
if __name__ == "__main__":
    tb = TeamBuilder(get_connection())
    print([p["name"] for p in tb.find_pokemon([{"field": "type", "op": "=", "value": "fire"}, {"field": "type", "op": "=", "value": "flying"}])])