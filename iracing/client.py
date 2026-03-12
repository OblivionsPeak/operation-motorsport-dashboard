"""
iRacing Data API client using OAuth2 "password_limited" grant.
Requires a registered OAuth client from https://oauth.iracing.com/accountmanagement
"""
import hashlib
import base64
import time
import logging

from curl_cffi import requests as curl_requests

log = logging.getLogger(__name__)

OAUTH_TOKEN_URL = 'https://oauth.iracing.com/oauth2/token'
DATA_BASE       = 'https://members-ng.iracing.com'


def _mask(value: str, identifier: str) -> str:
    """iRacing masking: base64(sha256(value + identifier.lower()))"""
    return base64.b64encode(
        hashlib.sha256((value + identifier.lower()).encode('utf-8')).digest()
    ).decode('utf-8')


class IRacingClient:
    """iRacing Data API client using OAuth2 password_limited grant."""

    def __init__(self):
        self._session       = curl_requests.Session(impersonate='chrome124')
        self._access_token  = None
        self._refresh_token = None
        self._expires_at    = 0.0
        self.authenticated  = False

    def login(self, username: str, password: str, client_id: str, client_secret: str) -> bool:
        """Obtain tokens using the password_limited grant."""
        data = {
            'grant_type':    'password_limited',
            'client_id':     client_id,
            'client_secret': _mask(client_secret, client_id),
            'username':      username,
            'password':      _mask(password, username),
            'scope':         'iracing.auth',
        }
        r = self._session.post(OAUTH_TOKEN_URL, data=data)
        r.raise_for_status()
        tokens = r.json()

        if 'access_token' not in tokens:
            log.error('OAuth token response missing access_token: %s', tokens)
            return False

        self._access_token  = tokens['access_token']
        self._refresh_token = tokens.get('refresh_token')
        self._expires_at    = time.time() + tokens.get('expires_in', 600) - 30
        self.authenticated  = True
        log.info('iRacing OAuth login succeeded, token expires in %ss', tokens.get('expires_in'))
        return True

    def refresh(self) -> bool:
        """Use refresh_token to get a new access_token."""
        if not self._refresh_token:
            return False
        data = {
            'grant_type':    'refresh_token',
            'refresh_token': self._refresh_token,
        }
        r = self._session.post(OAUTH_TOKEN_URL, data=data)
        if r.status_code != 200:
            log.warning('Token refresh failed (%s), will re-login', r.status_code)
            self.authenticated = False
            return False
        tokens = r.json()
        self._access_token  = tokens['access_token']
        self._refresh_token = tokens.get('refresh_token', self._refresh_token)
        self._expires_at    = time.time() + tokens.get('expires_in', 600) - 30
        log.info('iRacing token refreshed')
        return True

    def _ensure_token(self):
        if time.time() >= self._expires_at:
            self.refresh()

    def _get(self, path: str, **params) -> dict | list:
        self._ensure_token()
        headers = {'Authorization': f'Bearer {self._access_token}'}
        r = self._session.get(f'{DATA_BASE}{path}', params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        # iRacing returns S3 pre-signed links for large payloads
        if isinstance(data, dict) and 'link' in data:
            r2 = self._session.get(data['link'])
            r2.raise_for_status()
            return r2.json()
        return data

    # ── API methods ───────────────────────────────────────────────────────────

    def member_info(self) -> dict:
        return self._get('/data/member/info')

    def league_get(self, league_id: int) -> dict:
        return self._get('/data/league/get', league_id=league_id)

    def league_seasons(self, league_id: int, include_series: bool = False) -> dict:
        return self._get(
            '/data/league/seasons',
            league_id=league_id,
            include_series=int(include_series),
        )

    def league_season_standings(self, league_id: int, season_id: int) -> dict:
        return self._get(
            '/data/league/season_standings',
            league_id=league_id,
            season_id=season_id,
        )

    def league_season_sessions(
        self,
        league_id: int,
        season_id: int,
        results_only: bool = False,
    ) -> dict:
        return self._get(
            '/data/league/season_sessions',
            league_id=league_id,
            season_id=season_id,
            results_only=int(results_only),
        )

    def result(self, subsession_id: int) -> dict:
        return self._get('/data/results/get', subsession_id=subsession_id)
