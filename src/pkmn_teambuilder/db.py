import sqlite3
from pathlib import Path

DB_PATH = Path("data/pokemon.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def migrate(conn: sqlite3.Connection, schema_path: Path = SCHEMA_PATH) -> None:
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()