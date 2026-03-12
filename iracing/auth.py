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

_HEADERS = {
    'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept':       'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Referer':      'https://members.iracing.com/',
    'Origin':       'https://members.iracing.com',
}


def _hash_password(email: str, password: str) -> str:
    combined = (password + email.lower()).encode('utf-8')
    return base64.b64encode(hashlib.sha256(combined).digest()).decode('utf-8')


class IRacingAuth:
    _AUTH_TTL = 23 * 3600

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)
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

        # Prime session cookies
        try:
            self._session.get('https://members.iracing.com/', timeout=15)
        except Exception:
            pass

        log.info('Authenticating with iRacing API...')

        # Do NOT follow redirects automatically — requests converts POST→GET
        # on 301/302 which causes 405. We re-POST to any redirect location.
        resp = self._session.post(
            f'{IRACING_BASE}/auth',
            json={'email': email, 'password': pw_hash},
            timeout=30,
            allow_redirects=False,
        )

        log.info(f'Auth response: {resp.status_code}  headers: {dict(resp.headers)}')
        log.info(f'Auth body (first 500): {resp.text[:500]}')

        # Follow redirect manually with POST
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            log.info(f'Auth redirected → {location}, re-POSTing...')
            if location:
                resp = self._session.post(
                    location,
                    json={'email': email, 'password': pw_hash},
                    timeout=30,
                    allow_redirects=False,
                )
                log.info(f'Post-redirect response: {resp.status_code}')
                log.info(f'Post-redirect body: {resp.text[:500]}')

        if resp.status_code == 401:
            raise RuntimeError('iRacing login failed — check IRACING_EMAIL and IRACING_PASSWORD')
        if resp.status_code == 429:
            raise RuntimeError('iRacing rate-limited — wait a few minutes then retry')
        if resp.status_code == 405:
            raise RuntimeError(
                f'iRacing returned 405 for auth POST. '
                f'URL: {resp.url}  '
                f'Headers returned: {dict(resp.headers)}'
            )

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
