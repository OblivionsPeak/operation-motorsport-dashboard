-- League seasons
CREATE TABLE IF NOT EXISTS seasons (
    season_id   INTEGER PRIMARY KEY,
    league_id   INTEGER NOT NULL,
    season_name TEXT    NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1,   -- 1 = current/active
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Driver cache (basic profile per cust_id)
CREATE TABLE IF NOT EXISTS drivers (
    cust_id      INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    club_name    TEXT NOT NULL DEFAULT '',
    irating      INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Season standings (no points — league uses custom scoring)
CREATE TABLE IF NOT EXISTS standings (
    season_id  INTEGER NOT NULL,
    cust_id    INTEGER NOT NULL,
    position   INTEGER NOT NULL DEFAULT 0,
    starts     INTEGER NOT NULL DEFAULT 0,
    wins       INTEGER NOT NULL DEFAULT 0,
    top5       INTEGER NOT NULL DEFAULT 0,
    laps       INTEGER NOT NULL DEFAULT 0,
    laps_led   INTEGER NOT NULL DEFAULT 0,
    incidents  INTEGER NOT NULL DEFAULT 0,
    avg_finish REAL    NOT NULL DEFAULT 0,
    avg_start  REAL    NOT NULL DEFAULT 0,
    car_number TEXT    NOT NULL DEFAULT '',
    division   INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (season_id, cust_id)
);

-- Race sessions (one row per completed event)
CREATE TABLE IF NOT EXISTS sessions (
    subsession_id INTEGER PRIMARY KEY,
    season_id     INTEGER NOT NULL,
    track_name    TEXT    NOT NULL DEFAULT '',
    session_name  TEXT    NOT NULL DEFAULT '',
    start_time    TEXT    NOT NULL DEFAULT '',
    has_results   INTEGER NOT NULL DEFAULT 0,
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Individual race results (one row per driver per race)
CREATE TABLE IF NOT EXISTS race_results (
    subsession_id INTEGER NOT NULL,
    cust_id       INTEGER NOT NULL,
    display_name  TEXT    NOT NULL DEFAULT '',
    car_number    TEXT    NOT NULL DEFAULT '',
    finish_pos    INTEGER NOT NULL DEFAULT 0,
    start_pos     INTEGER NOT NULL DEFAULT 0,
    laps          INTEGER NOT NULL DEFAULT 0,
    laps_led      INTEGER NOT NULL DEFAULT 0,
    incidents     INTEGER NOT NULL DEFAULT 0,
    best_lap      TEXT    NOT NULL DEFAULT '—',
    reason_out    TEXT    NOT NULL DEFAULT 'Running',
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (subsession_id, cust_id)
);

-- App-level config (last sync times, etc.)
CREATE TABLE IF NOT EXISTS meta (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
