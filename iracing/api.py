"""
iRacing Data API — one function per endpoint.
No points data is fetched or returned (league uses custom scoring).
"""
import logging
from iracing.client import api_get

log = logging.getLogger(__name__)


def get_league(league_id: int) -> dict:
    """Fetch league metadata including season list."""
    return api_get('/data/league/get', {'league_id': league_id, 'include_licenses': False})


def get_season_sessions(league_id: int, season_id: int) -> list[dict]:
    """Return list of sessions for a season (completed races only)."""
    data = api_get('/data/league/season_sessions', {
        'league_id':    league_id,
        'season_id':    season_id,
        'results_only': True,
    })
    # Response may be nested under 'sessions' key
    if isinstance(data, dict):
        return data.get('sessions', [])
    if isinstance(data, list):
        return data
    return []


def get_season_standings(league_id: int, season_id: int) -> list[dict]:
    """
    Return driver standing rows for a season.
    Points fields are intentionally dropped — league uses custom scoring.
    """
    data = api_get('/data/league/season_standings', {
        'league_id': league_id,
        'season_id': season_id,
    })

    rows: list[dict] = []
    if isinstance(data, dict):
        rows = (
            data.get('standings', []) or
            data.get('driver_standings', []) or
            data.get('rows', [])
        )
    elif isinstance(data, list):
        rows = data

    # Strip points fields — not used
    clean = []
    for r in rows:
        clean.append({
            'cust_id':           r.get('cust_id'),
            'display_name':      r.get('display_name', 'Unknown'),
            'car_number':        r.get('car_number', ''),
            'position':          r.get('position', 0),
            'starts':            r.get('starts', 0),
            'wins':              r.get('wins', 0),
            'top5':              r.get('top5', 0),
            'laps':              r.get('laps', 0),
            'laps_led':          r.get('laps_led', 0),
            'incidents':         r.get('incidents', 0),
            'avg_finish':        round(r.get('avg_finish_position', 0) + 1, 2),  # 0-indexed → 1-indexed
            'avg_start':         round(r.get('avg_start_position', 0) + 1, 2),
            'division':          r.get('division', 0),
        })
    return clean


def get_race_result(subsession_id: int) -> dict:
    """
    Fetch full result for a completed race subsession.
    Returns a cleaned dict with track, date, and driver results.
    """
    data = api_get('/data/results/get', {'subsession_id': subsession_id})
    if not isinstance(data, dict):
        return {}

    track_name = (data.get('track') or {}).get('track_name', 'Unknown Track')
    start_time = data.get('start_time', '')

    # Find the Race simsession (type 6)
    race_results: list[dict] = []
    for ss in data.get('session_results', []):
        if ss.get('simsession_type') == 6 or ss.get('simsession_name', '').upper() == 'RACE':
            race_results = ss.get('results', [])
            break

    drivers = []
    for r in race_results:
        best_ms  = r.get('best_lap_time', -1)
        best_str = _fmt_laptime(best_ms) if best_ms > 0 else '—'
        drivers.append({
            'cust_id':      r.get('cust_id'),
            'display_name': r.get('display_name', 'Unknown'),
            'car_number':   r.get('livery', {}).get('car_number', r.get('car_number', '')),
            'finish_pos':   r.get('finish_position', 0) + 1,   # 0-indexed → 1-indexed
            'start_pos':    r.get('starting_position', 0) + 1,
            'laps':         r.get('laps_complete', 0),
            'laps_led':     r.get('laps_led', 0),
            'incidents':    r.get('incidents', 0),
            'best_lap':     best_str,
            'reason_out':   r.get('reason_out', 'Running'),
        })

    return {
        'subsession_id': subsession_id,
        'track_name':    track_name,
        'start_time':    start_time,
        'drivers':       drivers,
    }


def get_member(cust_id: int) -> dict:
    """Fetch basic member info."""
    data = api_get('/data/member/get', {'cust_ids': cust_id, 'include_licenses': False})
    members = data.get('members', []) if isinstance(data, dict) else []
    if not members:
        return {}
    m = members[0]
    return {
        'cust_id':     m.get('cust_id'),
        'display_name': m.get('display_name', 'Unknown'),
        'club_name':   m.get('club_name', ''),
        'irating':     m.get('irating', 0),
    }


# ── helpers ────────────────────────────────────────────────────────────────────

def _fmt_laptime(ms_tenths: int) -> str:
    """Convert iRacing lap time (tenths of ms) to M:SS.mmm string."""
    total_ms = ms_tenths / 10
    minutes  = int(total_ms // 60000)
    seconds  = (total_ms % 60000) / 1000
    return f'{minutes}:{seconds:06.3f}'
