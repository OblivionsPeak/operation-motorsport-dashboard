from flask import Blueprint, jsonify, request
import db.queries as q
from db.database import get_db
from config import LEAGUE_ID
from sync.scheduler import sync_sessions, _sync_race_result

bp = Blueprint('results', __name__)


@bp.get('/api/results')
def get_results():
    """List of completed races for a season."""
    season_id = request.args.get('season_id', type=int)

    if not season_id:
        season = q.get_active_season(LEAGUE_ID)
        if not season:
            return jsonify({'error': 'No active season found'}), 404
        season_id = season['season_id']

    sessions = q.get_sessions(season_id)

    # Only return sessions with results
    completed = [s for s in sessions if s.get('has_results')]

    if not completed:
        sync_sessions(season_id)
        sessions  = q.get_sessions(season_id)
        completed = [s for s in sessions if s.get('has_results')]

    return jsonify({'season_id': season_id, 'results': completed})


@bp.get('/api/results/<int:subsession_id>')
def get_race(subsession_id: int):
    """Full result for one race."""
    rows = q.get_race_results(subsession_id)

    if not rows:
        # Try to find which season this session belongs to
        sessions = []
        for season in q.get_seasons(LEAGUE_ID):
            all_sess = q.get_sessions(season['season_id'])
            sessions += all_sess

        season_id = next(
            (s['season_id'] for s in sessions if s['subsession_id'] == subsession_id),
            None
        )
        if season_id is None:
            return jsonify({'error': 'Session not found'}), 404

        _sync_race_result(subsession_id, season_id)
        rows = q.get_race_results(subsession_id)

    # Get session metadata
    with get_db() as db:
        sess = db.execute(
            'SELECT * FROM sessions WHERE subsession_id=?', (subsession_id,)
        ).fetchone()
    sess_data = dict(sess) if sess else {}

    return jsonify({
        'subsession_id': subsession_id,
        'track_name':    sess_data.get('track_name', ''),
        'start_time':    sess_data.get('start_time', ''),
        'results':       rows,
    })
