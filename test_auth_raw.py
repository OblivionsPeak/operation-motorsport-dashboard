"""
Raw iRacing auth diagnostic — bypasses iracingdataapi to see exact HTTP response.
Run: python test_auth_raw.py
"""
import os, hashlib, base64, json
import requests
from dotenv import load_dotenv
load_dotenv()

email    = os.environ.get('IRACING_EMAIL', '').strip()
password = os.environ.get('IRACING_PASSWORD', '').strip()

# iRacing password hashing: base64( sha256(password + email.lower()) )
pw_hash = base64.b64encode(
    hashlib.sha256((password + email.lower()).encode('utf-8')).digest()
).decode('utf-8')

print(f'Email:    {email}')
print(f'PW hash:  {pw_hash[:8]}... (first 8 chars shown)')
print()

session = requests.Session()
session.headers.update({
    'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept':          'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type':    'application/json',
    'Origin':          'https://www.iracing.com',
    'Referer':         'https://www.iracing.com/',
})

print('POSTing to https://members-ng.iracing.com/auth ...')
try:
    r = session.post(
        'https://members-ng.iracing.com/auth',
        json={'email': email, 'password': pw_hash},
        timeout=15,
    )
    print(f'Status:  {r.status_code}')
    print(f'Headers: {dict(r.headers)}')
    print(f'Body:    {repr(r.text[:500])}')
    print()

    if r.status_code == 200:
        try:
            data = r.json()
            print(f'JSON: {json.dumps(data, indent=2)[:500]}')
            if data.get('authcode') == 0:
                print('\nAUTH FAILED -- authcode=0 means wrong password or account issue.')
            elif data.get('authcode'):
                print(f'\nAUTH SUCCEEDED -- authcode={data["authcode"]}')
            else:
                print(f'\nUnexpected response shape: {data}')
        except Exception as e:
            print(f'Could not parse JSON: {e}')
    elif r.status_code == 401:
        print('401 -- Wrong credentials.')
    elif r.status_code == 405:
        print('405 -- CloudFront still blocking this IP.')
    else:
        print(f'Unexpected status {r.status_code}')

except Exception as e:
    print(f'Request failed: {e}')
