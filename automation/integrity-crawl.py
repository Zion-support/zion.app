
#!/usr/bin/env python3
"""Site integrity crawler for https://ziontechgroup.com"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

BASE_URL = "https://ziontechgroup.com"
MAX_PAGES = 200
DELAY = 0.3  # seconds between requests

def is_internal(url):
    parsed = urlparse(url)
    base = urlparse(BASE_URL)
    return parsed.netloc == base.netloc or parsed.netloc == ""

def check_url(url):
    try:
        resp = requests.head(url, allow_redirects=True, timeout=15)
        return resp.status_code
    except Exception:
        try:
            resp = requests.get(url, allow_redirects=True, timeout=15)
            return resp.status_code
        except Exception as e:
            return None

def classify_broken(url, status_code, redirects):
    if status_code is None:
        return "external reference error (unreachable)"
    if status_code == 404 or status_code == 410:
        return "missing page"
    if status_code in (403, 401):
        return "missing page (forbidden/unauthorized)"
    if status_code >= 500:
        return "missing page (server error)"
    # Follow redirects to see final
    if redirects:
        final_url = redirects[-1]
        if urlparse(final_url).netloc != urlparse(BASE_URL).netloc:
            return f"stale redirect -> external: {final_url}"
        return f"stale redirect -> {final_url} (status {status_code})"
    return f"unknown error (HTTP {status_code})"

visited = set()
queue = deque([BASE_URL])
broken = []
ok_count = 0
total = 0

print(f"Starting crawl of {BASE_URL}")
print("=" * 60)

while queue and total < MAX_PAGES:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)
    total += 1

    print(f"\n[{total}] Checking: {url}", flush=True)
    status_code = check_url(url)

    if status_code == 200:
        ok_count += 1
        print(f"  -> OK (200)")
        # Extract links
        try:
            resp = requests.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = str(a["href"]).strip()
                # Skip anchors, javascript, emails, tel
                if link.startswith("#") or link.startswith("javascript:") or link.startswith("mailto:") or link.startswith("tel:"):
                    continue
                full_url = urljoin(url, link)
                if is_internal(full_url) and full_url not in visited:
                    queue.append(full_url)
        except Exception as e:
            print(f"  -> Warning: could not parse links: {e}")
    else:
        # Get redirect chain for classification
        redirects = []
        try:
            resp = requests.get(url, allow_redirects=True, timeout=15)
            redirects = resp.history
        except Exception:
            pass
        classification = classify_broken(url, status_code, redirects)
        broken.append({"url": url, "status": status_code, "classification": classification})
        print(f"  -> BROKEN: HTTP {status_code} — {classification}")

    time.sleep(DELAY)

print("\n" + "=" * 60)
print("CRAWL SUMMARY")
print("=" * 60)
print(f"Total crawled:  {total}")
print(f"HTTP 200 OK:    {ok_count}")
print(f"Broken count:   {len(broken)}")
print()

if broken:
    print("BROKEN URLS (first 10):")
    print("-" * 60)
    for i, b in enumerate(broken[:10], 1):
        print(f"{i}. {b['url']}")
        print(f"   Status: {b['status']} | Type: {b['classification']}")
    if len(broken) > 10:
        print(f"\n... and {len(broken) - 10} more broken URLs.")
else:
    print("No broken URLs found.")
