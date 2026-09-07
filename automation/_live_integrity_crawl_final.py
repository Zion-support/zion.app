"""
Live site integrity check for https://ziontechgroup.com
- BFS crawl, internal links only
- reports total crawled, HTTP 200 count, broken count, first 10 broken URLs
- classifies broken as stale redirect / missing page / external reference error
"""
import sys, re, time
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
# normalize: strip trailing slash for base comparison
BASE_NETLOC = urlparse(BASE).netloc.lower()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)

crawled = set()
queue = [BASE]
broken = []  # list of dicts: url, status_code, reason, classification

MAX_PAGES = 500
TIMEOUT = 15

def is_internal(url):
    parsed = urlparse(url)
    # only same netloc, scheme http/https
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc.lower() != BASE_NETLOC:
        return False
    # skip fragments, empty paths
    return True

def classify(url, status_code, reason):
    """Classify broken into: stale redirect, missing page, external reference error."""
    # stale redirect: we got a redirect but final not 200
    if 300 <= status_code < 400:
        return "stale redirect"
    if status_code == 404 or status_code == 410:
        return "missing page"
    if 400 <= status_code < 500:
        return "missing page"  # client error generally
    if 500 <= status_code < 600:
        return "missing page"  # server error, page effectively missing
    # connection/timeout/etc
    if isinstance(reason, Exception):
        # If it's an external reference error (link to external but somehow we followed)
        # Actually if we only crawl internal, anything here is internal broken.
        # External reference error is when an internal page links to an external that is broken.
        # We won't follow externals, so this won't happen. But we can classify if domain mismatch.
        return "missing page"
    return "missing page"

def final_status(resp):
    """Return the final status code after following redirects manually to capture stale."""
    # requests follows redirects by default and gives the final 200.
    # To detect stale redirects we need to look at history.
    if resp.history:
        # We got redirected; final is 200 normally, but check if any intermediate is stale.
        # If final is 200, it's fine.
        return resp.status_code
    return resp.status_code

idx = 0
while queue and idx < MAX_PAGES:
    url = queue.pop(0)
    if url in crawled:
        continue
    # skip non-http(s) and non-internal
    if not is_internal(url):
        continue
    crawled.add(url)
    idx += 1
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        status = resp.status_code
        if status == 200:
            # extract links
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                # resolve
                full = urljoin(url, href)
                # drop fragments
                frag_idx = full.find("#")
                if frag_idx != -1:
                    full = full[:frag_idx]
                if is_internal(full) and full not in crawled and full not in queue:
                    queue.append(full)
        else:
            # non-200 internal response
            reason = None
            classification = classify(url, status, None)
            broken.append({
                "url": url,
                "status_code": status,
                "reason": reason,
                "classification": classification,
            })
            # still try extract links from body even if error page? skip for errors.
    except requests.exceptions.TooManyRedirects:
        broken.append({
            "url": url,
            "status_code": None,
            "reason": "Too many redirects",
            "classification": "stale redirect",
        })
    except requests.exceptions.RequestException as e:
        broken.append({
            "url": url,
            "status_code": None,
            "reason": str(e),
            "classification": "missing page",
        })
    time.sleep(0.1)  # be gentle

# also detect external references that are broken from internal pages? 
# The task says classify each broken as stale redirect, missing page, or external reference error.
# External reference errors would be internal pages linking to external URLs that are broken.
# We'll do a second pass: for each 200 page, check all external links and test them (head only, quick).
print(f"CRAWL COMPLETE: crawled={len(crawled)} broken_internal={len(broken)}")

# External reference check: sample of external links from crawled pages
external_broken = []
visited_external = set()
# We'll only check a bounded set of external links to keep runtime sane.
MAX_EXT_CHECKS = 200
ext_checked = 0
for url in list(crawled):
    if ext_checked >= MAX_EXT_CHECKS:
        break
    try:
        resp = session.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            full = urljoin(url, href)
            parsed = urlparse(full)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc.lower() == BASE_NETLOC:
                continue
            # external link
            if full in visited_external:
                continue
            visited_external.add(full)
            ext_checked += 1
            try:
                h = session.head(full, timeout=TIMEOUT, allow_redirects=True)
                if h.status_code >= 400:
                    external_broken.append({
                        "source_page": url,
                        "external_url": full,
                        "status_code": h.status_code,
                        "classification": "external reference error",
                    })
            except Exception:
                # try GET if HEAD fails
                try:
                    g = session.get(full, timeout=TIMEOUT, allow_redirects=True)
                    if g.status_code >= 400:
                        external_broken.append({
                            "source_page": url,
                            "external_url": full,
                            "status_code": g.status_code,
                            "classification": "external reference error",
                        })
                except Exception:
                    external_broken.append({
                        "source_page": url,
                        "external_url": full,
                        "status_code": None,
                        "classification": "external reference error",
                    })
    except Exception:
        pass

# Combine: internal broken + external broken
all_broken = broken + external_broken

print(f"\n=== ZION TEC GROUP SITE INTEGRITY REPORT ===")
print(f"Base URL: {BASE}")
print(f"Total crawled (internal pages): {len(crawled)}")
http200 = sum(1 for u in crawled if u not in [b['url'] for b in broken])
print(f"HTTP 200 count (internal): {len(crawled) - len(broken)}")
print(f"Broken count (internal + external): {len(all_broken)}")
print(f"  - internal broken: {len(broken)}")
print(f"  - external reference errors: {len(external_broken)}")
print()
print("First 10 broken URLs:")
for i, b in enumerate(all_broken[:10]):
    src = b.get("source_page", "")
    print(f"  {i+1}. {b['url']}  [status={b['status_code']}, class={b['classification']}" + (f", source={src}]" if src else "]"))

if len(all_broken) > 10:
    print(f"  ... and {len(all_broken) - 10} more")

print()
print("Breakdown by classification:")
from collections import Counter
cnt = Counter(b['classification'] for b in all_broken)
for cls, n in cnt.most_common():
    print(f"  {cls}: {n}")
