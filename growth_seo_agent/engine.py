import ipaddress
import json
import re
import socket
import time
from html import unescape
from urllib.parse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup


USER_AGENT = 'NovaBriefSEOStudio/2.0 (+https://www.novabrief.tech)'
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def normalize_site_url(value):
    value = (value or '').strip()
    if not value:
        raise ValueError('Website URL is required.')
    if '://' not in value:
        value = f'https://{value}'
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Enter a valid public HTTP or HTTPS website URL.')
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError('Enter a valid website port.') from exc
    clean_path = parsed.path.rstrip('/') or ''
    return urlunparse((parsed.scheme, parsed.netloc.lower(), clean_path, '', '', ''))


def validate_public_url(value):
    normalized = normalize_site_url(value)
    parsed = urlparse(normalized)
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))}
    except socket.gaierror as exc:
        raise ValueError('The website hostname could not be resolved.') from exc
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError('Private or local network addresses are not allowed.')
    return normalized


def fetch_document(url, timeout=12):
    current = validate_public_url(url)
    headers = {'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.5'}
    started = time.monotonic()

    for _ in range(5):
        response = requests.get(current, headers=headers, timeout=timeout, allow_redirects=False, stream=True)
        if response.is_redirect:
            location = response.headers.get('Location')
            response.close()
            if not location:
                raise ValueError('A redirect did not provide a destination.')
            current = validate_public_url(urljoin(current, location))
            continue

        body = bytearray()
        for chunk in response.iter_content(64 * 1024):
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                response.close()
                raise ValueError('The response exceeded the safe audit size limit.')
        elapsed_ms = int((time.monotonic() - started) * 1000)
        encoding = response.encoding or 'utf-8'
        text = bytes(body).decode(encoding, errors='replace')
        return {
            'url': current,
            'status': response.status_code,
            'headers': dict(response.headers),
            'text': text,
            'elapsed_ms': elapsed_ms,
            'content_type': (response.headers.get('Content-Type') or '').lower(),
        }

    raise ValueError('The website redirected too many times.')


def _issue(key, category, severity, url, title, detail, recommendation):
    return {
        'key': key,
        'category': category,
        'severity': severity,
        'url': url,
        'title': title,
        'detail': detail,
        'recommendation': recommendation,
    }


def _same_site(candidate, site_host):
    try:
        host = (urlparse(candidate).hostname or '').lower()
        return host == site_host or host.endswith(f'.{site_host}') or site_host.endswith(f'.{host}')
    except ValueError:
        return False


def _parse_sitemap(xml_text, site_host, limit):
    urls = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return urls
    for element in root.iter():
        if element.tag.endswith('loc') and element.text:
            candidate = element.text.strip()
            if candidate.startswith(('http://', 'https://')) and _same_site(candidate, site_host) and candidate not in urls:
                urls.append(candidate)
                if len(urls) >= limit:
                    break
    return urls


