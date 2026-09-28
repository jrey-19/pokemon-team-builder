import requests
import sqlite3
import json
import time

def fetch_pokemon(name: str) -> dict:
    time.sleep(0.05)
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
    response.raise_for_status()
    return response.json()

def parse_pokemon(data: dict) -> dict:
    stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
    return {
        "id": data['id'],
        "species_id": data['species']['url'].rstrip('/').split('/')[-1],
        "name": data['name'],
        "types": [t['type']['name'] for t in data['types']],
        "hp": stats['hp'],
        "attack": stats['attack'],
        "defense": stats['defense'],
        "special-attack": stats['special-attack'],
        "special-defense": stats['special-defense'],
        "speed": stats['speed'],
        "abilities": [{"name": a['ability']['name'], "is_hidden": a['is_hidden']} for a in data['abilities']
],
        "moves": [move['move']['name'] for move in data['moves']],
        "sprite": data['sprites']['front_default']
    }

def fetch_and_parse(names: list[str]) -> dict:
    results = []
    failed = []
    for i, name in enumerate(names, 1):
        try:
            data = fetch_pokemon(name)
            parsed = parse_pokemon(data)
            results.append(parsed)
            print(f"[{i}/{len(names)}] {parsed['name']}")
        except Exception as e:
            print(f"[{i}/{len(names)}] Failed to fetch {name}: {e}")
            failed.append(name)
    if failed:
        print(f"Failed to fetch {len(failed)} pokemon: {', '.join(failed)}")
    return results

def get_variety_names(species_name: str) -> list[str]:
    time.sleep(0.05)
    url = f"https://pokeapi.co/api/v2/pokemon-species/{species_name.lower()}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [variety['pokemon']['name'] for variety in data['varieties']]

def get_all_species() -> list[str]:
    time.sleep(0.05)
    url = "https://pokeapi.co/api/v2/pokemon-species?limit=10000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [species["name"] for species in data["results"]]

def get_all_varieties(species_names: list[str]) -> list[str]:
    all_names = []
    for i, species in enumerate(species_names, 1):
        varieties = get_variety_names(species)
        for variety in varieties:
            all_names.append(variety)
            if variety == species:
                print(f"[{i}] {variety}")
            else:
                print(f"    {variety}")
    return all_names

def save_to_json(data: list[dict], filename: str = "data/raw/pokemon_data.json") -> None:
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved {len(data)} records to {filename}")

def load_from_json(filename: str = "data/raw/pokemon_data.json") -> list[dict]:
    with open(filename) as f:
        data = json.load(f)
    print(f"Loaded {len(data)} pokemon from {filename}")
    return data

def insert_pokemon(conn, p: dict) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO pokemon
           (id, species_id, name, hp, attack, defense, special_attack, special_defense, speed, sprite)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (p["id"], p["species_id"], p["name"], p["hp"], p["attack"], p["defense"],
         p["special-attack"], p["special-defense"], p["speed"], p["sprite"])
    )

    for type_name in p["types"]:
        conn.execute("INSERT OR IGNORE INTO types (name) VALUES (?)", (type_name,))
        type_id = conn.execute("SELECT id FROM types WHERE name = ?", (type_name,)).fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO pokemon_types (pokemon_id, type_id) VALUES (?, ?)", (p["id"], type_id))

    for move_name in p["moves"]:
        conn.execute("INSERT OR IGNORE INTO moves (name) VALUES (?)", (move_name,))
        move_id = conn.execute("SELECT id FROM moves WHERE name = ?", (move_name,)).fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO pokemon_moves (pokemon_id, move_id) VALUES (?, ?)", (p["id"], move_id))

    for ability in p["abilities"]:
        conn.execute("INSERT OR IGNORE INTO abilities (name) VALUES (?)", (ability["name"],))
        ability_id = conn.execute("SELECT id FROM abilities WHERE name = ?", (ability["name"],)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden) VALUES (?, ?, ?)",
            (p["id"], ability_id, int(ability["is_hidden"]))
        )

    conn.commit()

def seed_type_matchups(conn, path: str = "data/raw/type_matchups.json") -> None:
    with open(path) as f:
        chart = json.load(f)

    # look up ids by name
    type_ids = {name: id for id, name in conn.execute("SELECT id, name FROM types")}

    for attacker, attacker_id in type_ids.items():
        overrides = chart.get(attacker, {})
        for defender, defender_id in type_ids.items():
            multiplier = overrides.get(defender, 1.0)
            conn.execute(
                """INSERT OR REPLACE INTO type_matchups
                   (attacker_type_id, defender_type_id, multiplier)
                   VALUES (?, ?, ?)""",
                (attacker_id, defender_id, multiplier),
            )
    conn.commit()

def insert_all(conn, pokemon_list: list[dict]) -> None:
    for i, p in enumerate(pokemon_list, 1):
        insert_pokemon(conn, p)
        print(f"[{i}/{len(pokemon_list)}] Inserted {p['name']}")

if __name__ == "__main__":
    species_names = get_all_species()
    all_variety_names = get_all_varieties(species_names)
    pokemon_list = fetch_and_parse(all_variety_names)
    save_to_json(pokemon_list)