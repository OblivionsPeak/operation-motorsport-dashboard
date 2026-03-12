"""Named query functions — no raw SQL in route handlers."""
from datetime import datetime, timezone
from db.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Seasons ────────────────────────────────────────────────────────────────────

def upsert_season(season_id: int, league_id: int, season_name: str, active: bool = True):
    with get_db() as db:
        db.execute('''
            INSERT INTO seasons (season_id, league_id, season_name, active, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(season_id) DO UPDATE SET
                season_name = excluded.season_name,
                active      = excluded.active,
                updated_at  = excluded.updated_at
        ''', (season_id, league_id, season_name, 1 if active else 0, _now()))


def get_seasons(league_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            'SELECT * FROM seasons WHERE league_id=? ORDER BY season_id DESC', (league_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_active_season(league_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            'SELECT * FROM seasons WHERE league_id=? AND active=1 ORDER BY season_id DESC LIMIT 1',
            (league_id,)
        ).fetchone()
    return dict(row) if row else None


# ── Drivers ────────────────────────────────────────────────────────────────────

def upsert_driver(cust_id: int, display_name: str, club_name: str = '', irating: int = 0):
    with get_db() as db:
        db.execute('''
            INSERT INTO drivers (cust_id, display_name, club_name, irating, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(cust_id) DO UPDATE SET
                display_name = excluded.display_name,
                club_name    = excluded.club_name,
                irating      = excluded.irating,
                updated_at   = excluded.updated_at
        ''', (cust_id, display_name, club_name, irating, _now()))


def get_driver(cust_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute('SELECT * FROM drivers WHERE cust_id=?', (cust_id,)).fetchone()
    return dict(row) if row else None


# ── Standings ──────────────────────────────────────────────────────────────────

def upsert_standing(season_id: int, row: dict):
    with get_db() as db:
        db.execute('''
            INSERT INTO standings
                (season_id, cust_id, position, starts, wins, top5,
                 laps, laps_led, incidents, avg_finish, avg_start,
                 car_number, division, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, cust_id) DO UPDATE SET
                position   = excluded.position,
                starts     = excluded.starts,
                wins       = excluded.wins,
                top5       = excluded.top5,
                laps       = excluded.laps,
                laps_led   = excluded.laps_led,
                incidents  = excluded.incidents,
                avg_finish = excluded.avg_finish,
                avg_start  = excluded.avg_start,
                car_number = excluded.car_number,
                division   = excluded.division,
                updated_at = excluded.updated_at
        ''', (
            season_id,
            row['cust_id'],
            row['position'],
            row['starts'],
            row['wins'],
            row['top5'],
            row['laps'],
            row['laps_led'],
            row['incidents'],
            row['avg_finish'],
            row['avg_start'],
            row['car_number'],
            row['division'],
            _now(),
        ))


def get_standings(season_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute('''
            SELECT s.*, d.display_name, d.club_name, d.irating
            FROM standings s
            LEFT JOIN drivers d ON d.cust_id = s.cust_id
            WHERE s.season_id = ?
            ORDER BY s.position ASC
        ''', (season_id,)).fetchall()
    return [dict(r) for r in rows]


# ── Sessions ───────────────────────────────────────────────────────────────────

def upsert_session(row: dict):
    with get_db() as db:
        db.execute('''
            INSERT INTO sessions
                (subsession_id, season_id, track_name, session_name,
                 start_time, has_results, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subsession_id) DO UPDATE SET
                track_name   = excluded.track_name,
                session_name = excluded.session_name,
                start_time   = excluded.start_time,
                has_results  = excluded.has_results,
                updated_at   = excluded.updated_at
        ''', (
            row['subsession_id'],
            row['season_id'],
            row.get('track_name', ''),
            row.get('session_name', ''),
            row.get('start_time', ''),
            1 if row.get('has_results') else 0,
            _now(),
        ))


def get_sessions(season_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute('''
            SELECT * FROM sessions WHERE season_id=? ORDER BY start_time DESC
        ''', (season_id,)).fetchall()
    return [dict(r) for r in rows]


def session_has_results(subsession_id: int) -> bool:
    with get_db() as db:
        row = db.execute(
            'SELECT has_results FROM sessions WHERE subsession_id=?', (subsession_id,)
        ).fetchone()
    return bool(row and row['has_results'])


# ── Race results ───────────────────────────────────────────────────────────────

def upsert_race_result(subsession_id: int, driver: dict):
    with get_db() as db:
        db.execute('''
            INSERT INTO race_results
                (subsession_id, cust_id, display_name, car_number,
                 finish_pos, start_pos, laps, laps_led,
                 incidents, best_lap, reason_out, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subsession_id, cust_id) DO UPDATE SET
                display_name = excluded.display_name,
                car_number   = excluded.car_number,
                finish_pos   = excluded.finish_pos,
                start_pos    = excluded.start_pos,
                laps         = excluded.laps,
                laps_led     = excluded.laps_led,
                incidents    = excluded.incidents,
                best_lap     = excluded.best_lap,
                reason_out   = excluded.reason_out,
                updated_at   = excluded.updated_at
        ''', (
            subsession_id,
            driver['cust_id'],
            driver['display_name'],
            driver.get('car_number', ''),
            driver['finish_pos'],
            driver['start_pos'],
            driver['laps'],
            driver['laps_led'],
            driver['incidents'],
            driver.get('best_lap', '—'),
            driver.get('reason_out', 'Running'),
            _now(),
        ))


def get_race_results(subsession_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute('''
            SELECT * FROM race_results WHERE subsession_id=? ORDER BY finish_pos ASC
        ''', (subsession_id,)).fetchall()
    return [dict(r) for r in rows]


def get_driver_results(cust_id: int) -> list[dict]:
    """All race results for one driver across all sessions, newest first."""
    with get_db() as db:
        rows = db.execute('''
            SELECT rr.*, s.track_name, s.start_time, s.season_id
            FROM race_results rr
            JOIN sessions s ON s.subsession_id = rr.subsession_id
            WHERE rr.cust_id = ?
            ORDER BY s.start_time DESC
        ''', (cust_id,)).fetchall()
    return [dict(r) for r in rows]


# ── Meta ───────────────────────────────────────────────────────────────────────

def set_meta(key: str, value: str):
    with get_db() as db:
        db.execute('''
            INSERT INTO meta (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        ''', (key, value, _now()))


def get_meta(key: str) -> str | None:
    with get_db() as db:
        row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    return row['value'] if row else None
