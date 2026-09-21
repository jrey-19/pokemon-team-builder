from pkmn_teambuilder.db import get_connection, migrate
conn = get_connection()
migrate(conn)