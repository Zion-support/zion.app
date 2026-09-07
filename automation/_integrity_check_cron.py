#!/usr/bin/env python3
"""
Live site integrity check for https://ziontechgroup.com.
BFS crawl, internal links only, requests+BeautifulSoup.
Reports: total crawled, HTTP 200 count, broken count, first 10 broken URLs,
with classification (stale redirect / missing page / external reference error).
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

BASE = "https://ziontechgroup.com"
MAX_PAGES = 400
DELAY = 0.25  # polite crawl delay
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "ZionIntegrityCheck/1.0 (+https://ziontechgroup.com)",
})

visited = set()
queue = [BASE]
broken = []
ok_count = 0
total = 0


def is_internal(url: str) -> bool:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    return netloc in ("ziontechgroup.com", "")


EXTENSIONS_TO_SKIP = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js",
    ".woff", ".woff2", ".ico", ".pdf",
)


def should_skip(url: str) -> bool:
    lower = url.lower()
    return any(lower.endswith(ext) for ext in EXTENSIONS_TO_SKIP)


def classify_broken(url: str, final_url: str, status_code: int | None, error: str | None) -> str:
    """Classify broken link: stale redirect, missing page, or external reference error."""
    if error is not None:
        return "external reference error"
    if urlparse(final_url).netloc != "ziontechgroup.com":
        return "external reference error"
    if status_code in (404, 410):
        return "missing page"
    if status_code is not None and status_code >= 400:
        return "missing page"
    if status_code in (301, 302, 307, 308):
        return "stale redirect"
    # Connection/unknown errors
    return "missing page"


# ---- Crawl ----
while queue and total < MAX_PAGES:
    url = queue.pop(0)
    if url in visited:
        continue
    if not is_internal(url):
        continue
    if should_skip(url):
        continue
    visited.add(url)
    total += 1

    try:
        resp = SESSION.get(url, timeout=20, allow_redirects=True)
        status = resp.status_code
        if status == 200:
            ok_count += 1
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if not href:
                    continue
                absolute = urljoin(url, str(href))
                if is_internal(absolute) and absolute not in visited:
                    queue.append(absolute)
        else:
            broken.append((url, resp.url, status, None))
        time.sleep(DELAY)
    except Exception as exc:
        broken.append((url, url, None, str(exc)))
        time.sleep(DELAY)

# ---- Report ----
print(f"Total crawled: {total}")
print(f"HTTP 200 count: {ok_count}")
print(f"Broken count: {len(broken)}")

if broken:
    print("\nFirst 10 broken URLs:")
    for idx, (url, final, status, err) in enumerate(broken[:10], start=1):
        classification = classify_broken(url, final, status, err)
        if err:
            detail = f"error: {err}"
        elif status:
            detail = f"status {status} → {final}"
        else:
            detail = "unknown"
        print(f"  [{idx}] {url}")
        print(f"      classification: {classification} | {detail}")
else:
    print("\nNo broken URLs found.")
