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
        row = conn.execute("SELECT id FROM pokemon WHERE name = ?", (name,)).fetchone()
        assert row is not None, f"{name} not in database"
        return row[0]

    return _pid


def test_coverage_gaps_for_mono_fire_team(tb, pid):
    gaps = tb.suggest_coverage_gaps([pid("charmander")])
    assert "water" in gaps
    assert "grass" not in gaps

# find_pokemon tests
def test_find_pokemon_by_type(tb):
    names = {p["name"] for p in tb.find_pokemon([{"field": "type", "op": "=", "value": "fire"}])}
    assert "charizard" in names
    assert "bulbasaur" not in names


def test_find_pokemon_min_speed(tb):
    results = tb.find_pokemon([{"field": "speed", "op": ">=", "value": 100}])
    assert results
    assert all(p["speed"] >= 100 for p in results)


def test_find_pokemon_combines_filters(tb):
    results = tb.find_pokemon([
        {"field": "type", "op": "=", "value": "electric"},
        {"field": "speed", "op": ">=", "value": 100},
    ])
    assert results
    assert all(p["speed"] >= 100 for p in results)


def test_find_pokemon_requires_all_listed_types(tb):
    names = {p["name"] for p in tb.find_pokemon([
        {"field": "type", "op": "=", "value": "fire"},
        {"field": "type", "op": "=", "value": "flying"},
    ])}
    assert "charizard" in names
    assert "talonflame" in names
    assert "charmander" not in names


def test_find_pokemon_by_move(tb):
    names = {p["name"] for p in tb.find_pokemon([{"field": "move", "op": "=", "value": "flamethrower"}])}
    assert "charizard" in names


def test_find_pokemon_requires_all_listed_moves(tb):
    names = {p["name"] for p in tb.find_pokemon([
        {"field": "move", "op": "=", "value": "flamethrower"},
        {"field": "move", "op": "=", "value": "fly"},
    ])}
    assert "charizard" in names
    assert "bulbasaur" not in names


def test_find_pokemon_no_filters_returns_everyone(tb):
    assert len(tb.find_pokemon()) > 1000


# bad input
def test_find_pokemon_rejects_bad_field(tb):
    with pytest.raises(ValueError):
        tb.find_pokemon([{"field": "name'; DROP TABLE pokemon; --", "op": "=", "value": "x"}])


def test_find_pokemon_rejects_bad_op(tb):
    with pytest.raises(ValueError):
        tb.find_pokemon([{"field": "speed", "op": "; DROP TABLE pokemon; --", "value": 1}])

# team_type_coverage tests
def test_dual_type_multiplies(tb, pid):
    charizard = pid("charizard")
    defense = tb.team_type_coverage([charizard])["defense"][charizard]
    assert defense["rock"] == 4.0    # 2 x 2
    assert defense["ground"] == 0.0  # 2 x 0
    assert defense["fire"] == 0.5    # 0.5 x 1


def test_ghost_poison_immunities(tb, pid):
    gengar = pid("gengar")
    defense = tb.team_type_coverage([gengar])["defense"][gengar]
    assert defense["normal"] == 0.0
    assert defense["fighting"] == 0.0
    assert defense["dark"] == 2.0


def test_offense_lists_super_effective_targets(tb, pid):
    offense = tb.team_type_coverage([pid("charmander")])["offense"]
    assert "grass" in offense
    assert "water" not in offense


def test_team_type_coverage_rejects_empty_team(tb):
    with pytest.raises(ValueError):
        tb.team_type_coverage([])


def test_team_type_coverage_rejects_unknown_id(tb):
    with pytest.raises(ValueError):
        tb.team_type_coverage([999999])

def test_type_chart_is_complete(conn):
    total = conn.execute("SELECT COUNT(*) FROM type_matchups").fetchone()[0]
    immunities = conn.execute(
        "SELECT COUNT(*) FROM type_matchups WHERE multiplier = 0"
    ).fetchone()[0]
    assert total == 324
    assert immunities == 8

# coverage tests
def test_coverage_gaps_for_mono_fire_team(tb, pid):
    gaps = tb.suggest_coverage_gaps([pid("charmander")])
    assert "water" in gaps
    assert "grass" not in gaps

def test_offense_uses_chosen_moves(tb, pid):
    cid = pid("charizard")
    offense = tb.team_type_coverage([cid], moves={cid: ["earthquake"]})["offense"]
    assert offense == ["electric", "fire", "poison", "rock", "steel"]  # super-effective targets for earthquake

def test_team_type_coverage_rejects_unlearnable_move(tb, pid):
    cid = pid("charizard")
    with pytest.raises(ValueError):
        tb.team_type_coverage([cid], moves={cid: ["not-a-move"]})


def test_members_report_for_charizard(tb, pid):
    cid = pid("charizard")
    m = tb.team_type_coverage([cid])["members"][cid]
    assert m["name"] == "charizard"
    assert m["weak_to"]["rock"] == 4.0
    assert m["immune_to"] == ["ground"]
    assert "grass" in m["super_effective_against"]
    assert m["not_very_effective_against"] == ["rock"]

def test_find_pokemon_pagination(tb):
    filters = [{"field": "type", "op": "=", "value": "fire"}]
    all_matches = tb.find_pokemon(filters)

    assert len(all_matches) > 10
    assert tb.find_pokemon(filters, limit=5, offset=5) == all_matches[5:10]
    assert tb.find_pokemon(filters, offset=5) == all_matches[5:]
    assert tb.find_pokemon(filters, offset=len(all_matches)) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": -1},
        {"offset": -1},
    ],
)
def test_find_pokemon_rejects_invalid_pagination(tb, kwargs):
    with pytest.raises(ValueError):
        tb.find_pokemon(**kwargs)

@pytest.mark.parametrize(
    "filters",
    [
        None,
        [{"field": "type", "op": "=", "value": "fire"}],
        [
            {"field": "type", "op": "=", "value": "fire"},
            {"field": "type", "op": "=", "value": "flying"},
        ],
        [
            {"field": "move", "op": "=", "value": "flamethrower"},
            {"field": "move", "op": "=", "value": "fly"},
        ],
        [{"field": "name", "op": "=", "value": "not-a-pokemon"}],
    ],
)
def test_count_pokemon_matches_full_results(tb, filters):
    assert tb.count_pokemon(filters) == len(tb.find_pokemon(filters))

def test_get_pokemon_moves(tb, pid):
    moves = tb.get_pokemon_moves(pid("charizard"))
    by_name = {move["name"]: move for move in moves}

    assert "flamethrower" in by_name
    assert by_name["flamethrower"]["type"] == "fire"
    assert by_name["flamethrower"]["damage_class"] == "special"
    assert by_name["flamethrower"]["power"] is not None
    assert [move["name"] for move in moves] == sorted(by_name)


def test_get_pokemon_moves_rejects_unknown_id(tb):
    with pytest.raises(ValueError, match="No such pokemon id"):
        tb.get_pokemon_moves(999999)