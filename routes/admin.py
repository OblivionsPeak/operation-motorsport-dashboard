from flask import Blueprint, jsonify, request
from config import ADMIN_PASSWORD
from sync.scheduler import trigger_sync
import db.queries as q

bp = Blueprint('admin', __name__)


def _check_auth():
    return request.headers.get('X-Admin-Password') == ADMIN_PASSWORD


@bp.post('/api/admin/sync')
def force_sync():
    if not _check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    trigger_sync()
    return jsonify({'status': 'sync triggered'})


@bp.get('/api/admin/status')
def sync_status():
    if not _check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'last_season_sync':   q.get_meta('last_season_sync'),
        'last_standings_sync': q.get_meta('last_standings_sync'),
        'last_session_sync':  q.get_meta('last_session_sync'),
    })
