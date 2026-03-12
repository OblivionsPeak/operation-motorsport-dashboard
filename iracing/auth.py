"""
iRacing Data API authentication.
Maintains a single requests.Session with valid cookies.
"""
import base64
import hashlib
import os
import time
import logging

import requests
from config import IRACING_BASE

log = logging.getLogger(__name__)


def _hash_password(email: str, password: str) -> str:
    """iRacing expects base64(sha256(password + email.lower()))."""
    combined = (password + email.lower()).encode('utf-8')
    return base64.b64encode(hashlib.sha256(combined).digest()).decode('utf-8')


class IRacingAuth:
    """Wraps a requests.Session and keeps it authenticated."""

    # Re-authenticate after 23 hours to stay ahead of the 24-hour expiry
    _AUTH_TTL = 23 * 3600

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': 'OM-Dashboard/1.0'})
        self._authed_at: float = 0.0
        self._ok = False

    # ── public ────────────────────────────────────────────────────────────────

    @property
    def session(self) -> requests.Session:
        return self._session

    def ensure(self):
        """Call before every API request."""
        if not self._ok or (time.time() - self._authed_at) > self._AUTH_TTL:
            self._login()

    # ── private ───────────────────────────────────────────────────────────────

    def _login(self):
        email    = os.environ['IRACING_EMAIL']
        password = os.environ['IRACING_PASSWORD']
        pw_hash  = _hash_password(email, password)

        log.info('Authenticating with iRacing API...')
        resp = self._session.post(
            f'{IRACING_BASE}/auth',
            json={'email': email, 'password': pw_hash},
            timeout=30,
        )
        if resp.status_code == 401:
            raise RuntimeError('iRacing login failed — check IRACING_EMAIL and IRACING_PASSWORD')
        resp.raise_for_status()

        self._ok        = True
        self._authed_at = time.time()
        log.info('iRacing authentication successful')

    def invalidate(self):
        self._ok = False


# Module-level singleton — safe for single-worker/single-process deployment
_auth = IRacingAuth()


def get_auth() -> IRacingAuth:
    return _auth
