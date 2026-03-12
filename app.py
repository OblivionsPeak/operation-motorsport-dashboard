"""
Operation Motorsport — iRacing League Dashboard
Flask app entry point.
"""
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, send_from_directory
from db.database import init_db
from routes.standings import bp as standings_bp
from routes.results   import bp as results_bp
from routes.drivers   import bp as drivers_bp
from routes.admin     import bp as admin_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')

# Register API blueprints
app.register_blueprint(standings_bp)
app.register_blueprint(results_bp)
app.register_blueprint(drivers_bp)
app.register_blueprint(admin_bp)


# ── Static page routes ────────────────────────────────────────────────────────

@app.get('/')
def index():
    return send_from_directory('static', 'index.html')

@app.get('/results')
def results_page():
    return send_from_directory('static', 'results.html')

@app.get('/race/<int:subsession_id>')
def race_page(subsession_id: int):
    return send_from_directory('static', 'race.html')

@app.get('/driver/<int:cust_id>')
def driver_page(cust_id: int):
    return send_from_directory('static', 'driver.html')


# ── Startup ───────────────────────────────────────────────────────────────────

def create_app():
    init_db()
    log.info('Database initialised')

    # Only start scheduler when running as a real server (not during imports)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        from sync.scheduler import start_scheduler
        start_scheduler()

    return app


if __name__ == '__main__':
    create_app()
    port = int(os.environ.get('PORT', 5055))
    app.run(host='0.0.0.0', port=port, debug=False)
