import urllib.request
import json

headers = {'User-Agent': 'Mozilla/5.0'}

print("=== CHECKING LIVE PRODUCTION DEPLOYMENT FOR SKILL CHECK REFRESH ===")

try:
    req = urllib.request.Request('https://www.novabrief.tech/learn-python', headers=headers)
    res = urllib.request.urlopen(req, timeout=15)
    html = res.read().decode('utf-8')
    print(f"[{res.status}] /learn-python: OK ({len(html)} bytes)")
    print("   + Has 'Reset & New Questions':", ('Reset &amp; New Questions' in html or 'Reset & New Questions' in html))
    print("   + Has 'Review & Concept Breakdown':", ('Review &amp; Concept Breakdown' in html or 'Review & Concept Breakdown' in html))
    print("   + Has 'refreshSkillCheck':", ('refreshSkillCheck' in html))

    req_api = urllib.request.Request('https://www.novabrief.tech/api/python/skill-check', headers=headers)
    res_api = urllib.request.urlopen(req_api, timeout=15)
    api_data = json.loads(res_api.read().decode('utf-8'))
    print(f"[{res_api.status}] /api/python/skill-check: OK")
    print("   + Status:", api_data.get('status'))
    print("   + Questions count:", len(api_data.get('questions', [])))
    for q in api_data.get('questions', [])[:2]:
        lines = [line for line in q.get('explanation', '').split('\n') if line]
        print(f"      - {q.get('module_title')}: {len(lines)} explanation lines")

except Exception as e:
    print("Error checking live site:", e)
