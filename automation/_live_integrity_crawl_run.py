#!/usr/bin/env python3
"""
Live site integrity crawl for https://ziontechgroup.com
- BFS over internal links only
- reports total, 200 count, broken count, first 10 broken URLs
- classifies broken: stale redirect / missing page / external reference error
"""
import sys
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
SCHEME = "https"
HOST = "ziontechgroup.com"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; integrity-check/1.0)",
})
session.timeout = 20

visited = set()
queue = [BASE]
broken = []       # (url, classification_reason)
redirects = []    # (from_url, to_url, status)
total = 0
ok200 = 0

def strip_fragment(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

def is_internal(url):
    p = urlparse(url)
    return p.scheme in (SCHEME, "") and (p.netloc == HOST or p.netloc == "")

def normalize(url):
    url = strip_fragment(url)
    if urlparse(url).scheme == "":
        url = urljoin(BASE + "/", url)
    # strip trailing query/fragment noise, keep path
    return url

def fetch(url):
    try:
        resp = session.get(url, allow_redirects=True, timeout=20)
        return resp
    except Exception as e:
        return None

print(f"Starting crawl of {BASE}", flush=True)

while queue:
    url = queue.pop(0)
    url = normalize(url)
    if url in visited:
        continue
    visited.add(url)
    total += 1

    print(f"[{total}] FETCH {url}", flush=True)
    resp = fetch(url)
    if resp is None:
        broken.append((url, "missing page (connection exception)"))
        continue

    status = resp.status_code

    # track redirects
    if len(resp.history) > 0:
        for h in resp.history:
            redirects.append((url, h.url, h.status_code))

    if status == 200:
        ok200 += 1
        # extract links
        try:
            html = resp.text
        except Exception:
            html = ""
        if len(html) > 0:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception:
                soup = BeautifulSoup("", "html.parser")
            for tag in soup.find_all(["a", "link"]):
                href = tag.get("href")
                if not href:
                    continue
                full = urljoin(url, href)
                full = normalize(full)
                if not is_internal(full):
                    continue
                if full not in visited and full not in queue:
                    queue.append(full)
        continue

    # non-200 handling
    if 300 <= status < 400:
        # check if final target is external
        final_url = resp.url
        if not is_internal(final_url):
            broken.append((url, f"stale redirect (3xx -> external {final_url})"))
        else:
            broken.append((url, f"stale redirect (3xx internal, final {final_url} status {resp.status_code})"))
        # still try to follow for more links if it eventually got somewhere
        if status == 200:
            ok200 += 1
        continue

    # 4xx, 5xx, etc.
    broken.append((url, f"missing page (HTTP {status})"))

# report
print("\n===== INTEGRITY REPORT =====", flush=True)
print(f"Base URL: {BASE}", flush=True)
print(f"Total crawled: {total}", flush=True)
print(f"HTTP 200: {ok200}", flush=True)
print(f"Broken: {len(broken)}", flush=True)
print(f"Redirects tracked: {len(redirects)}", flush=True)
print("\n--- First 10 broken URLs ---", flush=True)
for i, (url, reason) in enumerate(broken[:10], 1):
    print(f"{i}. {url}  [{reason}]", flush=True)

if len(broken) == 0:
    print("\nSite healthy — no broken internal links found.", flush=True)
else:
    # classification summary
    stale = sum(1 for _, r in broken if r.startswith("stale redirect"))
    missing = sum(1 for _, r in broken if r.startswith("missing page"))
    ext_err = sum(1 for _, r in broken if "external" in r.lower())
    print(f"\n--- Classification summary ---", flush=True)
    print(f"  stale redirect: {stale}", flush=True)
    print(f"  missing page: {missing}", flush=True)
    print(f"  external reference error: {ext_err}", flush=True)

print("\n===== END =====", flush=True)
