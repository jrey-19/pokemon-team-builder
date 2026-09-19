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