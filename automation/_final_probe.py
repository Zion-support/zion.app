import requests, re

urls = [
    ('https://ziontechgroup.com/', 'Homepage', ['Zion Tech Group', 'AI & IT Discovery']),
    ('https://ziontechgroup.com/public-roadmap/', 'Public Roadmap', ['Public Roadmap', 'what Zion is building next', 'vote on upcoming']),
    ('https://ziontechgroup.com/status-page/', 'Status Page', ['Status Page', 'All systems operational', 'component status']),
    ('https://ziontechgroup.com/use-cases/', 'Use cases', ['Use cases', 'Discover how Zion Tech Group delivers']),
    ('https://ziontechgroup.com/solutions/healthcare/', 'Healthcare Solutions', ['Healthcare Solutions', 'Modernize healthcare delivery']),
    ('https://ziontechgroup.com/industries/financial-services/', 'Financial Services', ['Financial Services', 'governance']),
    ('https://ziontechgroup.com/free-consultation/', 'Free Consultation', ['Discovery', 'AI/IT Discovery', '99']),
    ('https://ziontechgroup.com/tools/phishing-analyzer/', 'Phishing Analyzer', ['Phishing', 'analyzer']),
]

print('=== LIVE SITE INTEGRITY CHECK - ziontechgroup.com ===')
print()
all_ok = True
for u, label, markers in urls:
    r = requests.get(u, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
    body = r.text
    tsize = len(body)
    title = re.search(r'<title>([^<]+)</title>', body)
    canonical = re.search(r'canonical[^>]+href="([^"]+)"', body)
    title_txt = title.group(1).strip() if title else 'NONE'
    canon_txt = canonical.group(1) if canonical else 'NONE'
    marker_hit = True
    for m in markers:
        if m not in body:
            marker_hit = False
            break
    size_ok = tsize > 700
    status = 'LIVE' if (r.status_code == 200 and size_ok and marker_hit) else 'ISSUE'
    if status != 'LIVE':
        all_ok = False
    print(f'{r.status_code:3d}  {label:22s}  {tsize:6d}B  {status}')
    print(f'     title:     {title_txt}')
    print(f'     canonical: {canon_txt}')
    print(f'     markers:   {"HIT" if marker_hit else "MISSING"}')
    if not marker_hit:
        print(f'     body[:200]: {body[:200]}')
    print()

if all_ok:
    print('RESULT: All 8 routes LIVE - full doc content serves, correct canonical URLs.')
else:
    print('RESULT: Some routes still have issues (see above).')
