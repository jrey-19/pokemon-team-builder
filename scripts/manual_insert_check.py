from pkmn_teambuilder.db import get_connection, migrate
from pkmn_teambuilder.ingest import insert_pokemon, load_from_json

data = load_from_json("data/raw/pokemon_data.json")
conn = get_connection()
migrate(conn)
insert_pokemon(conn, data[9])
print(f"Inserted {data[9]['name']} — check your SQLite viewer")