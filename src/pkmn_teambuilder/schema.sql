CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    species_id INTEGER,
    name TEXT NOT NULL,
    hp INTEGER,
    attack INTEGER,
    defense INTEGER,
    special_attack INTEGER,
    special_defense INTEGER,
    speed INTEGER,
    sprite TEXT
);

CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
); 

CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INTEGER,
    type_id INTEGER,
    PRIMARY KEY (pokemon_id, type_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (type_id) REFERENCES types(id)
);

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    power INTEGER,
    accuracy INTEGER,
    pp INTEGER,
    type_id INTEGER REFERENCES types(id),
    damage_class TEXT,
    effect TEXT
);

CREATE TABLE IF NOT EXISTS pokemon_moves (
    pokemon_id INTEGER,
    move_id INTEGER,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (move_id) REFERENCES moves(id)
);

CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    effect TEXT
);

CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER,
    ability_id INTEGER,
    is_hidden INTEGER,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
);

CREATE TABLE IF NOT EXISTS type_matchups (
    attacker_type_id INTEGER,
    defender_type_id INTEGER,
    multiplier REAL,
    PRIMARY KEY (attacker_type_id, defender_type_id),
    FOREIGN KEY (attacker_type_id) REFERENCES types(id),
    FOREIGN KEY (defender_type_id) REFERENCES types(id)
);

CREATE INDEX IF NOT EXISTS idx_pokemon_types_pokemon_id ON pokemon_types(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_moves_pokemon_id ON pokemon_moves(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_abilities_pokemon_id ON pokemon_abilities(pokemon_id);