def analyze_page(document, homepage=False):
    url = document['url']
    status = int(document['status'])
    issues = []
    summary = {'url': url, 'status': status, 'elapsed_ms': document.get('elapsed_ms', 0)}

    if status >= 400:
        issues.append(_issue('http_error', 'indexability', 'critical', url, f'Page returns HTTP {status}', 'Search engines and visitors cannot access this page successfully.', 'Restore the page or redirect it to the closest relevant live URL.'))
        return summary, issues
    if 'html' not in document.get('content_type', '') and '<html' not in document.get('text', '').lower():
        issues.append(_issue('non_html', 'indexability', 'warning', url, 'Page did not return HTML', 'The audited URL returned a non-HTML response.', 'Confirm this URL is intended to appear in organic search.'))
        return summary, issues

    soup = BeautifulSoup(document['text'], 'html.parser')
    title = unescape(soup.title.get_text(' ', strip=True)) if soup.title else ''
    description_tag = soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)})
    description = (description_tag.get('content') or '').strip() if description_tag else ''
    h1s = [item.get_text(' ', strip=True) for item in soup.find_all('h1') if item.get_text(' ', strip=True)]
    canonical_tag = soup.find('link', attrs={'rel': lambda value: value and 'canonical' in value})
    canonical = urljoin(url, canonical_tag.get('href', '').strip()) if canonical_tag and canonical_tag.get('href') else ''
    robots_values = ' '.join((item.get('content') or '') for item in soup.find_all('meta', attrs={'name': re.compile(r'robots|googlebot', re.I)})).lower()
    viewport = soup.find('meta', attrs={'name': re.compile(r'^viewport$', re.I)})
    language = (soup.html.get('lang') or '').strip() if soup.html else ''
    images = soup.find_all('img')
    missing_alt = sum(1 for image in images if image.get('alt') is None)
    structured_data = soup.find_all('script', attrs={'type': re.compile(r'application/ld\+json', re.I)})
    visible_text = ' '.join(soup.stripped_strings)
    word_count = len(re.findall(r"\b[\w'-]+\b", visible_text))
    site_host = (urlparse(url).hostname or '').lower()
    internal_links = []
    for anchor in soup.find_all('a', href=True):
        candidate = urljoin(url, anchor.get('href', '').strip()).split('#', 1)[0]
        if candidate.startswith(('http://', 'https://')) and _same_site(candidate, site_host) and candidate not in internal_links:
            internal_links.append(candidate)

    summary.update({
        'title': title,
        'description': description,
        'h1': h1s[0] if h1s else '',
        'canonical': canonical,
        'word_count': word_count,
        'internal_links': internal_links[:100],
    })

    if not title:
        issues.append(_issue('missing_title', 'metadata', 'critical', url, 'Missing page title', 'The page has no HTML title for search results and browser tabs.', 'Write a unique, descriptive title that accurately summarizes this page.'))
    elif len(title) > 70:
        issues.append(_issue('long_title', 'metadata', 'notice', url, 'Page title may be truncated', f'The title is {len(title)} characters long.', 'Make the title concise while keeping the most useful words near the beginning.'))
    if not description:
        issues.append(_issue('missing_description', 'metadata', 'warning', url, 'Missing meta description', 'Search engines may need to generate a less controlled search-result snippet.', 'Add a concise, page-specific description written for people.'))
    if not h1s:
        issues.append(_issue('missing_h1', 'content', 'warning', url, 'Missing primary heading', 'The page has no clear H1 describing its main topic.', 'Add one clear primary heading that matches the page purpose.'))
    if 'noindex' in robots_values:
        issues.append(_issue('noindex', 'indexability', 'critical', url, 'Page is marked noindex', 'The page explicitly asks search engines not to index it.', 'Remove noindex if this page should appear in search results.'))
    if not canonical:
        issues.append(_issue('missing_canonical', 'indexability', 'notice', url, 'Canonical URL is not declared', 'The page does not state its preferred URL version.', 'Add a self-referencing canonical when multiple URL versions may exist.'))
    elif not _same_site(canonical, site_host):
        issues.append(_issue('external_canonical', 'indexability', 'warning', url, 'Canonical points to another website', f'The declared canonical is {canonical}.', 'Confirm this is intentional; otherwise point the canonical to the preferred URL on this site.'))
    if not viewport:
        issues.append(_issue('missing_viewport', 'mobile', 'warning', url, 'Mobile viewport is missing', 'The page may not render correctly on mobile devices.', 'Add a responsive viewport meta tag and verify the mobile layout.'))
    if not language:
        issues.append(_issue('missing_language', 'accessibility', 'notice', url, 'Document language is missing', 'Browsers and assistive technology cannot identify the page language.', 'Set the lang attribute on the HTML element.'))
    if images and missing_alt:
        issues.append(_issue('missing_alt', 'accessibility', 'warning', url, 'Images are missing alternative text', f'{missing_alt} of {len(images)} images have no alt attribute.', 'Add useful alt text to meaningful images and empty alt text to decorative images.'))
    if homepage and not structured_data:
        issues.append(_issue('missing_structured_data', 'structured_data', 'notice', url, 'No structured data detected on the homepage', 'Eligible structured data can help search engines understand the organization and site.', 'Add valid Organization or WebSite JSON-LD only when it matches visible, accurate information.'))
    if word_count < 120:
        issues.append(_issue('limited_content', 'content', 'notice', url, 'Limited indexable page content', f'Approximately {word_count} visible words were detected.', 'Confirm the page fully answers the visitor’s main question without padding or keyword repetition.'))
    if document.get('elapsed_ms', 0) > 1800:
        issues.append(_issue('slow_server_response', 'performance', 'warning', url, 'Slow server response during audit', f'The HTML response took about {document["elapsed_ms"]} ms.', 'Investigate server latency and then validate real user Core Web Vitals in Search Console.'))

    return summary, issues


