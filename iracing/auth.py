"""
iRacing Data API authentication via iracingdataapi library.
iracingdataapi handles the auth flow that CloudFront otherwise blocks.
"""
import os
import time
import logging
import warnings

from iracingdataapi.client import irDataClient

log = logging.getLogger(__name__)


class IRacingAuth:
    _AUTH_TTL = 23 * 3600

    def __init__(self):
        self._client: irDataClient | None = None
        self._authed_at: float = 0.0
        self._ok = False

    @property
    def client(self) -> irDataClient:
        return self._client

    def ensure(self):
        if not self._ok or (time.time() - self._authed_at) > self._AUTH_TTL:
            self._login()

    def _login(self):
        email    = os.environ['IRACING_EMAIL']
        password = os.environ['IRACING_PASSWORD']

        log.info('Authenticating with iRacing API...')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')   # suppress pydantic deprecation notice
            self._client = irDataClient(username=email, password=password)

        # Verify auth succeeded with a lightweight call
        info = None
        try:
            info = self._client.member_info()
        except Exception as e:
            raise RuntimeError(f'iRacing auth failed — member_info error: {e}') from e

        if not info or not isinstance(info, dict) or not info.get('cust_id'):
            raise RuntimeError(
                'iRacing auth failed — empty response. '
                'Possible causes: IP block (wait 15-30 min), wrong credentials, or 2FA required.'
            )

        self._ok        = True
        self._authed_at = time.time()
        log.info('iRacing authentication successful (cust_id=%s)', info.get('cust_id'))

    def invalidate(self):
        self._ok    = False
        self._client = None


_auth = IRacingAuth()


def get_auth() -> IRacingAuth:
    return _auth
