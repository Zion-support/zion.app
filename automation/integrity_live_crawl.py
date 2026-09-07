#!/usr/bin/env python3
"""
Live site integrity crawl for https://ziontechgroup.com
BFS from homepage, internal links only, reports status counts + broken URLs.
"""
import sys, re, time
from urllib.parse import urljoin, urlparse
from collections import deque
import requests
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
MAX_PAGES = 500
TIMEOUT = 15
DELAY = 0.1  # polite crawl delay

seen = set()
broken = []  # (url, status_code, final_url, reason)
ok_count = 0
redirect_count = 0
error_count = 0
queue = deque([BASE])

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; ZionIntegrityBot/1.0; +https://ziontechgroup.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def is_internal(url):
    parsed = urlparse(url)
    return parsed.netloc == urlparse(BASE).netloc or parsed.netloc == ""

def classify(url, status_code, final_url, resp):
    """Classify a broken link."""
    if status_code >= 500:
        return "server error"
    if status_code in (408, 429, 503):
        return "server error"
    # Check if it redirected somewhere unexpected
    if final_url != url and status_code in (301, 302, 307, 308):
        # Followed redirect but still not 200
        return "stale redirect"
    if status_code == 404:
        # Check if it looks like an external URL masquerading as internal
        parsed = urlparse(final_url if final_url else url)
        if parsed.netloc and parsed.netloc != urlparse(BASE).netloc:
            return "external reference error"
        return "missing page"
    if 400 <= status_code < 500:
        return "client error"
    return "unknown"

print(f"Starting crawl of {BASE} (max {MAX_PAGES} pages, {TIMEOUT}s timeout)", flush=True)

while queue and len(seen) < MAX_PAGES:
    url = queue.popleft()
    if url in seen:
        continue
    seen.add(url)
    
    try:
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True, headers=headers)
        status_code = resp.status_code
        final_url = resp.url
        
        if status_code == 200:
            ok_count += 1
        elif 300 <= status_code < 400:
            redirect_count += 1
            # Still extract links from redirect pages if we got HTML
            if "text/html" in resp.headers.get("content-type", ""):
                pass  # fall through to link extraction
            else:
                continue
        else:
            error_count += 1
            reason = classify(url, status_code, final_url, resp)
            broken.append((url, status_code, final_url, reason))
        
        # Extract links only from HTML responses
        ct = resp.headers.get("content-type", "")
        if "text/html" not in ct:
            continue
        
        soup = BeautifulSoup(resp.content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            # Skip anchors, javascript, mailto, tel
            if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                continue
            abs_url = urljoin(url, href)
            # Normalize: strip fragment
            abs_url = abs_url.split("#")[0]
            if not is_internal(abs_url):
                continue
            # Only http/https
            if not abs_url.startswith(("http://", "https://")):
                continue
            if abs_url not in seen:
                queue.append(abs_url)
        
        if len(seen) % 50 == 0:
            print(f"  ... {len(seen)} pages crawled, {len(broken)} broken so far", flush=True)
    
    except requests.exceptions.Timeout:
        error_count += 1
        broken.append((url, "TIMEOUT", "", "timeout"))
    except requests.exceptions.ConnectionError as e:
        error_count += 1
        broken.append((url, "CONN_ERR", "", f"connection error: {e}"))
    except Exception as e:
        error_count += 1
        broken.append((url, "ERR", "", f"{type(e).__name__}: {e}"))
    
    time.sleep(DELAY)

print(f"\n{'='*60}", flush=True)
print(f"CRAWL COMPLETE — {BASE}", flush=True)
print(f"{'='*60}", flush=True)
print(f"Total pages crawled : {len(seen)}", flush=True)
print(f"HTTP 200            : {ok_count}", flush=True)
print(f"Redirects (3xx)    : {redirect_count}", flush=True)
print(f"Broken / errors     : {len(broken)}", flush=True)
print(f"{'='*60}", flush=True)

if broken:
    print(f"\nFIRST {min(10, len(broken))} BROKEN URLS:", flush=True)
    print(f"{'='*60}", flush=True)
    for i, (url, status, final, reason) in enumerate(broken[:10], 1):
        print(f"{i:2d}. [{status}] {reason}", flush=True)
        print(f"    URL   : {url}", flush=True)
        if final and final != url:
            print(f"    Final : {final}", flush=True)
    if len(broken) > 10:
        print(f"\n... and {len(broken) - 10} more broken URLs", flush=True)
    
    # Classification summary
    from collections import Counter
    reasons = Counter(r for _, _, _, r in broken)
    print(f"\nCLASSIFICATION SUMMARY:", flush=True)
    for reason, count in reasons.most_common():
        print(f"  {reason}: {count}", flush=True)
else:
    print("No broken URLs found — site is clean.", flush=True)
