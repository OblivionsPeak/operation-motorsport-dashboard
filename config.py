import os

IRACING_BASE      = 'https://members-ng.iracing.com'
LEAGUE_ID         = int(os.getenv('LEAGUE_ID', '5403'))
ADMIN_PASSWORD    = os.getenv('ADMIN_PASSWORD', 'changeme')
SYNC_INTERVAL_MIN = int(os.getenv('SYNC_INTERVAL_MINUTES', '15'))

# DB stored in ./data/ locally; override via DB_PATH env var for cloud
_here   = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv('DB_PATH', os.path.join(_here, 'data', 'dashboard.db'))
