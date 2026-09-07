#!/usr/bin/env python3
"""
Live site integrity check for https://ziontechgroup.com
Crawls internal links with requests+BeautifulSoup, reports totals and broken URLs.
"""

import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

BASE_URL = "https://ziontechgroup.com"
MAX_PAGES = 500
DELAY = 0.15  # polite delay between requests

def is_internal(url: str) -> bool:
    """Return True if url belongs to ziontechgroup.com."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return host in ("ziontechgroup.com", "www.ziontechgroup.com", "")
    except Exception:
        return False

def classify_broken(url: str, status_code: int, final_url: str, history: list) -> str:
    """Classify a broken URL into one of three categories."""
    if status_code in (404, 410):
        return "missing page"
    if status_code in (401, 403, 500, 502, 503):
        return "server error"
    # Check redirect chain for stale redirects
    if history:
        last = history[-1]
        if last.status_code in (301, 302, 307, 308):
            return "stale redirect"
    # If final URL differs from requested and is external
    if final_url != url and not is_internal(final_url):
        return "external reference error"
    if status_code >= 400:
        return "missing page"
    return "unknown"

def crawl():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; SiteIntegrityBot/1.0)"
    })

    visited = set()
    queue = deque([BASE_URL])
    results = {
        "total": 0,
        "ok": 0,
        "broken": 0,
        "broken_list": [],
        "errors": [],
    }

    while queue and results["total"] < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        results["total"] += 1

        try:
            resp = session.get(url, timeout=15, allow_redirects=True)
            final_url = resp.url
            status = resp.status_code

            if status == 200:
                results["ok"] += 1
                # Extract internal links
                if "text/html" in resp.headers.get("content-type", ""):
                    try:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = str(a["href"]).strip()
                            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                                continue
                            full_url = urljoin(url, href)
                            parsed = urlparse(full_url)
                            clean = parsed._replace(fragment="").geturl()
                            if is_internal(clean) and clean not in visited:
                                queue.append(clean)
                    except Exception:
                        pass
            else:
                results["broken"] += 1
                classification = classify_broken(url, status, final_url, resp.history)
                results["broken_list"].append({
                    "url": url,
                    "status": status,
                    "final_url": final_url,
                    "classification": classification,
                })
                # Still extract links from broken pages for completeness
                if "text/html" in resp.headers.get("content-type", ""):
                    try:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"].strip()
                            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                                continue
                            full_url = urljoin(url, href)
                            parsed = urlparse(full_url)
                            clean = parsed._replace(fragment="").geturl()
                            if is_internal(clean) and clean not in visited:
                                queue.append(clean)
                    except Exception:
                        pass

        except requests.exceptions.Timeout:
            results["errors"].append({"url": url, "error": "timeout"})
            results["broken"] += 1
            results["broken_list"].append({
                "url": url,
                "status": "timeout",
                "final_url": "",
                "classification": "external reference error",
            })
        except requests.exceptions.ConnectionError as e:
            results["errors"].append({"url": url, "error": f"connection: {e}"})
            results["broken"] += 1
            results["broken_list"].append({
                "url": url,
                "status": "connection_error",
                "final_url": "",
                "classification": "external reference error",
            })
        except Exception as e:
            results["errors"].append({"url": url, "error": str(e)})
            results["broken"] += 1
            results["broken_list"].append({
                "url": url,
                "status": "error",
                "final_url": "",
                "classification": "unknown",
            })

        time.sleep(DELAY)

    return results

def main():
    print(f"Starting crawl of {BASE_URL}...")
    print(f"Max pages: {MAX_PAGES}, delay: {DELAY}s")
    print("-" * 60)

    start = time.time()
    results = crawl()
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"CRAWL COMPLETE — {elapsed:.1f}s elapsed")
    print(f"{'=' * 60}")
    print(f"Total crawled:   {results['total']}")
    print(f"HTTP 200:        {results['ok']}")
    print(f"Broken:          {results['broken']}")
    print(f"Errors:          {len(results['errors'])}")
    print(f"{'=' * 60}")

    if results["broken"] > 0:
        print(f"\nFirst 10 broken URLs:")
        print("-" * 60)
        for i, item in enumerate(results["broken_list"][:10], 1):
            print(f"\n[{i}] {item['url']}")
            print(f"    Status:    {item['status']}")
            print(f"    Final URL: {item['final_url']}")
            print(f"    Class:     {item['classification']}")
    else:
        print("\nNo broken URLs found. Site is clean.")

    if results["errors"]:
        print(f"\nRequest errors ({len(results['errors'])}):")
        for e in results["errors"][:5]:
            print(f"  - {e['url']}: {e['error']}")

    # Summary by classification
    if results["broken"] > 0:
        from collections import Counter
        classes = Counter(item["classification"] for item in results["broken_list"])
        print(f"\nBreakdown by classification:")
        for cls, count in classes.most_common():
            print(f"  {cls}: {count}")

if __name__ == "__main__":
    main()
