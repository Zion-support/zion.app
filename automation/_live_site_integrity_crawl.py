"""
Site integrity crawl for https://ziontechgroup.com
Uses requests + BeautifulSoup from .crawl-venv.
Follows internal links only. Reports: total crawled, HTTP 200 count,
broken count, first 10 broken URLs with classification.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import sys

BASE_URL = "https://ziontechgroup.com"
DOMAIN = urlparse(BASE_URL).netloc
MAX_PAGES = 300
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

visited = set()
to_visit = [BASE_URL]
broken = []
ok_200 = 0
broken_count = 0
total_crawled = 0

def classify(url, status_code, final_url, history):
    """Classify a broken URL."""
    if status_code in (404, 403, 401, 500, 502, 503):
        return "missing page"
    if status_code in (301, 302, 307, 308):
        # Check if redirect leads somewhere valid
        if history:
            last = history[-1]
            if last.status_code == 404:
                return "stale redirect"
            if last.status_code == 200:
                return "stale redirect (redirects to valid 200, but original not 200)"
        return "stale redirect"
    if status_code >= 400:
        return "missing page"
    # Connection errors, timeouts, etc.
    return "external reference error"


print(f"Starting crawl of {BASE_URL} ...")
print(f"Max pages: {MAX_PAGES}, Timeout: {TIMEOUT}s")
print("-" * 60)

while to_visit and total_crawled < MAX_PAGES:
    url = to_visit.pop(0)
    if url in visited:
        continue
    visited.add(url)
    
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        total_crawled += 1
        
        if resp.status_code == 200:
            ok_200 += 1
            # Extract links
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = str(a["href"]).strip()
                    # Skip anchors, javascript, mailto, tel, etc.
                    if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                        continue
                    full_url = urljoin(resp.url, href)
                    parsed = urlparse(full_url)
                    # Internal links only
                    if parsed.netloc in (DOMAIN, ""):
                        clean = parsed._replace(fragment="").geturl()
                        if clean not in visited and clean not in to_visit:
                            to_visit.append(clean)
            except Exception as e:
                pass  # Don't let parsing errors stop the crawl
            
            if total_crawled % 25 == 0:
                print(f"  [progress] crawled {total_crawled} pages, 200s: {ok_200}, broken: {broken_count}, queue: {len(to_visit)}")
        
        else:
            broken_count += 1
            classification = classify(url, resp.status_code, resp.url, resp.history)
            broken.append({
                "url": url,
                "status": resp.status_code,
                "final_url": resp.url,
                "classification": classification,
                "redirect_chain": [f"{h.status_code} {h.url}" for h in resp.history] + [f"{resp.status_code} {resp.url}"]
            })
            if len(broken) <= 10:
                chain_str = " → ".join(broken[-1]["redirect_chain"])
                print(f"  BROKEN [{classification}]: {url} → {resp.status_code} ({chain_str})")
        
        time.sleep(0.05)  # small delay to be polite
        
    except requests.exceptions.Timeout:
        broken_count += 1
        broken.append({"url": url, "status": "TIMEOUT", "final_url": "", "classification": "external reference error", "redirect_chain": []})
        if len(broken) <= 10:
            print(f"  BROKEN [external reference error]: {url} → TIMEOUT")
    except requests.exceptions.ConnectionError as e:
        broken_count += 1
        broken.append({"url": url, "status": "CONN_ERR", "final_url": "", "classification": "external reference error", "redirect_chain": []})
        if len(broken) <= 10:
            print(f"  BROKEN [external reference error]: {url} → CONNECTION ERROR")
    except Exception as e:
        broken_count += 1
        broken.append({"url": url, "status": "ERR", "final_url": "", "classification": "external reference error", "redirect_chain": []})
        if len(broken) <= 10:
            print(f"  BROKEN [external reference error]: {url} → {type(e).__name__}: {e}")

print("-" * 60)
print(f"\n✅ SITE INTEGRITY REPORT for {BASE_URL}")
print(f"   Crawl date:     {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Total crawled:  {total_crawled}")
print(f"   HTTP 200:       {ok_200}")
print(f"   Broken count:   {broken_count}")
print()

if broken_count == 0:
    print("   ✅ No broken URLs found!")
else:
    print(f"   ❌ Found {broken_count} broken URLs")
    print()
    print("   First 10 broken URLs (classification):")
    print("   " + "-" * 70)
    
    # Deduplicate by URL
    seen = set()
    unique_broken = []
    for b in broken:
        key = b["url"]
        if key not in seen:
            seen.add(key)
            unique_broken.append(b)
    
    for i, b in enumerate(unique_broken[:10], 1):
        chain = " → ".join(b["redirect_chain"]) if b["redirect_chain"] else "N/A"
        print(f"   {i:2d}. [{b['classification']}] {b['status']}")
        print(f"       URL:    {b['url']}")
        print(f"       Chain:  {chain}")
        print()

    # Classification summary
    from collections import Counter
    classes = Counter(b["classification"] for b in unique_broken)
    print("   Classification summary:")
    for cls, cnt in classes.most_common():
        print(f"     - {cls}: {cnt}")
