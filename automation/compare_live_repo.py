#!/usr/bin/env python3
"""Fetch live page content for key routes and compare with repo HTML."""
import requests

routes = {
    '/': 'index.html',
    '/public-roadmap/': 'public-roadmap/index.html',
    '/status-page/': 'status-page/index.html',
    '/use-cases/': 'use-cases/index.html',
    '/solutions/healthcare/': 'solutions/healthcare/index.html',
    '/industries/financial-services/': 'industries/financial-services/index.html',
    '/free-consultation/': 'free-consultation/index.html',
    '/tools/phishing-analyzer/': 'tools/phishing-analyzer/index.html',
}

BASE_REPO = '/Users/miami2/zion-support/zion-support.github.io'
BASE_URL = 'https://ziontechgroup.com'

print('LIVE vs REPO CONTENT COMPARISON')
print('=' * 70)

for route, filename in routes.items():
    url = BASE_URL + route
    repo_path = f'{BASE_REPO}/{filename}'
    
    import re
    # Fetch live
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        live_status = r.status_code
        live_size = len(r.content)
        live_title = ''
        m = re.search(r'<title[^>]*>([^<]+)</title>', r.text, re.I)
        if m:
            live_title = m.group(1).strip()
    except Exception as e:
        live_status = 0
        live_size = 0
        live_title = f'ERROR: {e}'
    
    # Read repo
    try:
        with open(repo_path, 'r') as f:
            repo_content = f.read()
        repo_size = len(repo_content)
        m = re.search(r'<title[^>]*>([^<]+)</title>', repo_content, re.I)
        repo_title = m.group(1).strip() if m else '(no title)'
    except Exception as e:
        repo_size = 0
        repo_title = f'ERROR: {e}'
    
    match = 'MATCH' if live_title == repo_title else 'DIFF'
    size_diff = live_size - repo_size
    
    print(f'Route: {route}')
    print(f'  Live:  status={live_status} size={live_size}B title="{live_title}"')
    print(f'  Repo:  size={repo_size}B title="{repo_title}"')
    print(f'  [{match}] size_diff={size_diff:+d}B')
    print()

print('=' * 70)
print('NOTE: Negative size_diff means live page is SMALLER than repo —')
print('      the live site may be serving a stub or outdated version.')
