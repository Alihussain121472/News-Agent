import urllib.request
import json
import sys

try:
    req = urllib.request.Request(
        'https://api.github.com/repos/Alihussain121472/News-Agent/deployments',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    res = urllib.request.urlopen(req).read()
    deps = json.loads(res)
    print(f'Total deployments: {len(deps)}')
    for d in deps[:5]:
        dep_id = d['id']
        req_st = urllib.request.Request(
            f'https://api.github.com/repos/Alihussain121472/News-Agent/deployments/{dep_id}/statuses',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        st_data = json.loads(urllib.request.urlopen(req_st).read())
        state = st_data[0]['state'] if st_data else 'unknown'
        print(f"{dep_id} sha={d['sha'][:7]} env={d['environment']} state={state} created={d['created_at']}")
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
