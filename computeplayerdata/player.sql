CREATE TABLE IF NOT EXISTS player (
    player_id TEXT PRIMARY KEY,
    player_name TEXT,
    position TEXT,
    bats TEXT,
    throws TEXT,
    height INTEGER,
    weight INTEGER,
    dob DATE,
    birthplace TEXT,
    debut_date DATE,
    jersey_numbers TEXT,
    photo_link TEXT
);