def audit_site(site_url, max_pages=20, fetcher=fetch_document):
    site_url = normalize_site_url(site_url)
    site_host = (urlparse(site_url).hostname or '').lower()
    max_pages = max(1, min(int(max_pages or 20), 50))
    issues = []
    pages = []

    homepage = fetcher(site_url)
    home_summary, home_issues = analyze_page(homepage, homepage=True)
    pages.append(home_summary)
    issues.extend(home_issues)

    robots_url = urljoin(f'{site_url}/', 'robots.txt')
    sitemap_url = urljoin(f'{site_url}/', 'sitemap.xml')
    robots_ok = False
    sitemap_ok = False
    sitemap_urls = []

    try:
        robots_doc = fetcher(robots_url)
        robots_ok = robots_doc['status'] < 400
        if not robots_ok:
            issues.append(_issue('robots_unavailable', 'discovery', 'warning', robots_url, 'robots.txt is unavailable', f'The file returned HTTP {robots_doc["status"]}.', 'Publish a valid robots.txt file at the site root.'))
        elif re.search(r'(?im)^\s*disallow\s*:\s*/\s*$', robots_doc['text']):
            issues.append(_issue('robots_blocks_site', 'indexability', 'critical', robots_url, 'robots.txt may block the entire site', 'A Disallow: / directive was detected.', 'Review the applicable user-agent group and remove the block if public pages should be crawled.'))
    except Exception as exc:
        issues.append(_issue('robots_unavailable', 'discovery', 'warning', robots_url, 'robots.txt could not be checked', str(exc), 'Publish a reachable robots.txt file at the site root.'))

    try:
        sitemap_doc = fetcher(sitemap_url)
        sitemap_ok = sitemap_doc['status'] < 400
        if sitemap_ok:
            sitemap_urls = _parse_sitemap(sitemap_doc['text'], site_host, max_pages)
            if not sitemap_urls:
                issues.append(_issue('empty_sitemap', 'discovery', 'warning', sitemap_url, 'Sitemap contains no usable page URLs', 'No same-site page URLs were found in sitemap.xml.', 'Include absolute canonical URLs that should appear in search results.'))
        else:
            issues.append(_issue('sitemap_unavailable', 'discovery', 'warning', sitemap_url, 'sitemap.xml is unavailable', f'The file returned HTTP {sitemap_doc["status"]}.', 'Publish a valid XML sitemap at the site root and submit it in Search Console.'))
    except Exception as exc:
        issues.append(_issue('sitemap_unavailable', 'discovery', 'warning', sitemap_url, 'sitemap.xml could not be checked', str(exc), 'Publish a valid XML sitemap at the site root and submit it in Search Console.'))

    candidates = sitemap_urls or home_summary.get('internal_links', [])
    seen = {homepage['url'].rstrip('/')}
    for candidate in candidates:
        if len(pages) >= max_pages:
            break
        normalized = candidate.rstrip('/')
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            document = fetcher(candidate)
            page_summary, page_issues = analyze_page(document)
            pages.append(page_summary)
            issues.extend(page_issues)
        except Exception as exc:
            pages.append({'url': candidate, 'status': 0, 'elapsed_ms': 0, 'title': '', 'h1': '', 'canonical': '', 'word_count': 0, 'internal_links': []})
            issues.append(_issue('fetch_failed', 'indexability', 'critical', candidate, 'Page audit failed', str(exc), 'Confirm the page is publicly reachable and returns valid HTML.'))

    titles = {}
    for page in pages:
        title = (page.get('title') or '').strip().lower()
        if title:
            titles.setdefault(title, []).append(page['url'])
    for duplicate_title, urls in titles.items():
        if len(urls) > 1:
            for duplicate_url in urls:
                issues.append(_issue('duplicate_title', 'metadata', 'warning', duplicate_url, 'Duplicate page title', f'The same title appears on {len(urls)} audited pages.', 'Write a unique title that reflects this page’s specific purpose.'))

    weights = {'critical': 16, 'warning': 5, 'notice': 1}
    score = max(0, 100 - sum(weights.get(item['severity'], 0) for item in issues))
    latencies = [page.get('elapsed_ms', 0) for page in pages if page.get('elapsed_ms')]
    return {
        'site_url': site_url,
        'score': score,
        'pages_checked': len(pages),
        'critical_count': sum(1 for item in issues if item['severity'] == 'critical'),
        'warning_count': sum(1 for item in issues if item['severity'] == 'warning'),
        'notice_count': sum(1 for item in issues if item['severity'] == 'notice'),
        'robots_ok': robots_ok,
        'sitemap_ok': sitemap_ok,
        'average_response_ms': int(sum(latencies) / len(latencies)) if latencies else 0,
        'pages': pages,
        'issues': issues,
    }


