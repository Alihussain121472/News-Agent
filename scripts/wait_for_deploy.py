import urllib.request
import json
import time
import sys

target_sha = 'be529df'
print(f"Monitoring deployment for sha={target_sha}...")

for attempt in range(40):
    try:
        req = urllib.request.Request(
            'https://api.github.com/repos/Alihussain121472/News-Agent/deployments',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        res = urllib.request.urlopen(req, timeout=10).read()
        deps = json.loads(res)
        found = False
        for d in deps[:3]:
            if d['sha'].startswith(target_sha):
                found = True
                dep_id = d['id']
                req_st = urllib.request.Request(
                    f'https://api.github.com/repos/Alihussain121472/News-Agent/deployments/{dep_id}/statuses',
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                st_data = json.loads(urllib.request.urlopen(req_st, timeout=10).read())
                state = st_data[0]['state'] if st_data else 'unknown'
                desc = st_data[0].get('description', '') if st_data else ''
                print(f"[{attempt+1}] Deployment {dep_id}: state={state} ({desc})")
                if state == 'success':
                    print("RENDER DEPLOYMENT SUCCEEDED!")
                    sys.exit(0)
                elif state in ('failure', 'error'):
                    print(f"RENDER DEPLOYMENT FAILED: {state}")
                    sys.exit(1)
        if not found:
            print(f"[{attempt+1}] Target deployment not found yet...")
    except Exception as e:
        print(f"[{attempt+1}] Polling error: {e}")
    time.sleep(15)

print("Timed out waiting for deployment")
sys.exit(2)
