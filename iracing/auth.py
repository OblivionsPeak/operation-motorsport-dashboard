"""
iRacing OAuth2 authentication using the password_limited grant.
Requires IRACING_CLIENT_ID and IRACING_CLIENT_SECRET environment variables
obtained by registering at https://oauth.iracing.com/accountmanagement
"""
import os
import time
import logging

from iracing.client import IRacingClient

log = logging.getLogger(__name__)


class IRacingAuth:
    # Tokens last 10 min; refresh_token lasts 7 days. Re-login after 7 days.
    _RELOGIN_TTL = 6 * 24 * 3600  # 6 days

    def __init__(self):
        self._client:    IRacingClient | None = None
        self._authed_at: float = 0.0
        self._ok = False

    @property
    def client(self) -> IRacingClient:
        return self._client

    def ensure(self):
        if not self._ok or (time.time() - self._authed_at) > self._RELOGIN_TTL:
            self._login()

    def _login(self):
        username      = os.environ['IRACING_EMAIL']
        password      = os.environ['IRACING_PASSWORD']
        client_id     = os.environ['IRACING_CLIENT_ID']
        client_secret = os.environ['IRACING_CLIENT_SECRET']

        log.info('Authenticating with iRacing OAuth2 (password_limited)...')
        client = IRacingClient()

        if not client.login(username, password, client_id, client_secret):
            raise RuntimeError(
                'iRacing OAuth2 login failed. '
                'Check IRACING_CLIENT_ID, IRACING_CLIENT_SECRET, and credentials.'
            )

        # Verify with a lightweight call
        try:
            info = client.member_info()
        except Exception as e:
            raise RuntimeError(f'iRacing auth succeeded but member_info failed: {e}') from e

        if not isinstance(info, dict) or not info.get('cust_id'):
            raise RuntimeError(f'iRacing member_info returned unexpected data: {info!r}')

        self._client    = client
        self._ok        = True
        self._authed_at = time.time()
        log.info('iRacing authentication successful (cust_id=%s)', info.get('cust_id'))

    def invalidate(self):
        self._ok     = False
        self._client = None


_auth = IRacingAuth()


def get_auth() -> IRacingAuth:
    return _auth
