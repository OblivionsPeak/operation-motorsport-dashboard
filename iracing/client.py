"""
Low-level iRacing API client.
Handles GET requests, auto-retry on 401, and S3 link-following.
"""
import logging
import requests
from config import IRACING_BASE
from iracing.auth import get_auth

log = logging.getLogger(__name__)


def _follow_s3(session: requests.Session, link: str) -> dict | list:
    """Fetch an S3 pre-signed URL and handle chunked responses."""
    resp = session.get(link, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Some endpoints wrap data in {"data": {...}} with chunk_info
    if isinstance(data, dict) and 'data' in data:
        inner = data['data']
        if isinstance(inner, dict) and 'chunk_info' in inner:
            chunk_info = inner['chunk_info']
            base_url   = chunk_info.get('base_download_url', '')
            chunks     = chunk_info.get('chunk_file_names', [])
            rows: list = []
            for fname in chunks:
                cr = session.get(base_url + fname, timeout=60)
                cr.raise_for_status()
                rows.extend(cr.json())
            inner['rows'] = rows
        return inner

    return data


def api_get(path: str, params: dict | None = None) -> dict | list:
    """
    GET {IRACING_BASE}{path}, following the S3 link pattern if present.
    Auto-retries once on 401.
    """
    auth = get_auth()
    auth.ensure()

    for attempt in range(2):
        resp = auth.session.get(
            f'{IRACING_BASE}{path}',
            params=params,
            timeout=30,
        )
        if resp.status_code == 401 and attempt == 0:
            log.warning('Got 401 — re-authenticating')
            auth.invalidate()
            auth.ensure()
            continue
        resp.raise_for_status()
        break

    data = resp.json()

    # Follow S3 link if the response just contains {"link": "..."}
    if isinstance(data, dict) and 'link' in data and len(data) <= 3:
        return _follow_s3(auth.session, data['link'])

    return data
