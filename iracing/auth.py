"""
iRacing Data API authentication.
Maintains a single requests.Session with valid cookies.

NOTE: Do NOT add browser-like headers (Origin, Referer, fake User-Agent).
iRacing's CloudFront WAF blocks requests that impersonate browsers.
The default python-requests User-Agent works fine.
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
    _AUTH_TTL = 23 * 3600

    def __init__(self):
        self._session = requests.Session()
        # Do NOT set custom headers — CloudFront blocks browser-impersonation
        self._authed_at: float = 0.0
        self._ok = False

    @property
    def session(self) -> requests.Session:
        return self._session

    def ensure(self):
        if not self._ok or (time.time() - self._authed_at) > self._AUTH_TTL:
            self._login()

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

        log.info(f'Auth status: {resp.status_code}')

        if resp.status_code == 401:
            raise RuntimeError('iRacing login failed — check IRACING_EMAIL and IRACING_PASSWORD')
        if resp.status_code == 429:
            raise RuntimeError('iRacing rate-limited — wait a few minutes then retry')
        resp.raise_for_status()

        try:
            body = resp.json()
            if body.get('authcode') == 0:
                raise RuntimeError(
                    f'iRacing rejected credentials: {body.get("message", "unknown")}'
                )
        except (ValueError, AttributeError):
            pass

        self._ok        = True
        self._authed_at = time.time()
        log.info('iRacing authentication successful')

    def invalidate(self):
        self._ok = False


_auth = IRacingAuth()


def get_auth() -> IRacingAuth:
    return _auth
