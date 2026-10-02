from pkmn_teambuilder.db import get_connection, migrate
from pkmn_teambuilder.ingest import backfill_ability_effects, backfill_move_details, insert_all, load_from_json, seed_type_matchups

data = load_from_json("data/raw/pokemon_data.json")
conn = get_connection()
migrate(conn)
backfill_ability_effects(conn)
backfill_move_details(conn)
insert_all(conn, data)
seed_type_matchups(conn)
print(f"Done. Inserted {len(data)} pokemon.")