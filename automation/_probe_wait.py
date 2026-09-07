import requests, re, time, sys

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
    '/public-roadmap/': ['Public Roadmap', 'See what Zion is building next'],
    '/status-page/': ['Status Page', 'All systems operational'],
    '/use-cases/': ['Use-cases', 'Discover how Zion Tech Group delivers'],
    '/solutions/healthcare/': ['Healthcare Solutions', 'Modernize healthcare delivery'],
    '/industries/financial-services/': ['Financial Services', 'governance'],
    '/free-consultation/': ['Free Consultation', 'AI/IT Discovery'],
    '/tools/phishing-analyzer/': ['Phishing Analyzer', 'phishing'],
}

def probe():
    results = []
    for u in urls:
        r = requests.get(u, timeout=20)
        body = r.text
        title = re.search(r'<title>([^<]+)</title>', body)
        canonical = re.search(r'canonical[^>]+href="([^"]+)"', body)
        tsize = len(body)
        live = r.status_code == 200 and tsize > 1000
        results.append((u, r.status_code, tsize, live, title, canonical, body[:200]))
    return results

for attempt in range(4):
    print(f"\n=== Attempt {attempt+1} ===")
    results = probe()
    all_live = True
    for u, sc, tsize, live, title, canonical, snippet in results:
        flag = 'LIVE' if live else f'SHORT({tsize}B)'
        print(f'{sc:3d} {u:50s} {tsize:6d}B  {flag}')
        if title: print(f'    title: {title.group(1)}')
        if canonical: print(f'    canonical: {canonical.group(1)}')
        if not live:
            all_live = False
    if all_live:
        print("\nALL ROUTES LIVE with full content.")
        sys.exit(0)
    print("Not all live yet, waiting 60s...")
    time.sleep(60)

print("\nAfter 4 attempts, not all routes serve full content.")
sys.exit(1)
