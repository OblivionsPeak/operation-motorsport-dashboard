import traceback
from flask import Blueprint, jsonify, request
import db.queries as q
from config import LEAGUE_ID
from sync.scheduler import sync_standings

bp = Blueprint('standings', __name__)


@bp.get('/api/standings')
def get_standings():
    try:
        season_id = request.args.get('season_id', type=int)

        if not season_id:
            season = q.get_active_season(LEAGUE_ID)
            if not season:
                return jsonify({'error': 'No active season found — sync may still be running'}), 404
            season_id = season['season_id']

        rows = q.get_standings(season_id)

        if not rows:
            sync_standings(season_id)
            rows = q.get_standings(season_id)

        return jsonify({'season_id': season_id, 'standings': rows})

    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@bp.get('/api/seasons')
def get_seasons():
    seasons = q.get_seasons(LEAGUE_ID)
    return jsonify({'seasons': seasons})
