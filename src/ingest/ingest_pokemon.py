import requests
import sqlite3
import json

# Fetches raw JSON for a single Pokemon from PokeAPI
def fetch_pokemon(name: str) -> dict:
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
    response.raise_for_status()
    return response.json()

# Organizes the raw JSON into a structured dictionary with important fields
def parse_pokemon(data: dict) -> dict:
    stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
    return {
        "id": data['id'],
        "name": data['name'],
        "types": [t['type']['name'] for t in data['types']],
        "hp": stats['hp'],
        "attack": stats['attack'],
        "defense": stats['defense'],
        "special-attack": stats['special-attack'],
        "special-defense": stats['special-defense'],
        "speed": stats['speed'],
        "ability": data['abilities'][0]['ability']['name'] if data['abilities'] else None,
        "moves": [move['move']['name'] for move in data['moves']],
        "sprite": data['sprites']['front_default']
    }

def fetch_and_parse(names: list[str]) -> dict:
    results = []
    for i, name in enumerate(names, 1):
        data = fetch_pokemon(name)
        parsed = parse_pokemon(data)
        results.append(parsed)
        print(f"[{i}/{len(names)}] {parsed['name']}")
    return results

def get_variety_names(species_name: str) -> list[str]:
    url = f"https://pokeapi.co/api/v2/pokemon-species/{species_name.lower()}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [variety['pokemon']['name'] for variety in data['varieties']]

def get_all_species() -> list[str]:
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
def save_to_json(data: list[dict], filename: str = "pokemon_data.json") -> None:
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved {len(data)} records to {filename}")

def load_from_json(filename: str = "pokemon_data.json") -> list[dict]:
    with open(filename) as f:
        data = json.load(f)
    print(f"Loaded {len(data)} pokemon from {filename}")
    return data

if __name__ == "__main__":
    species_names = get_all_species()
    all_variety_names = get_all_varieties(species_names)
    pokemon_list = fetch_and_parse(all_variety_names)
    save_to_json(pokemon_list)