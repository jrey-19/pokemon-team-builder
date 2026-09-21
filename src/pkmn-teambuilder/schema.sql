CREATE TABLE pokemon (
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

CREATE TABLE types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
); 

CREATE TABLE pokemon_types (
    pokemon_id INTEGER PRIMARY KEY,
    type_id INTEGER,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (type_id) REFERENCES types(id)
);

CREATE TABLE moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);

CREATE TABLE pokemon_moves (
    pokemon_id INTEGER,
    move_id INTEGER,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (move_id) REFERENCES moves(id)
);

CREATE TABLE abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);

CREATE TABLE pokemon_abilities (
    pokemon_id INTEGER,
    ability_id INTEGER,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
);

CREATE TABLE type_matchups (
    attacker_type_id INTEGER,
    defender_type_id INTEGER,
    multiplier REAL,
    PRIMARY KEY (attacker_type_id, defender_type_id),
    FOREIGN KEY (attacker_type_id) REFERENCES types(id),
    FOREIGN KEY (defender_type_id) REFERENCES types(id)
);

CREATE INDEX idx_pokemon_types_pokemon_id ON pokemon_types(pokemon_id);
CREATE INDEX idx_pokemon_moves_pokemon_id ON pokemon_moves(pokemon_id);
CREATE INDEX idx_pokemon_abilities_pokemon_id ON pokemon_abilities(pokemon_id);