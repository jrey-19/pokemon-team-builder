import requests
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

if __name__ == "__main__":
    get_pokemon_data("https://pokeapi.co/api/v2/pokemon/1")