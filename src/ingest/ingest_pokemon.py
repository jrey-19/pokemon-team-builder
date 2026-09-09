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

if __name__ == "__main__":
    test = fetch_and_parse(["pikachu", "charizard", "bulbasaur"])
    print(test)