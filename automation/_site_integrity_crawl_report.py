#!/usr/bin/env python3
"""Live site integrity check for ziontechgroup.com — BFS crawl, internal links only.

Uses the Python venv at /Users/miami2/zion.app/automation/.crawl-venv.
Does NOT modify files; prints a read-only report.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import sys
import time

BASE_URL = "https://ziontechgroup.com"
MAX_PAGES = 500
DELAY = 0.3
TIMEOUT = 20

def is_internal_url(url: str, base_netloc: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != base_netloc and parsed.netloc != "":
        return False
    # Exclude non-http schemes
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False
    return True

def classify_broken(status_code: int, final_url: str, base_netloc: str) -> str:
    if status_code in (301, 302, 307, 308):
        return "stale_redirect"
    if status_code == 404:
        return "missing_page"
    if status_code >= 500:
        return "server_error"
    parsed = urlparse(final_url)
    if parsed.netloc and parsed.netloc != base_netloc:
        return "external_reference_error"
    if status_code == 0:
        return "connection_error"
    return "unknown"

records = {}
visited = set()
queue = deque([BASE_URL])
success_count = 0
broken_count = 0
total_crawled = 0

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; SiteIntegrityCheck/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

print(f"Starting crawl of {BASE_URL} ...", file=sys.stderr)

while queue and total_crawled < MAX_PAGES:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)
    total_crawled += 1

    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        final_url = resp.url
        status = resp.status_code

        if status == 200:
            success_count += 1
            # Extract links to queue
            if "text/html" in resp.headers.get("content-type", ""):
                try:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        link = str(a["href"]).strip()
                        if link.startswith("#") or link.startswith("javascript:") or \
                           link.startswith("mailto:") or link.startswith("tel:"):
                            continue
                        full_url = urljoin(final_url, link)
                        if is_internal_url(full_url, urlparse(BASE_URL).netloc):
                            if full_url not in visited:
                                queue.append(full_url)
                except Exception:
                    pass
        else:
            broken_count += 1
            category = classify_broken(status, final_url, urlparse(BASE_URL).netloc)
            records[url] = (status, category, final_url)
            # Still try to extract links even from error pages
            if "text/html" in resp.headers.get("content-type", ""):
                try:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        link = str(a["href"]).strip()
                        if link.startswith("#") or link.startswith("javascript:") or \
                           link.startswith("mailto:") or link.startswith("tel:"):
                            continue
                        full_url = urljoin(final_url, link)
                        if is_internal_url(full_url, urlparse(BASE_URL).netloc):
                            if full_url not in visited:
                                queue.append(full_url)
                except Exception:
                    pass

    except requests.exceptions.Timeout:
        broken_count += 1
        records[url] = (0, "timeout", url)
    except requests.exceptions.ConnectionError:
        broken_count += 1
        records[url] = (0, "connection_error", url)
    except Exception as e:
        broken_count += 1
        records[url] = (0, "error:" + str(e)[:60], url)

    time.sleep(DELAY)

# Report
print("=" * 60)
print("SITE INTEGRITY CHECK REPORT")
print("=" * 60)
print(f"Target:       {BASE_URL}")
print(f"Total crawled: {total_crawled}")
print(f"HTTP 200:      {success_count}")
print(f"Broken:        {broken_count}")
print("=" * 60)

if broken_count > 0:
    print("\nBROKEN URLS (first 10):")
    print("-" * 60)
    broken_list = list(records.items())
    for i, (url, (code, cat, final)) in enumerate(broken_list[:10]):
        extra = f" -> {final}" if final != url else ""
        print(f"  {i+1}. [{code or 'ERR'}] ({cat}){extra}")
        print(f"     {url}")
    print("-" * 60)

    cats = {}
    for url, (code, cat, final) in records.items():
        cats[cat] = cats.get(cat, 0) + 1
    print("\nBreakdown by classification:")
    for cat, cnt in sorted(cats.items()):
        print(f"  {cat}: {cnt}")
else:
    print("\nNo broken URLs found. Site appears healthy.")

print("\nDone.")
