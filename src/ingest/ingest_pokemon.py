import requests
import sqlite3

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
    return {name: parse_pokemon(fetch_pokemon(name)) for name in names}

def get_variety_names(species_name: str) -> list[str]:
    url = f"https://pokeapi.co/api/v2/pokemon-species/{species_name.lower()}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [variety["pokemon"]["name"] for variety in data["varieties"]]

def get_all_species() -> list[str]:
    url = "https://pokeapi.co/api/v2/pokemon-species?limit=10000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [species["name"] for species in data["results"]]

if __name__ == "__main__":

    # Parses first 10 species and varieties
    species_names = get_all_species()[:10]

    variety_names = []
    for species in species_names:
        variety_names.extend(get_variety_names(species))

    print(len(variety_names))
    print(variety_names)

    pokemon_list = fetch_and_parse(variety_names)
    print(f"Total parsed: {len(pokemon_list)}")