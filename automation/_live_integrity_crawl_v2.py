#!/usr/bin/env python3
"""
Live site integrity crawl for https://ziontechgroup.com
Single-threaded BFS — reliable, deterministic, no threading races.
"""
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
SCHEME = "https"
HOST = "ziontechgroup.com"
FETCH_TIMEOUT = 25

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (zion-integrity-crawl/1.0)",
})

visited = set()
queue = []
broken = []
redirects = []
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
    return url

def fetch(url):
    try:
        return session.get(url, allow_redirects=True, timeout=FETCH_TIMEOUT)
    except Exception:
        return None

# seed
queue.append(BASE)

while queue:
    url = queue.pop(0)
    url = normalize(url)
    if url in visited:
        continue
    visited.add(url)
    total += 1
    print(f"[{total}] {url}", flush=True)

    resp = fetch(url)
    if resp is None:
        broken.append((url, "missing page (connection exception)"))
        continue

    status = resp.status_code

    # track redirect chain
    for h in resp.history:
        redirects.append((url, h.url, h.status_code))

    if status == 200:
        ok200 += 1
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for tag in soup.find_all(["a", "link"]):
            href = tag.get("href")
            if not href:
                continue
            full = normalize(urljoin(url, href))
            if not is_internal(full):
                continue
            if full not in visited and full not in queue:
                queue.append(full)
        continue

    if 300 <= status < 400:
        final = resp.url
        if not is_internal(final):
            reason = f"stale redirect (3xx -> external {final})"
        else:
            reason = f"stale redirect (3xx internal, final {final} status {resp.status_code})"
        broken.append((url, reason))
        continue

    broken.append((url, f"missing page (HTTP {status})"))

# ---------- REPORT ----------
print("\n" + "=" * 60)
print("INTEGRITY REPORT — https://ziontechgroup.com")
print("=" * 60)
print(f"Total crawled:     {total}")
print(f"HTTP 200:          {ok200}")
print(f"Broken:            {len(broken)}")
print(f"Redirects tracked: {len(redirects)}")
print()
if broken:
    print("First 10 broken URLs:")
    for i, (u, r) in enumerate(broken[:10], 1):
        print(f"  {i}. {u}")
        print(f"     → {r}")
    print()
    stale = sum(1 for _, r in broken if r.startswith("stale redirect"))
    missing = sum(1 for _, r in broken if r.startswith("missing page"))
    ext = sum(1 for _, r in broken if "external" in r.lower())
    print("Classification summary:")
    print(f"  stale redirect:          {stale}")
    print(f"  missing page:            {missing}")
    print(f"  external reference error: {ext}")
else:
    print("Site healthy — no broken internal links found.")
print("=" * 60)
