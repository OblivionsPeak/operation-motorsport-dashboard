"""
Quick auth test using the iracingdataapi community library.
Run: python test_auth.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from iracingdataapi.client import irDataClient
except ImportError:
    print("Installing iracingdataapi...")
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'iracingdataapi'])
    from iracingdataapi.client import irDataClient

email    = os.environ.get('IRACING_EMAIL', '')
password = os.environ.get('IRACING_PASSWORD', '')

print(f'Testing auth for: {email}')
print('Connecting to iRacing API...')

try:
    client = irDataClient(username=email, password=password)
    print(f'authenticated after init: {getattr(client, "authenticated", "N/A")}')

    # member_info is a lightweight call that requires auth
    info = client.member_info()
    print(f'member_info result type: {type(info)}')
    print(f'member_info result: {info}')

    if info and isinstance(info, dict) and info.get('cust_id'):
        print(f'\nAUTH SUCCEEDED — logged in as cust_id={info["cust_id"]}')
    elif info:
        print(f'\nAUTH POSSIBLY OK — got data but unexpected shape')
    else:
        print(f'\nAUTH FAILED — empty response (IP block likely, wait 15-30 min)')

except Exception as e:
    msg = str(e)
    print(f'\nException: {e}')
    if '405' in msg:
        print('→ 405 Method Not Allowed — CloudFront IP block. Wait 15-30 min or use phone hotspot.')
    elif '401' in msg or 'authcode' in msg.lower() or 'unauthorized' in msg.lower():
        print('→ 401 Unauthorized — wrong credentials.')
    elif 'Expecting value' in msg or 'JSONDecodeError' in msg:
        print('>> Empty/invalid JSON response -- almost certainly an IP block.')
        print('   Wait 15-30 minutes then retry, or connect via phone hotspot.')
    else:
        print(f'→ Unexpected error.')
