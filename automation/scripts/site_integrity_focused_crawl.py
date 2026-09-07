#!/usr/bin/env python3
"""Focused BFS site integrity crawl for https://ziontechgroup.com.
Follows internal links only, classifies broken URLs, writes a JSON report."""

import json, os, re, sys, time
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ziontechgroup.com"
SITE_DOMAIN = "ziontechgroup.com"
MAX_PAGES = 600
OUT_PATH = "/Users/miami2/zion.app/automation/reports/site-integrity-latest.json"

def strip_fragment(url: str) -> str:
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

def normalize(url: str) -> str:
    url = strip_fragment(url)
    # enforce trailing slash on paths that look like directories
    ps = urlparse(url)
    if ps.path and not ps.path.endswith("/") and not "." in os.path.basename(ps.path):
        # only for directory-looking paths without file extension
        if not re.search(r"\.[a-zA-Z0-9]+$", ps.path):
            url = urlunparse(ps._replace(path=ps.path + "/"))
    return url

def is_internal(url: str) -> bool:
    p = urlparse(url)
    return p.netloc in (SITE_DOMAIN, f"www.{SITE_DOMAIN}", "")

def classify(url, status_code, history, exception=None):
    if exception:
        return "missing page"
    if status_code == 200:
        return None
    # follow redirect chain to final
    final = None
    if history:
        final_url = history[-1].url
        final_code = history[-1].status_code
        # check if final is external
        if urlparse(final_url).netloc and urlparse(final_url).netloc != SITE_DOMAIN and not urlparse(final_url).netloc.startswith("www."+SITE_DOMAIN):
            return "stale redirect"
        if final_code != 200:
            # 3xx that didn't resolve to 200, or 4xx/5xx chain
            return "stale redirect" if 300 <= status_code < 400 else "missing page"
    if 300 <= status_code < 400:
        return "stale redirect"
    return "missing page"

def crawl():
    visited = set()
    queue = [BASE_URL]
    crawled = []
    broken = []
    redirects = []
    start = time.time()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ZionIntegrityCrawl/1.0)"})
    while queue and len(crawled) < MAX_PAGES:
        url = queue.pop(0)
        url = normalize(url)
        if url in visited:
            continue
        visited.add(url)
        try:
            r = session.get(url, timeout=15, allow_redirects=True)
            elapsed = time.time() - start
            entry = {
                "url": url,
                "status": r.status_code,
                "redirect_chain": [h.url for h in r.history],
                "elapsed_s": round(elapsed, 2)
            }
            crawled.append(entry)
            if r.status_code == 200:
                # extract links
                try:
                    soup = BeautifulSoup(r.text, "html.parser")
                except Exception:
                    soup = None
                if soup:
                    for tag in soup.find_all("a", href=True):
                        href = tag["href"].strip()
                        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                            continue
                        full = urljoin(url, href)
                        if is_internal(full) and full not in visited:
                            queue.append(full)
            else:
                cls = classify(url, r.status_code, r.history)
                if cls:
                    broken.append({"url": url, "status": r.status_code, "classification": cls, "chain": [h.url for h in r.history]})
                if r.history:
                    redirects.append({"from": url, "to": r.url, "status": r.status_code})
        except requests.exceptions.RequestException as e:
            broken.append({"url": url, "status": "exception", "classification": "missing page", "error": str(e)[:200]})
            crawled.append({"url": url, "status": "exception", "elapsed_s": round(time.time()-start, 2)})
        except Exception as e:
            broken.append({"url": url, "status": "error", "classification": "missing page", "error": str(e)[:200]})
            crawled.append({"url": url, "status": "error", "elapsed_s": round(time.time()-start, 2)})
    summary = {
        "total_crawled": len(crawled),
        "http_200": sum(1 for c in crawled if c["status"] == 200),
        "broken_count": len(broken),
        "redirect_count": len(redirects),
        "elapsed_s": round(time.time()-start, 2)
    }
    report = {"summary": summary, "broken": broken[:200], "redirects": redirects[:100]}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"SUMMARY total_crawled={summary['total_crawled']} http_200={summary['http_200']} broken={summary['broken_count']} redirects={summary['redirect_count']} time={summary['elapsed_s']}s")
    print(f"Report: {OUT_PATH}")

if __name__ == "__main__":
    crawl()
