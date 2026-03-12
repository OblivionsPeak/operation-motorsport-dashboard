"""
Background sync engine.
Fetches data from iRacing API and writes to SQLite cache.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

import db.queries as q
from config import LEAGUE_ID, SYNC_INTERVAL_MIN
from iracing import api

log = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


# ── Sync functions ────────────────────────────────────────────────────────────

def sync_seasons():
    """Fetch league metadata and upsert season list."""
    log.info('Syncing league seasons...')
    try:
        league = api.get_league(LEAGUE_ID)
        seasons = league.get('seasons', [])
        for s in seasons:
            sid  = s.get('season_id')
            name = s.get('season_name', f'Season {sid}')
            # Mark the highest season_id as active
            active = (sid == max(x.get('season_id', 0) for x in seasons))
            q.upsert_season(sid, LEAGUE_ID, name, active)
        log.info(f'Synced {len(seasons)} seasons')
        q.set_meta('last_season_sync', datetime.now(timezone.utc).isoformat())
    except Exception as e:
        log.error(f'Season sync failed: {e}')


def sync_standings(season_id: int):
    """Fetch and cache standings for a season."""
    log.info(f'Syncing standings for season {season_id}...')
    try:
        rows = api.get_season_standings(LEAGUE_ID, season_id)
        for row in rows:
            cust_id = row.get('cust_id')
            if cust_id:
                q.upsert_driver(cust_id, row.get('display_name', 'Unknown'))
                q.upsert_standing(season_id, row)
        log.info(f'Synced {len(rows)} standing rows')
        q.set_meta('last_standings_sync', datetime.now(timezone.utc).isoformat())
    except Exception as e:
        log.error(f'Standings sync failed: {e}')


def sync_sessions(season_id: int):
    """Fetch session list and pull results for any new completed races."""
    log.info(f'Syncing sessions for season {season_id}...')
    try:
        sessions = api.get_season_sessions(LEAGUE_ID, season_id)
        for s in sessions:
            sub_id = s.get('subsession_id')
            if not sub_id:
                continue

            track = (s.get('track') or {}).get('track_name', 'Unknown Track')
            q.upsert_session({
                'subsession_id': sub_id,
                'season_id':     season_id,
                'track_name':    track,
                'session_name':  s.get('session_name', ''),
                'start_time':    s.get('launch_at', ''),
                'has_results':   bool(s.get('has_results')),
            })

            # Only fetch race results once (historical results never change)
            if s.get('has_results') and not _race_fully_cached(sub_id):
                _sync_race_result(sub_id, season_id)

        log.info(f'Synced {len(sessions)} sessions')
        q.set_meta('last_session_sync', datetime.now(timezone.utc).isoformat())
    except Exception as e:
        log.error(f'Session sync failed: {e}')


def _sync_race_result(subsession_id: int, season_id: int):
    """Fetch and store one race result."""
    try:
        result = api.get_race_result(subsession_id)
        if not result or not result.get('drivers'):
            return
        for driver in result['drivers']:
            cust_id = driver.get('cust_id')
            if cust_id:
                q.upsert_driver(cust_id, driver.get('display_name', 'Unknown'))
                q.upsert_race_result(subsession_id, driver)
        # Mark session as having results
        q.upsert_session({
            'subsession_id': subsession_id,
            'season_id':     season_id,
            'track_name':    result.get('track_name', ''),
            'session_name':  '',
            'start_time':    result.get('start_time', ''),
            'has_results':   True,
        })
        log.info(f'Cached result for subsession {subsession_id} ({len(result["drivers"])} drivers)')
    except Exception as e:
        log.error(f'Race result sync failed for {subsession_id}: {e}')


def _race_fully_cached(subsession_id: int) -> bool:
    """True if we already have race results for this subsession."""
    results = q.get_race_results(subsession_id)
    return len(results) > 0


def sync_all():
    """Full sync: seasons → standings → sessions → results."""
    log.info('=== Starting full sync ===')
    sync_seasons()

    season = q.get_active_season(LEAGUE_ID)
    if not season:
        log.warning('No active season found — skipping standings/sessions sync')
        return

    sid = season['season_id']
    sync_standings(sid)
    sync_sessions(sid)
    log.info('=== Sync complete ===')


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def start_scheduler():
    """Start APScheduler background job. Safe to call once."""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        sync_all,
        trigger='interval',
        minutes=SYNC_INTERVAL_MIN,
        id='sync_all',
        replace_existing=True,
    )
    _scheduler.start()
    log.info(f'Scheduler started — syncing every {SYNC_INTERVAL_MIN} minutes')

    # Run once at startup (after a short delay to let Flask start)
    import threading
    def _initial():
        import time; time.sleep(5)
        sync_all()
    threading.Thread(target=_initial, daemon=True).start()


def trigger_sync():
    """Manually trigger a full sync (called from admin route)."""
    import threading
    threading.Thread(target=sync_all, daemon=True).start()
