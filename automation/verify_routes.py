import requests
import re
from urllib.parse import urljoin

BASE = 'https://ziontechgroup.com'
routes = [
    '/', '/public-roadmap', '/status-page', '/use-cases',
    '/solutions/healthcare', '/industries/financial-services',
    '/free-consultation', '/tools/phishing-analyzer'
]

print('=== LIVE RE-VERIFICATION after deploy ===')
for r in routes:
    u = urljoin(BASE, r) if r != '/' else BASE
    try:
        resp = requests.get(u, timeout=20, allow_redirects=True)
        canon = ''
        m = re.search(r'<link rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', resp.text)
        if m:
            canon = m.group(1)
        print(f'{resp.status_code:3d}  {r:35s} -> {resp.url}')
        if canon:
            expected = u if r != '/' else BASE
            ok = '✓' if canon.rstrip('/') == expected.rstrip('/') else '✗'
            print(f'     canonical: {canon} {ok}')
        else:
            print('     canonical: (none)')
    except Exception as e:
        print(f'ERR  {r:35s} -> {e}')
