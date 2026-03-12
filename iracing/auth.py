"""
iRacing Data API authentication.
Maintains a single requests.Session with valid cookies.

iRacing requires:
  1. A GET to the members site first (sets initial cookies)
  2. A POST to /auth with browser-like headers and hashed password
  3. Cookies are then valid for ~24 hours
"""
import base64
import hashlib
import os
import time
import logging

import requests
from config import IRACING_BASE

log = logging.getLogger(__name__)

# iRacing expects requests that look like they come from a browser
_BROWSER_HEADERS = {
    'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept':       'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Referer':      'https://members.iracing.com/',
    'Origin':       'https://members.iracing.com',
}


def _hash_password(email: str, password: str) -> str:
    """iRacing expects base64(sha256(password + email.lower()))."""
    combined = (password + email.lower()).encode('utf-8')
    return base64.b64encode(hashlib.sha256(combined).digest()).decode('utf-8')


class IRacingAuth:
    """Wraps a requests.Session and keeps it authenticated."""

    _AUTH_TTL = 23 * 3600   # re-auth after 23 hours

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(_BROWSER_HEADERS)
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

        # Prime the session with initial cookies from the members site
        try:
            self._session.get('https://members.iracing.com/', timeout=15)
        except Exception:
            pass  # Non-fatal — proceed to auth attempt

        log.info('Authenticating with iRacing API...')
        resp = self._session.post(
            f'{IRACING_BASE}/auth',
            json={'email': email, 'password': pw_hash},
            timeout=30,
        )

        if resp.status_code == 401:
            raise RuntimeError(
                'iRacing login failed — check IRACING_EMAIL and IRACING_PASSWORD'
            )
        if resp.status_code == 429:
            raise RuntimeError(
                'iRacing rate-limited auth — too many login attempts, wait a few minutes'
            )
        resp.raise_for_status()

        # iRacing sometimes returns 200 with an authcode indicating success/failure
        try:
            body = resp.json()
            if body.get('authcode') == 0:
                raise RuntimeError(
                    f'iRacing rejected credentials: {body.get("message", "unknown error")}'
                )
        except (ValueError, AttributeError):
            pass  # Non-JSON response is fine if status was 200

        self._ok        = True
        self._authed_at = time.time()
        log.info('iRacing authentication successful')

    def invalidate(self):
        self._ok = False


# Module-level singleton — safe for single-worker/single-process deployment
_auth = IRacingAuth()


def get_auth() -> IRacingAuth:
    return _auth
