#!/usr/bin/env python3
"""Live site integrity check for https://ziontechgroup.com — BFS crawl."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import time

BASE = "https://ziontechgroup.com"
MAX_PAGES = 200
DELAY = 0.3  # polite crawl delay

session = requests.Session()
session.headers.update({
    "User-Agent": "ZionIntegrityCheck/1.0 (+https://ziontechgroup.com)",
})

visited = set()
broken = []
ok_count = 0
total = 0
queue = [BASE]

def is_internal(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    return netloc == "ziontechgroup.com" or netloc == ""

def classify_broken(url, final_url, status_code, error):
    """Classify: stale redirect, missing page, or external reference error."""
    if error is not None:
        return "external reference error"
    # Check if it ended up on an external domain
    if urlparse(final_url).netloc != "ziontechgroup.com":
        return "external reference error"
    # 404-like → missing page
    if status_code in (404, 410):
        return "missing page"
    if status_code >= 400:
        return "missing page"
    # Redirect to something non-200 or external
    if status_code in (301, 302, 307, 308):
        # Already followed redirects; if we got here with a non-200, it means
        # the redirect target failed
        if status_code != 200:
            return "stale redirect"
    return "missing page"

while queue and total < MAX_PAGES:
    url = queue.pop(0)
    if url in visited:
        continue
    if not is_internal(url):
        continue
    if url.endswith(".png") or url.endswith(".jpg") or url.endswith(".jpeg") or url.endswith(".gif") or url.endswith(".svg") or url.endswith(".css") or url.endswith(".js") or url.endswith(".woff") or url.endswith(".woff2") or url.endswith(".ico"):
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
                    absolute = urljoin(url, str(href))
                    if is_internal(absolute) and absolute not in visited:
                        queue.append(absolute)
        else:
            broken.append((url, resp.url, status, None))
        time.sleep(DELAY)
    except Exception as e:
        broken.append((url, url, None, str(e)))
        time.sleep(DELAY)

print(f"Total crawled: {total}")
print(f"HTTP 200 count: {ok_count}")
print(f"Broken count: {len(broken)}")

if broken:
    print("\nFirst 10 broken URLs:")
    for i, (url, final, status, err) in enumerate(broken[:10]):
        classification = classify_broken(url, final, status, err)
        if err:
            detail = f"error: {err}"
        elif status:
            detail = f"status {status} → {final}"
        else:
            detail = "unknown"
        print(f"  [{i+1}] {url}")
        print(f"      classification: {classification} | {detail}")
else:
    print("\nNo broken URLs found.")
