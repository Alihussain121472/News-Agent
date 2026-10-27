import urllib.request

headers = {'User-Agent': 'Mozilla/5.0'}

def check(url, name, look_for=None, not_look_for=None):
    look_for = look_for or []
    not_look_for = not_look_for or []
    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=15)
        text = res.read().decode('utf-8', errors='ignore')
        print(f"[{res.status}] {name}: OK ({len(text)} bytes)")
        for lf in look_for:
            print(f"   + Has '{lf}': {lf in text}")
        for nlf in not_look_for:
            print(f"   - Omitted '{nlf}': {nlf not in text}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")

check('https://www.novabrief.tech/programs', 'Student Programs Directory',
      look_for=['Systems Limited', 'Arbisoft', '10Pearls', 'Devsinc'],
      not_look_for=["NASA L'SPACE"])
