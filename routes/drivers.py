from flask import Blueprint, jsonify
import db.queries as q

bp = Blueprint('drivers', __name__)


@bp.get('/api/drivers/<int:cust_id>')
def get_driver(cust_id: int):
    driver  = q.get_driver(cust_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    results = q.get_driver_results(cust_id)

    # Compute career stats from cached results
    starts    = len(results)
    wins      = sum(1 for r in results if r['finish_pos'] == 1)
    top5      = sum(1 for r in results if r['finish_pos'] <= 5)
    incidents = sum(r['incidents'] for r in results)
    avg_finish = round(
        sum(r['finish_pos'] for r in results) / starts, 2
    ) if starts else 0

    return jsonify({
        'driver':  driver,
        'stats': {
            'starts':    starts,
            'wins':      wins,
            'top5':      top5,
            'incidents': incidents,
            'avg_finish': avg_finish,
        },
        'results': results,
    })
