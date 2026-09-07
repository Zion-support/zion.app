"""Live site integrity check for https://ziontechgroup.com
Follows internal links only (BFS), classifies broken URLs.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict

BASE = "https://ziontechgroup.com"
MAX_PAGES = 500
TIMEOUT = 20

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (compatible; IntegrityCrawl/1.0)"

def strip_fragment(url: str) -> str:
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

from urllib.parse import urlunparse

def get_links(html: str, base_url: str):
    """Extract internal links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for tag in soup.find_all(["a", "link"]):
        href = tag.get("href")
        if not href:
            continue
        href = str(href)
        full = urljoin(base_url, href)
        full = strip_fragment(full)
        if not full.startswith(BASE):
            continue  # external only
        links.add(full)
    return links

def classify(url: str, status_code: int, final_url: str, exception: str = None) -> str:
    if exception:
        return "missing page"
    if status_code == 200:
        return "ok"
    # 3xx
    if 300 <= status_code < 400:
        if final_url.startswith(BASE):
            if status_code == 200:
                return "ok"
            return "stale redirect"
        else:
            return "stale redirect"
    # 4xx, 5xx
    if 400 <= status_code < 600:
        return "missing page"
    return "missing page"

visited = set()
queue = deque([BASE])
counts = {"ok": 0, "missing page": 0, "stale redirect": 0, "external reference error": 0}
broken = []

while queue and len(visited) < MAX_PAGES:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)
    
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        final_url = resp.url
        status = resp.status_code
        
        if status == 200:
            counts["ok"] += 1
            # Extract internal links
            try:
                links = get_links(resp.text, url)
                for link in links:
                    if link not in visited:
                        queue.append(link)
            except Exception:
                pass
        elif 300 <= status < 400:
            cls = classify(url, status, final_url)
            counts[cls] += 1
            broken.append((url, status, final_url, cls))
            if cls == "stale redirect":
                # still follow to extract links from final
                try:
                    r2 = session.get(final_url, timeout=TIMEOUT, allow_redirects=True)
                    if r2.status_code == 200:
                        counts["ok"] += 1
                        for link in get_links(r2.text, final_url):
                            if link not in visited:
                                queue.append(link)
                except Exception:
                    pass
            else:
                # try to extract links from the redirect page anyway
                try:
                    r2 = session.get(url, timeout=TIMEOUT, allow_redirects=False)
                    if r2.status_code == 200:
                        for link in get_links(r2.text, url):
                            if link not in visited:
                                queue.append(link)
                except Exception:
                    pass
        else:
            cls = classify(url, status, final_url)
            counts[cls] += 1
            broken.append((url, status, final_url, cls))
            # still try to extract links from error page
            try:
                if resp.text:
                    for link in get_links(resp.text, url):
                        if link not in visited:
                            queue.append(link)
            except Exception:
                pass
    except Exception as e:
        counts["missing page"] += 1
        broken.append((url, None, str(e), "missing page"))

print(f"Total crawled: {len(visited)}")
print(f"HTTP 200: {counts['ok']}")
print(f"Broken count: {counts['missing page'] + counts['stale redirect']}")
print()
print("Breakdown:")
for k, v in counts.items():
    if v > 0:
        print(f"  {k}: {v}")
print()
if broken:
    print("First 10 broken URLs:")
    for i, (url, status, final, cls) in enumerate(broken[:10], 1):
        if status is None:
            print(f"  {i}. {url}")
            print(f"     Classification: {cls} — Error: {final}")
        else:
            print(f"  {i}. {url}")
            print(f"     Status: {status} -> {final}")
            print(f"     Classification: {cls}")
else:
    print("No broken URLs found.")
