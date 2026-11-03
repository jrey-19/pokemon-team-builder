import pytest

from pkmn_teambuilder.db import get_connection
from pkmn_teambuilder.team_builder import TeamBuilder


@pytest.fixture(scope="session")
def conn():
    connection = get_connection()
    yield connection
    connection.close()


@pytest.fixture
def tb(conn):
    return TeamBuilder(conn)


@pytest.fixture
def pid(conn):
    def _pid(name: str) -> int:
        row = conn.execute(
            "SELECT id FROM pokemon WHERE name = ?", (name,)
        ).fetchone()
        assert row is not None, f"{name} not in database"
        return row[0]

    return _pid