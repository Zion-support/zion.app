#!/usr/bin/env python3
"""Live site integrity crawl for ziontechgroup.com."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import sys
import time
from collections import deque

BASE = "https://ziontechgroup.com"
TIMEOUT = 20
MAX_PAGES = 800
DELAY = 0.3

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; SiteIntegrityCrawler/1.0; +ziontechgroup.com)"
})

seen = set()
queue = deque([BASE])
stats = {"total": 0, "ok": 0, "broken": 0}
broken_urls = []

def classify(url, resp):
    """Classify a broken URL."""
    status = getattr(resp, "status_code", None)
    final_url = getattr(resp, "url", url)
    reason = getattr(resp, "reason", "")

    if status is None:
        return "external_reference_error"

    # Redirect to external domain = stale redirect
    if status in (301, 302, 303, 307, 308):
        try:
            parsed_final = urlparse(final_url)
            parsed_orig = urlparse(url)
            if parsed_final.netloc != parsed_orig.netloc:
                return "stale_redirect"
            # Redirect to a non-200 or relative redirect that didn't resolve
            return "stale_redirect"
        except Exception:
            return "stale_redirect"

    if status == 404:
        return "missing_page"

    if status >= 400:
        return "missing_page"

    return "external_reference_error"

def is_internal(url):
    """Return True if url is on the same domain."""
    parsed = urlparse(url)
    return parsed.netloc in (BASE.split("//")[1], "localhost", "")

def extract_links(html, current_url):
    """Extract internal, non-fragment links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        # Skip anchors, javascript, mailto, tel, etc.
        if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        full = urljoin(current_url, href)
        full, _ = urldefrag(full)
        if is_internal(full) and full.startswith(BASE):
            links.add(full)
    return links

print(f"Starting crawl from {BASE}")
print(f"Max pages: {MAX_PAGES}, delay: {DELAY}s")
print("-" * 60)

while queue and stats["total"] < MAX_PAGES:
    url = queue.popleft()
    if url in seen:
        continue
    seen.add(url)
    stats["total"] += 1

    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        final_url = resp.url

        if resp.status_code == 200:
            stats["ok"] += 1
            # Only extract links from successful 200 responses
            if "text/html" in resp.headers.get("Content-Type", ""):
                for link in extract_links(resp.text, url):
                    if link not in seen:
                        queue.append(link)
        else:
            stats["broken"] += 1
            classification = classify(url, resp)
            broken_urls.append({
                "url": url,
                "status": resp.status_code,
                "final_url": final_url,
                "classification": classification,
            })
            # Still extract links from error pages if HTML
            if "text/html" in resp.headers.get("Content-Type", ""):
                for link in extract_links(resp.text, url):
                    if link not in seen:
                        queue.append(link)

        if stats["total"] % 50 == 0:
            print(f"  ... {stats['total']} pages crawled, {stats['ok']} ok, {stats['broken']} broken")

        time.sleep(DELAY)

    except requests.exceptions.Timeout:
        stats["broken"] += 1
        broken_urls.append({
            "url": url,
            "status": "TIMEOUT",
            "final_url": url,
            "classification": "external_reference_error",
        })
    except requests.exceptions.ConnectionError as e:
        stats["broken"] += 1
        broken_urls.append({
            "url": url,
            "status": f"CONNECTION_ERROR",
            "final_url": url,
            "classification": "external_reference_error",
        })
    except Exception as e:
        stats["broken"] += 1
        broken_urls.append({
            "url": url,
            "status": f"ERROR: {str(e)[:80]}",
            "final_url": url,
            "classification": "external_reference_error",
        })

print("-" * 60)
print("CRAWL COMPLETE")
print(f"  Total crawled:  {stats['total']}")
print(f"  HTTP 200:       {stats['ok']}")
print(f"  Broken:         {stats['broken']}")

if broken_urls:
    print(f"\nBROKEN URLS ({len(broken_urls)} total, showing first 10):")
    print("-" * 70)
    for i, b in enumerate(broken_urls[:10], 1):
        print(f"  {i:3d}. [{b['classification']:25s}] (HTTP {str(b['status']):8s}) {b['url']}")
        if b['final_url'] != b['url']:
            print(f"       -> redirected to: {b['final_url']}")

    # Summary by classification
    from collections import Counter
    cls_counts = Counter(b['classification'] for b in broken_urls)
    print(f"\nCLASSIFICATION SUMMARY:")
    for cls, count in sorted(cls_counts.items()):
        print(f"  {cls:30s}: {count}")

print()
