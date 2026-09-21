import sqlite3
import pytest
from pkmn_teambuilder.db import migrate
from pkmn_teambuilder.ingest import insert_pokemon, insert_all

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    yield conn
    conn.close()

def make_fake_pokemon(id=6, name="charizard", species_id=6):
    return {
        "id": id,
        "species_id": species_id,
        "name": name,
        "types": ["fire", "flying"],
        "hp": 78, "attack": 84, "defense": 78,
        "special-attack": 109, "special-defense": 85, "speed": 100,
        "abilities": [
            {"name": "blaze", "is_hidden": False},
            {"name": "solar-power", "is_hidden": True},
        ],
        "moves": ["flamethrower", "fly"],
        "sprite": "url",
    }


# pokemon table

def test_insert_pokemon_creates_one_row(conn):
    insert_pokemon(conn, make_fake_pokemon())
    count = conn.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
    assert count == 1

def test_insert_pokemon_stores_correct_stats(conn):
    insert_pokemon(conn, make_fake_pokemon())
    row = conn.execute("SELECT hp, speed FROM pokemon WHERE id = 6").fetchone()
    assert row == (78, 100)


# types

def test_dual_type_pokemon_gets_two_rows(conn):
    insert_pokemon(conn, make_fake_pokemon())
    count = conn.execute("SELECT COUNT(*) FROM pokemon_types WHERE pokemon_id = 6").fetchone()[0]
    assert count == 2

def test_single_type_pokemon_gets_one_row(conn):
    p = make_fake_pokemon(id=1, name="bulbasaur")
    p["types"] = ["grass"]
    insert_pokemon(conn, p)
    count = conn.execute("SELECT COUNT(*) FROM pokemon_types WHERE pokemon_id = 1").fetchone()[0]
    assert count == 1

def test_shared_type_is_not_duplicated_in_types_table(conn):
    insert_pokemon(conn, make_fake_pokemon(id=6, name="charizard"))
    insert_pokemon(conn, make_fake_pokemon(id=7, name="charizard2"))
    count = conn.execute("SELECT COUNT(*) FROM types WHERE name = 'fire'").fetchone()[0]
    assert count == 1 # fire only appears once


# abilities

def test_pokemon_gets_both_abilities(conn):
    insert_pokemon(conn, make_fake_pokemon())
    count = conn.execute("SELECT COUNT(*) FROM pokemon_abilities WHERE pokemon_id = 6").fetchone()[0]
    assert count == 2

def test_hidden_ability_flag_is_correct(conn):
    insert_pokemon(conn, make_fake_pokemon())
    rows = conn.execute(
        """SELECT a.name, pa.is_hidden FROM pokemon_abilities pa
           JOIN abilities a ON pa.ability_id = a.id
           WHERE pa.pokemon_id = 6"""
    ).fetchall()
    assert ("blaze", 0) in rows
    assert ("solar-power", 1) in rows


# moves

def test_pokemon_gets_all_moves(conn):
    insert_pokemon(conn, make_fake_pokemon())
    count = conn.execute("SELECT COUNT(*) FROM pokemon_moves WHERE pokemon_id = 6").fetchone()[0]
    assert count == 2


# idempotency

def test_insert_pokemon_twice_does_not_duplicate(conn):
    insert_pokemon(conn, make_fake_pokemon())
    insert_pokemon(conn, make_fake_pokemon())