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
    req_news = urllib.request.Request('https://www.novabrief.tech/news', headers={'User-Agent': 'Mozilla/5.0'})
    resp_news = urllib.request.urlopen(req_news, timeout=15)
    news_html = resp_news.read().decode('utf-8')
    print('News Page Status:', resp_news.status)
    print('Has initialNewsFeed:', 'id="initialNewsFeed"' in news_html)
    print('Has toggleMoreNewsBtn:', 'id="toggleMoreNewsBtn"' in news_html)
    print('Has moreNewsFeed:', 'id="moreNewsFeed"' in news_html)
    print('Has See More News text:', 'See More News' in news_html)
    if 'id="initialNewsFeed"' in news_html and 'id="seeMoreNewsContainer"' in news_html:
        initial_part = news_html.split('id="initialNewsFeed"')[1].split('id="seeMoreNewsContainer"')[0]
        more_part = news_html.split('id="moreNewsFeed"')[1].split('</div>\n                </div>')[0] if 'id="moreNewsFeed"' in news_html else ''
        print('Initial news cards rendered:', initial_part.count('<article id="article-'))
        print('Dropdown news cards rendered:', more_part.count('<article id="article-'))
except Exception as e:
    print('Error checking live site:', e)
