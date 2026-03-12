"""
iRacing OAuth2 auth test (password_limited grant).
Run: python test_auth_raw.py

Requires IRACING_CLIENT_ID and IRACING_CLIENT_SECRET in .env
Register at: https://oauth.iracing.com/accountmanagement
"""
import os, json
from dotenv import load_dotenv
from iracing.client import IRacingClient

load_dotenv()

username      = os.environ.get('IRACING_EMAIL', '').strip()
password      = os.environ.get('IRACING_PASSWORD', '').strip()
client_id     = os.environ.get('IRACING_CLIENT_ID', '').strip()
client_secret = os.environ.get('IRACING_CLIENT_SECRET', '').strip()

if not client_id or client_id == 'your_client_id_here':
    print('ERROR: IRACING_CLIENT_ID not set in .env')
    print('Register at: https://oauth.iracing.com/accountmanagement')
    exit(1)

print(f'Email:     {username}')
print(f'Client ID: {client_id}')
print()

client = IRacingClient()
print('Attempting OAuth2 login (password_limited)...')
ok = client.login(username, password, client_id, client_secret)

if ok:
    print('LOGIN SUCCEEDED')
    print('Fetching member_info...')
    try:
        info = client.member_info()
        print(f'cust_id:      {info.get("cust_id")}')
        print(f'display_name: {info.get("display_name")}')
        print()
        print('Auth is working! The dashboard will sync data automatically.')
    except Exception as e:
        print(f'member_info failed: {e}')
else:
    print('LOGIN FAILED — check client credentials')
