#!/usr/bin/env python3
"""
Live site integrity check for https://ziontechgroup.com
Crawls internal links with requests+BeautifulSoup only.
Reports: total crawled, HTTP 200 count, broken count, first 10 broken URLs
with classification (stale redirect / missing page / external reference error).
Read-only — no files modified.
"""

import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, Counter

BASE_URL = "https://ziontechgroup.com"
MAX_PAGES = 500
DELAY = 0.2  # polite delay between requests

INTERNAL_HOSTS = {"ziontechgroup.com", "www.ziontechgroup.com", ""}


def is_internal(url: str) -> bool:
    """Return True if url belongs to ziontechgroup.com (no scheme/host = relative)."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return host in INTERNAL_HOSTS
    except Exception:
        return False


def extract_links(html: str, base: str) -> list[str]:
    """Extract internal, visited-clean links from HTML."""
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if href.startswith(("javascript:", "mailto:", "tel:")):
                continue
            if href.startswith("#"):
                # resolve against base
                href = urljoin(base, href)
            full = urljoin(base, href)
            parsed = urlparse(full)
            clean = parsed._replace(fragment="", query="").geturl()
            if is_internal(clean):
                links.append(clean)
    except Exception:
        pass
    return links


def classify_broken(url: str, status: int, final_url: str, history: list) -> str:
    """Classify a broken URL into: stale redirect, missing page, external reference error."""
    if status in (404, 410):
        return "missing page"
    if status in (401, 403, 500, 502, 503, 504):
        return "server error"
    # Stale redirect: ended on a redirect response
    if history:
        last = history[-1]
        if last.status_code in (301, 302, 307, 308):
            return "stale redirect"
    # External reference error: final URL is external
    if final_url and final_url != url and not is_internal(final_url):
        return "external reference error"
    # Fallback
    if status >= 400:
        return "missing page"
    return "unknown"


def crawl() -> dict:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; SiteIntegrityBot/1.0; +https://ziontechgroup.com)"
    })

    visited: set[str] = set()
    queue: deque[str] = deque([BASE_URL])
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
            history = resp.history

            if status == 200 and "text/html" in resp.headers.get("content-type", ""):
                results["ok"] += 1
                for link in extract_links(resp.text, url):
                    if link not in visited:
                        queue.append(link)
            else:
                # Non-200 or non-HTML: record as broken
                results["broken"] += 1
                classification = classify_broken(url, status, final_url, history)
                results["broken_list"].append({
                    "url": url,
                    "status": status,
                    "final_url": final_url,
                    "classification": classification,
                })
                # Still try to extract links from broken HTML pages
                if "text/html" in resp.headers.get("content-type", ""):
                    for link in extract_links(resp.text, url):
                        if link not in visited:
                            queue.append(link)

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
    print(f"Starting crawl of {BASE_URL} ...")
    print(f"Max pages: {MAX_PAGES} · delay: {DELAY}s")
    print("-" * 60)

    start = time.time()
    results = crawl()
    elapsed = time.time() - start

    print()
    print("=" * 60)
    print(f"CRAWL COMPLETE — {elapsed:.1f}s elapsed")
    print("=" * 60)
    print(f"Total crawled:   {results['total']}")
    print(f"HTTP 200:        {results['ok']}")
    print(f"Broken:          {results['broken']}")
    print(f"Request errors:  {len(results['errors'])}")
    print("=" * 60)

    if results["broken"] > 0:
        print()
        print("First 10 broken URLs:")
        print("-" * 60)
        for i, item in enumerate(results["broken_list"][:10], 1):
            print(f"\n[{i}] {item['url']}")
            print(f"    Status:    {item['status']}")
            print(f"    Final URL: {item['final_url']}")
            print(f"    Class:     {item['classification']}")

        print()
        print("Breakdown by classification:")
        classes = Counter(item["classification"] for item in results["broken_list"])
        for cls, count in classes.most_common():
            print(f"  {cls}: {count}")
    else:
        print()
        print("No broken URLs found. Site is clean.")

    if results["errors"]:
        print()
        print(f"Request errors ({len(results['errors'])}):")
        for e in results["errors"][:5]:
            print(f"  - {e['url']}: {e['error']}")

    # Exit with non-zero if broken found (for cron alerting)
    if results["broken"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
