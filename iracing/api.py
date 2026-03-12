"""
iRacing Data API calls via iracingdataapi library.
No points data is used — league uses custom scoring.
"""
import logging
import warnings
from iracing.auth import get_auth

log = logging.getLogger(__name__)


def _client():
    auth = get_auth()
    auth.ensure()
    return auth.client


def _safe_call(fn, *args, **kwargs):
    """Call an iracingdataapi method, suppressing pydantic deprecation warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return fn(*args, **kwargs)


def get_league(league_id: int) -> dict:
    result = _safe_call(_client().league, league_id)
    return result if isinstance(result, dict) else {}


def get_season_sessions(league_id: int, season_id: int) -> list[dict]:
    result = _safe_call(
        _client().league_season_sessions,
        league_id=league_id,
        season_id=season_id,
        results_only=True,
    )
    if isinstance(result, dict):
        return result.get('sessions', [])
    if isinstance(result, list):
        return result
    return []


def get_season_standings(league_id: int, season_id: int) -> list[dict]:
    result = _safe_call(
        _client().league_season_standings,
        league_id=league_id,
        season_id=season_id,
    )

    rows: list = []
    if isinstance(result, dict):
        rows = (
            result.get('standings', []) or
            result.get('driver_standings', []) or
            result.get('rows', [])
        )
    elif isinstance(result, list):
        rows = result

    clean = []
    for r in rows:
        if not isinstance(r, dict):
            r = dict(r)
        clean.append({
            'cust_id':      r.get('cust_id'),
            'display_name': r.get('display_name', 'Unknown'),
            'car_number':   r.get('car_number', ''),
            'position':     r.get('position', 0),
            'starts':       r.get('starts', 0),
            'wins':         r.get('wins', 0),
            'top5':         r.get('top5', 0),
            'laps':         r.get('laps', 0),
            'laps_led':     r.get('laps_led', 0),
            'incidents':    r.get('incidents', 0),
            'avg_finish':   round((r.get('avg_finish_position') or 0) + 1, 2),
            'avg_start':    round((r.get('avg_start_position') or 0) + 1, 2),
            'division':     r.get('division', 0),
        })
    return clean


def get_race_result(subsession_id: int) -> dict:
    result = _safe_call(_client().result, subsession_id=subsession_id)
    if not isinstance(result, dict):
        try:
            result = dict(result)
        except Exception:
            return {}

    track_name = (result.get('track') or {}).get('track_name', 'Unknown Track')
    start_time = result.get('start_time', '')

    race_results: list = []
    for ss in result.get('session_results', []):
        if not isinstance(ss, dict):
            ss = dict(ss)
        stype = ss.get('simsession_type')
        sname = ss.get('simsession_name', '').upper()
        if stype == 6 or sname == 'RACE':
            race_results = ss.get('results', [])
            break

    drivers = []
    for r in race_results:
        if not isinstance(r, dict):
            r = dict(r)
        best_ms  = r.get('best_lap_time', -1)
        best_str = _fmt_laptime(best_ms) if best_ms and best_ms > 0 else '—'
        livery   = r.get('livery') or {}
        if not isinstance(livery, dict):
            livery = dict(livery)
        drivers.append({
            'cust_id':      r.get('cust_id'),
            'display_name': r.get('display_name', 'Unknown'),
            'car_number':   livery.get('car_number', r.get('car_number', '')),
            'finish_pos':   (r.get('finish_position') or 0) + 1,
            'start_pos':    (r.get('starting_position') or 0) + 1,
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


def _fmt_laptime(ms_tenths: int) -> str:
    total_ms = ms_tenths / 10
    minutes  = int(total_ms // 60000)
    seconds  = (total_ms % 60000) / 1000
    return f'{minutes}:{seconds:06.3f}'
