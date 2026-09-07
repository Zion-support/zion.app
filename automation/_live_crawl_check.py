#!/usr/bin/env python3
"""Live site integrity check for https://ziontechgroup.com — BFS crawl."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag, urlunparse
from collections import deque
import sys
import time

BASE = "https://ziontechgroup.com"
MAX_PAGES = 500
DELAY = 0.3

session = requests.Session()
session.headers.update({
    "User-Agent": "ZionIntegrityCheck/1.0 (+https://ziontechgroup.com)",
})

visited = set()
broken = []
ok_count = 0
total = 0
queue = deque([BASE])

def is_internal(url):
    parsed = urlparse(url)
    return parsed.netloc.lower() in ("ziontechgroup.com", "") or parsed.netloc.endswith(".ziontechgroup.com")

def strip_fragment(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

def classify(url, final_url, status_code, error):
    """Classify broken URL: stale redirect, missing page, external reference error."""
    if error is not None:
        return "external reference error"
    if urlparse(final_url).netloc.lower() not in ("ziontechgroup.com", ""):
        return "external reference error"
    if status_code in (404, 410):
        return "missing page"
    if status_code >= 400:
        return "missing page"
    if status_code in (301, 302, 307, 308):
        return "stale redirect"
    return "missing page"

while queue and total < MAX_PAGES:
    url = queue.popleft()
    url = strip_fragment(url)
    if url in visited:
        continue
    if not is_internal(url):
        continue
    # Skip static assets and non-HTTP schemes
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".woff", ".woff2", ".ico", ".webp")):
        continue
    if parsed.scheme in ("mailto", "tel", "javascript"):
        continue
    visited.add(url)
    total += 1

    try:
        resp = session.get(url, timeout=20, allow_redirects=True)
        status = resp.status_code
        if status == 200:
            ok_count += 1
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href:
                    absolute = strip_fragment(urljoin(url, str(href)))
                    if is_internal(absolute) and absolute not in visited:
                        queue.append(absolute)
        else:
            broken.append((url, resp.url, status, None))
        time.sleep(DELAY)
    except Exception as e:
        broken.append((url, url, None, str(e)))
        time.sleep(DELAY)

print(f"\n=== Site Integrity Report: https://ziontechgroup.com ===")
print(f"Total crawled: {total}")
print(f"HTTP 200 count: {ok_count}")
print(f"Broken count: {len(broken)}")

if broken:
    print(f"\n--- First 10 broken URLs ---")
    for i, (url, final, status, err) in enumerate(broken[:10], 1):
        reason = classify(url, final, status, err)
        print(f"{i}. {url}")
        print(f"   Classification: {reason}")
        if status:
            print(f"   HTTP status: {status}")
        if final and final != url:
            print(f"   Final URL: {final}")
        if err:
            print(f"   Error: {err}")
        print()

    print(f"\n--- Full broken classification ---")
    from collections import Counter
    cls = Counter()
    for url, final, status, err in broken:
        cls[classify(url, final, status, err)] += 1
    for c, n in cls.most_common():
        print(f"  {c}: {n}")
else:
    print("\nNo broken URLs found. Site healthy.")
