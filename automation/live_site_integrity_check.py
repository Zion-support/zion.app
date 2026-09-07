#!/usr/bin/env python3
"""Live site integrity check for https://ziontechgroup.com"""
import sys
import json
import re
import time
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ziontechgroup.com"
START_URL = BASE_URL + "/"
MAX_PAGES = 500
DELAY = 0.25
TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SiteIntegrityChecker/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

class Crawler:
    def __init__(self, base_url, start_url):
        self.base_netloc = urlparse(base_url).netloc
        self.visited = set()
        self.queue = [start_url]
        self.results = []  # list of (url, status_code, error_msg, is_external)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def is_internal(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.base_netloc or parsed.netloc == ""

    def normalize(self, url):
        """Normalize URL for dedup: strip fragments, trailing slash consistency."""
        parsed = urlparse(url)
        path = parsed.path
        if path and not path.endswith("/") and "." in path.split("/")[-1]:
            pass  # file-like; leave
        elif path and not path.endswith("/"):
            path += "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}{'?' + parsed.query if parsed.query else ''}"

    def check_page(self, url, is_external=False):
        if url in self.visited:
            return
        self.visited.add(url)
        try:
            resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            status = resp.status_code
            error = None
            # Check for redirect chains that don't end at 200
            if status in (301, 302, 307, 308):
                # Follow redirect manually to see final destination
                final = resp.headers.get("Location", "")
                if final:
                    final_full = urljoin(url, final) if not final.startswith("http") else final
                    final_resp = self.session.get(final_full, timeout=TIMEOUT, allow_redirects=True)
                    if final_resp.status_code == 200:
                        # It's a working redirect — classify accordingly
                        status = final_resp.status_code
                        error = f"redirect ({resp.status_code} -> 200)"
                    else:
                        error = f"broken redirect: {resp.status_code} -> {final_resp.status_code} [{final_full}]"
                else:
                    error = f"redirect without Location header ({resp.status_code})"
            self.results.append((url, status, error, is_external))
            return resp, status
        except requests.exceptions.ConnectionError as e:
            error = f"connection error: {e}"
            self.results.append((url, 0, error, is_external))
            return None, 0
        except requests.exceptions.Timeout:
            error = "timeout"
            self.results.append((url, 0, error, is_external))
            return None, 0
        except Exception as e:
            error = f"error: {e}"
            self.results.append((url, 0, error, is_external))
            return None, 0

    def extract_links(self, url, html):
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if isinstance(href, list):
                href = " ".join(str(h) for h in href)
            if not href:
                continue
            href = href.strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full = urljoin(url, href)
            if self.is_internal(full) and full not in self.visited:
                links.add(full)
        return list(links)

    def crawl(self):
        while self.queue and len(self.visited) < MAX_PAGES:
            url = self.queue.pop(0)
            if url in self.visited:
                continue
            print(f"[CRAWL] {len(self.visited)+1}: {url}", file=sys.stderr)
            resp, status = self.check_page(url)
            if resp is not None and status == 200:
                links = self.extract_links(url, resp.text)
                for link in links:
                    if link not in self.visited:
                        self.queue.append(link)
            time.sleep(DELAY)
        return self.results

    def report(self):
        total = len(self.results)
        ok = sum(1 for _, s, _, _ in self.results if s == 200)
        broken = [(url, s, err, ext) for url, s, err, ext in self.results if s != 200]
        broken_count = len(broken)

        print("\n" + "="*70)
        print("ZION TECH GROUP — LIVE SITE INTEGRITY CHECK")
        print(f"Target: {BASE_URL}")
        print(f"Total crawled: {total}")
        print(f"HTTP 200 OK:   {ok}")
        print(f"Broken:        {broken_count}")
        print("="*70)

        if broken_count == 0:
            print("\n✓ No broken URLs found. Site appears healthy.")
            return

        print(f"\nFirst 10 broken URLs (of {broken_count}):\n")

        for i, (url, status, error, is_external) in enumerate(broken[:10], 1):
            # Classify
            if is_external:
                classification = "external reference error"
            elif status in (301, 302, 307, 308):
                classification = "stale redirect"
            elif status == 404:
                classification = "missing page (404)"
            elif status == 0:
                if "connection" in (error or "").lower():
                    classification = "connection error"
                elif "timeout" in (error or "").lower():
                    classification = "timeout error"
                else:
                    classification = "unknown error"
            else:
                classification = f"HTTP {status}"

            print(f"  {i:2d}. [{classification}]")
            print(f"      URL:  {url}")
            print(f"      HTTP: {status}" + (f" ({error})" if error else ""))
            print()

        # Summary of classifications
        classifications = {}
        for url, status, error, ext in broken:
            if ext:
                c = "external reference error"
            elif status in (301, 302, 307, 308):
                c = "stale redirect"
            elif status == 404:
                c = "missing page (404)"
            elif status == 0:
                c = "connection/timeout error"
            else:
                c = f"HTTP {status}"
            classifications[c] = classifications.get(c, 0) + 1

        print("-"*70)
        print("BROKEN URL CLASSIFICATION SUMMARY:")
        for c, n in sorted(classifications.items()):
            print(f"  {c}: {n}")
        print("-"*70)

if __name__ == "__main__":
    crawler = Crawler(BASE_URL, START_URL)
    crawler.crawl()
    crawler.report()
