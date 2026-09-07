#!/usr/bin/env python3
"""
Live site integrity crawl for https://ziontechgroup.com
Seeds from sitemap.xml, then BFS-follows internal links.
Classifies broken URLs as: stale redirect, missing page, external reference error.
"""
import sys, json, os, re
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ziontechgroup.com"
BASE_NETLOC = urlparse(BASE_URL).netloc
TIMEOUT = 20
MAX_PAGES = 5000

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ZionIntegrityCrawl/1.0)"
})

def normalize(url: str) -> str:
    p = urlparse(url)
    p = p._replace(fragment="", scheme=p.scheme.lower(), netloc=p.netloc.lower())
    return urlunparse(p)

def is_internal(url: str) -> bool:
    return urlparse(url).netloc.lower() == BASE_NETLOC

def probe(url: str):
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        return resp.status_code, resp.url, None
    except requests.RequestException as e:
        return None, url, e

def classify(url: str, status, final_url, exc) -> str:
    if exc is not None:
        return "missing page" if is_internal(url) else "external reference error"
    if status is None:
        return "missing page"
    if 200 <= status < 300:
        return "ok"
    if is_internal(url):
        if final_url and urlparse(final_url).netloc.lower() != BASE_NETLOC:
            return "stale redirect"
        if status >= 400:
            return "missing page"
        return "stale redirect"
    return "external reference error"

def extract_intralinks(html: str, page_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all(["a", "link"], href=True):
        href = tag.get("href")
        if href is None:
            continue
        full = normalize(urljoin(page_url, href))
        if not is_internal(full):
            continue
        path = urlparse(full).path
        if path.endswith((".png",".jpg",".jpeg",".gif",".svg",".ico",
                          ".css",".js",".woff",".woff2",".ttf",".eot")):
            continue
        if full not in visited and full not in queue:
            links.append(full)
    return links

# --- 1. Seed from sitemap ---
print("Fetching sitemap...", file=sys.stderr)
try:
    sm_resp = session.get(f"{BASE_URL}/sitemap.xml", timeout=30)
    sm_urls = re.findall(r'<loc>(.*?)</loc>', sm_resp.text)
    seed_urls = [normalize(u) for u in sm_urls if is_internal(u)]
    print(f"Sitemap: {len(seed_urls)} URLs seeded", file=sys.stderr)
except Exception as e:
    print(f"Sitemap fetch failed: {e} — seeding from homepage only", file=sys.stderr)
    seed_urls = [normalize(BASE_URL)]

# --- 2. BFS crawl ---
visited = set()
queue = deque()

for u in seed_urls:
    if u not in visited:
        visited.add(u)
        queue.append(u)

total_crawled = 0
http_200 = 0
broken = []
redirects = []

print(f"Starting BFS crawl from {len(queue)} seed URLs...", file=sys.stderr)

while queue and total_crawled < MAX_PAGES:
    url = queue.popleft()
    total_crawled += 1

    status, final_url, exc = probe(url)

    if exc is None and status is not None and 200 <= status < 300:
        http_200 += 1
        if status in (301, 302, 303, 307, 308):
            redirects.append((url, final_url, status))
        # Extract links from live pages
        try:
            html = session.get(url, timeout=TIMEOUT).text
            for link in extract_intralinks(html, url):
                if link not in visited:
                    visited.add(link)
                    queue.append(link)
        except Exception:
            pass
    else:
        classification = classify(url, status, final_url, exc)
        broken.append((url, status if exc is None else f"ERR: {type(exc).__name__}", classification))

    if total_crawled % 100 == 0:
        print(f"  crawled {total_crawled}, 200s: {http_200}, broken: {len(broken)}...", file=sys.stderr)

print(f"\nCrawl complete: {total_crawled} pages, {http_200} HTTP 200, {len(broken)} broken", file=sys.stderr)

# --- 3. Classify & report ---
class_counts = {}
for _, _, c in broken:
    class_counts[c] = class_counts.get(c, 0) + 1

print("\n=== INTEGRITY CHECK REPORT ===")
print(f"Site: {BASE_URL}")
print(f"Total crawled (internal pages): {total_crawled}")
print(f"HTTP 200 count: {http_200}")
print(f"Broken count: {len(broken)}")
print()
if broken:
    print("First 10 broken URLs:")
    for i, (u, s, c) in enumerate(broken[:10], 1):
        print(f"  {i}. {u}")
        print(f"     Status: {s}  |  Classification: {c}")
    print()
    print("Classification summary:")
    for c, n in sorted(class_counts.items()):
        print(f"  {c}: {n}")
else:
    print("No broken URLs found.")

# Write report
report = {
    "site": BASE_URL,
    "total_crawled": total_crawled,
    "http_200_count": http_200,
    "broken_count": len(broken),
    "broken_urls": [{"url": u, "status": s, "classification": c} for u, s, c in broken[:10]],
    "classification_summary": class_counts,
}
out_path = "/Users/miami2/zion.app/automation/reports/site-integrity-latest.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\nJSON report: {out_path}")
