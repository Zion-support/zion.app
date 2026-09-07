import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import sys
from collections import deque

BASE = "https://ziontechgroup.com"
START = BASE + "/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def is_internal(url, base):
    parsed = urlparse(url)
    base_parsed = urlparse(base)
    return parsed.netloc == "" or parsed.netloc == base_parsed.netloc

visited = set()
queue = deque([START])
broken = []
ok_count = 0
broken_count = 0
crawl_count = 0

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

while queue:
    url = queue.popleft()
    url, _ = urldefrag(url)
    if url in visited:
        continue
    visited.add(url)
    crawl_count += 1

    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        status = resp.status_code
        final_url = resp.url
    except requests.RequestException as e:
        broken.append((url, "EXTERNAL REFERENCE ERROR", str(e)))
        broken_count += 1
        if crawl_count % 50 == 0:
            print(f"[Progress] crawled={crawl_count}, ok={ok_count}, broken={broken_count}", file=sys.stderr)
        continue

    if status == 200:
        ok_count += 1
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = str(a["href"])
                full = urljoin(url, href)
                full, _ = urldefrag(full)
                if is_internal(full, BASE) and full not in visited:
                    queue.append(full)
        except Exception:
            pass
    else:
        broken_count += 1
        broken.append((url, f"HTTP {status}", ""))
        if crawl_count % 50 == 0:
            print(f"[Progress] crawled={crawl_count}, ok={ok_count}, broken={broken_count}", file=sys.stderr)

def classify_broken(broken_list):
    results = []
    for url, status_str, err in broken_list:
        if status_str.startswith("HTTP"):
            code = int(status_str.split()[1])
            if code in (301, 302, 307, 308):
                results.append((url, "stale redirect", status_str))
            elif code == 404:
                results.append((url, "missing page", status_str))
            elif code == 403:
                results.append((url, "missing page (forbidden)", status_str))
            elif code >= 500:
                results.append((url, "missing page (server error)", status_str))
            else:
                results.append((url, "missing page", status_str))
        elif status_str == "EXTERNAL REFERENCE ERROR":
            results.append((url, "external reference error", err))
        else:
            results.append((url, "unknown", status_str))
    return results

classified = classify_broken(broken)

print("=" * 70)
print("ZION TEC GROUP — SITE INTEGRITY CHECK")
print("=" * 70)
print(f"Base URL: {BASE}")
print(f"Total crawled: {crawl_count}")
print(f"HTTP 200 count: {ok_count}")
print(f"Broken count: {broken_count}")
print()
if broken_count > 0:
    print("BROKEN URLS — FIRST 10 + CLASSIFICATION")
    print("-" * 70)
    for url, cls, detail in classified[:10]:
        print(f"[{cls}] {url}")
        if detail:
            print(f"         detail: {detail}")
    if len(classified) > 10:
        print(f"\n... and {len(classified) - 10} more broken URLs (truncated)")
else:
    print("No broken URLs found.")
print("=" * 70)
