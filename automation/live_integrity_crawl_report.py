#!/usr/bin/env python3
"""Live site integrity crawl for https://ziontechgroup.com.
BFS, internal links only. Reports counts + first 10 broken URLs.
Uses venv: /Users/miami2/zion.app/automation/.crawl-venv
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import time

BASE = "https://ziontechgroup.com"
MAX_PAGES = 500
DELAY = 0.15  # seconds between requests

def is_internal(url: str) -> bool:
    p = urlparse(url)
    base_p = urlparse(BASE)
    return (p.scheme in ("", "http", "https")
            and p.netloc in ("", base_p.netloc)
            and not p.fragment)

def classify_broken(url: str, status: int, final_url: str, exception: str = "") -> str:
    """Return one of: stale redirect, missing page, external reference error, or unknown."""
    if exception:
        # Connection/timeout errors
        if "timeout" in exception.lower() or "connection" in exception.lower():
            return "external reference error"
        return "unknown"
    if status in (404, 410):
        return "missing page"
    if status in (301, 302, 307, 308):
        # A redirect that didn't end at 200
        if final_url != url and not final_url.startswith(BASE):
            return "stale redirect"
        return "stale redirect"
    if status >= 500:
        return "missing page"
    return "unknown"

def crawl():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ZionIntegrityCrawler/1.0 (+https://ziontechgroup.com)"
    })

    visited = set()
    queue = [BASE]
    results = []  # (url, status, final_url, exception_or_None)
    broken = []

    while queue and len(visited) < MAX_PAGES:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            final_url = resp.url
            status = resp.status_code
            exception = None
        except requests.exceptions.Timeout as e:
            status = 0
            final_url = url
            exception = f"timeout: {e}"
        except requests.exceptions.ConnectionError as e:
            status = 0
            final_url = url
            exception = f"connection: {e}"
        except Exception as e:
            status = 0
            final_url = url
            exception = str(e)

        results.append((url, status, final_url, exception))

        if status != 200 or (exception and "timeout" not in exception and "connection" not in exception):
            # Only count truly broken — exclude connection errors on first hop for external-like
            is_broken = False
            if exception:
                is_broken = True
            elif status != 200:
                is_broken = True
            if is_broken:
                classification = classify_broken(url, status, final_url, exception or "")
                broken.append({
                    "url": url,
                    "status": status,
                    "final_url": final_url,
                    "exception": exception,
                    "classification": classification,
                })

        # Only extract links from successful HTML responses
        if status == 200 and exception is None:
            try:
                soup = BeautifulSoup(resp.content, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    absolute = urljoin(url, href)
                    if is_internal(absolute) and absolute not in visited:
                        # Normalize: strip fragment, trailing slash consistency
                        parsed = urlparse(absolute)
                        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            clean += f"?{parsed.query}"
                        if clean not in visited:
                            queue.append(clean)
            except Exception:
                pass

        time.sleep(DELAY)

    return results, broken

if __name__ == "__main__":
    sys.stdout.write("Starting live crawl of {} ...\n".format(BASE))
    sys.stdout.flush()
    results, broken = crawl()

    total = len(results)
    ok_200 = sum(1 for _, s, _, _ in results if s == 200 and _ is None)
    broken_count = len(broken)

    print("=" * 60)
    print("ZION TECH GROUP — LIVE SITE INTEGRITY REPORT")
    print("=" * 60)
    print(f"Target:          {BASE}")
    print(f"Total crawled:   {total}")
    print(f"HTTP 200 count:  {ok_200}")
    print(f"Broken count:    {broken_count}")
    print("=" * 60)

    if broken_count > 0:
        print("\nFIRST 10 BROKEN URLS:")
        print("-" * 60)
        for i, b in enumerate(broken[:10], 1):
            exc = ""
            if b["exception"]:
                exc = f" | error: {b['exception']}"
            print(f"{i:2d}. [{b['status']}] {b['url']}{exc}")
            print(f"     final: {b['final_url']}")
            print(f"     class: {b['classification']}")
            print()
    else:
        print("\nNo broken URLs found.")

    # Summary by classification
    if broken_count > 0:
        from collections import Counter
        cls_counts = Counter(b["classification"] for b in broken)
        print("-" * 60)
        print("BROKEN CLASSIFICATION SUMMARY:")
        for cls, cnt in cls_counts.most_common():
            print(f"  {cls}: {cnt}")
