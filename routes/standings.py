from flask import Blueprint, jsonify, request
import db.queries as q
from config import LEAGUE_ID
from sync.scheduler import sync_standings

bp = Blueprint('standings', __name__)


@bp.get('/api/standings')
def get_standings():
    season_id = request.args.get('season_id', type=int)

    if not season_id:
        season = q.get_active_season(LEAGUE_ID)
        if not season:
            return jsonify({'error': 'No active season found'}), 404
        season_id = season['season_id']

    rows = q.get_standings(season_id)

    # If empty, trigger a live sync and wait
    if not rows:
        sync_standings(season_id)
        rows = q.get_standings(season_id)

    return jsonify({
        'season_id': season_id,
        'standings': rows,
    })


@bp.get('/api/seasons')
def get_seasons():
    seasons = q.get_seasons(LEAGUE_ID)
    return jsonify({'seasons': seasons})
