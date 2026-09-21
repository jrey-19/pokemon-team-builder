from db import get_connection, migrate
conn = get_connection()
migrate(conn)