def inspect_backlink(prospect_url, target_site_url, fetcher=fetch_document):
    document = fetcher(prospect_url)
    if document['status'] >= 400:
        return {'status': 'unreachable', 'http_status': document['status'], 'link_url': None, 'attributes': []}
    soup = BeautifulSoup(document['text'], 'html.parser')
    target_host = (urlparse(normalize_site_url(target_site_url)).hostname or '').lower()
    for anchor in soup.find_all('a', href=True):
        destination = urljoin(document['url'], anchor['href'])
        if _same_site(destination, target_host):
            rel = [str(value).lower() for value in (anchor.get('rel') or [])]
            return {'status': 'earned', 'http_status': document['status'], 'link_url': destination, 'attributes': rel}
    return {'status': 'prospect', 'http_status': document['status'], 'link_url': None, 'attributes': []}


def build_content_brief(keyword, intent='informational', target_url=''):
    keyword = re.sub(r'\s+', ' ', (keyword or '').strip())
    if not keyword:
        raise ValueError('Keyword is required.')
    clean_title = keyword.title()
    slug = re.sub(r'[^a-z0-9]+', '-', keyword.lower()).strip('-')
    angle = {
        'commercial': 'help readers compare options and make a confident decision',
        'transactional': 'help ready-to-act readers complete the next step safely',
        'navigational': 'help readers find the exact NovaBrief resource they need',
    }.get(intent, 'answer the reader’s main question with practical, original guidance')
    return {
        'keyword': keyword,
        'intent': intent,
        'working_title': f'{clean_title}: A Practical NovaBrief Guide',
        'slug': slug,
        'meta_description': f'Understand {keyword} with a practical guide from NovaBrief Tech, including clear steps, useful examples, and next actions.'[:155],
        'audience_goal': angle,
        'target_url': target_url,
        'outline': [
            f'What {keyword} means and why it matters',
            'The key decisions readers need to make',
            'A practical step-by-step approach',
            'Common mistakes and how to avoid them',
            'Recommended next steps and relevant NovaBrief resources',
        ],
        'quality_checks': [
            'Use first-hand examples or clearly attributed sources',
            'Answer the search intent before adding promotional material',
            'Link to relevant internal pages with descriptive anchor text',
            'Avoid keyword repetition that sounds unnatural',
            'Review accuracy, authorship, and update dates before publishing',
        ],
    }
