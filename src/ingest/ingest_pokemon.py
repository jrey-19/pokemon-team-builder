import requests
import sqlite3
EXCLUDE_SUFFIXES = ["-totem", "-cap" ]
EXCLUDE_EXACT = ["raticate-totem-alola", "pikachu-belle", "pikachu-rock-star", "pikachu-bell", "pikachu-pop-star", "pikachu-phd", "pikachu-libre", "pikachu-cosplay"]

def should_include(name: str) -> bool:
    if name in EXCLUDE_EXACT:
        return False
    if any(name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
        return False
    return True

def get_pokemon_data(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # example outputs
        print(f"Name: {data['name'].capitalize()}")
        print(f"Type: {[t['type']['name'] for t in data['types']]}")
        print(f"Stats: { {stat['stat']['name']: stat['base_stat'] for stat in data['stats']} }")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

def get_pokemon_varieties(pokemon_name):
    # create url 
    url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}"
    
    response = requests.get(url)
    
    # request successful
    if response.status_code == 200:
        data = response.json()
        
        print(f"Name: {data['name'].capitalize()}")
        print(f"ID: {data['id']}")
        print(f"Varieties: {[variety['pokemon']['name'] for variety in data['varieties']]}")
        for variety in data['varieties']:
            variety_url = variety['pokemon']['url']
            if should_include(variety['pokemon']['name']):
                get_pokemon_data(variety_url)
            else:
                print(f"Excluded variety: {variety['pokemon']['name']}")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

def loop_all_pokemon():
    url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for pokemon in data['results']:
            get_pokemon_varieties(pokemon['name'])


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

if __name__ == "__main__":
    test = fetch_pokemon("venusaur")
    print(parse_pokemon(test))