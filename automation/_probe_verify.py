import requests
import re

urls = [
    'https://ziontechgroup.com/',
    'https://ziontechgroup.com/public-roadmap/',
    'https://ziontechgroup.com/status-page/',
    'https://ziontechgroup.com/use-cases/',
    'https://ziontechgroup.com/solutions/healthcare/',
    'https://ziontechgroup.com/industries/financial-services/',
    'https://ziontechgroup.com/free-consultation/',
    'https://ziontechgroup.com/tools/phishing-analyzer/',
]
markers = {
    '/public-roadmap/': ['Public Roadmap', 'what Zion is building'],
    '/status-page/': ['Status Page', 'operational status'],
    '/use-cases/': ['Use-cases', 'Discover how Zion'],
    '/solutions/healthcare/': ['Healthcare Solutions', 'healthcare delivery'],
    '/industries/financial-services/': ['Financial Services', 'governance'],
    '/free-consultation/': ['Free Consultation', 'AI/IT Discovery'],
    '/tools/phishing-analyzer/': ['Phishing Analyzer', 'phishing'],
}
for u in urls:
    r = requests.get(u, timeout=20)
    body = r.text
    live_ok = r.status_code == 200 and len(body) > 500
    marker_hit = True
    if u in markers:
        hit = any(m in body for m in markers[u])
        if not hit:
            marker_hit = False
    status = 'LIVE' if live_ok else 'STALE/SHORT'
    print(f'{r.status_code:3d} {u:50s} {len(body):6d}B  {status}  marker={"yes" if marker_hit else "NO"}')
    if u in markers and not marker_hit:
        title = re.search(r'<title>([^<]+)</title>', body)
        canonical = re.search(r'canonical[^>]+href="([^"]+)"', body)
        print(f'    title: {title.group(1) if title else "NONE"}')
        print(f'    canonical: {canonical.group(1) if canonical else "NONE"}')
        print(f'    first 300 chars: {body[:300]}')
