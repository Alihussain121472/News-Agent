import urllib.request

try:
    req = urllib.request.Request('https://www.novabrief.tech/', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8')
    print('Homepage Status:', resp.status)
    print('Has python-feature-banner:', 'python-feature-banner' in html)
    print('Has CS50P Course Banner:', 'CS50P Aligned Interactive Engineering Course' in html)
    print('Has data-theme-surface adaptive:', 'data-theme-surface="adaptive"' in html)

    req_css = urllib.request.Request('https://www.novabrief.tech/static/css/website-theme.min.css', headers={'User-Agent': 'Mozilla/5.0'})
    resp_css = urllib.request.urlopen(req_css, timeout=15)
    css_text = resp_css.read().decode('utf-8')
    print('CSS Status:', resp_css.status)
    print('Has .python-feature-banner in live CSS:', '.python-feature-banner' in css_text)
    print('Has .text-white guarantee in live CSS:', '.text-white' in css_text)
except Exception as e:
    print('Error checking live site:', e)
