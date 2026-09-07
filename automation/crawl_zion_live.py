#!/usr/bin/env python3
"""Live site integrity crawl for https://ziontechgroup.com — internal links only."""
import sys
import time
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque, Counter

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ziontechgroup.com"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) ZionIntegrityCrawl/1.0"
REQUEST_TIMEOUT = 15
DELAY = 0.25  # polite delay between requests

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def strip_fragment(url: str) -> str:
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))


def is_internal(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in ("", "ziontechgroup.com", "www.ziontechgroup.com")


def extract_links(html: str, base: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all(["a", "link", "img", "script"]):
        attr = "src" if tag.name in ("img", "script") else "href"
        href = tag.get(attr)
        if not href:
            continue
        # skip anchors, javascript, mailto, tel
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = strip_fragment(urljoin(base, href))
        if is_internal(full):
            links.append(full)
    return links


def classify(url: str, status: int, redirect_to: str = None, exception: str = None) -> str:
    if exception:
        return "missing page"
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        if redirect_to and not is_internal(redirect_to):
            return "stale redirect"
        return "stale redirect"
    # 4xx / 5xx
    return "missing page"


def probe(url: str) -> dict:
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        final_url = resp.url
        status = resp.status_code
        if not is_internal(final_url):
            return {
                "url": url,
                "status": status,
                "final_url": final_url,
                "classification": "stale redirect" if 300 <= status < 400 else "external reference error",
                "exception": None,
            }
        if resp.history:
            for hop in resp.history:
                if not is_internal(hop.url):
                    return {
                        "url": url,
                        "status": status,
                        "final_url": final_url,
                        "classification": "stale redirect",
                        "exception": None,
                    }
        return {
            "url": url,
            "status": status,
            "final_url": final_url,
            "classification": classify(url, status, redirect_to=final_url),
            "exception": None,
        }
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "status": None,
            "final_url": None,
            "classification": "missing page",
            "exception": str(e)[:120],
        }


def main():
    visited = set()
    queue = deque([BASE_URL])
    results = []

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        result = probe(url)
        results.append(result)
        print(f"[{len(visited):5}] {result['classification']:25} {url}", flush=True)

        if result["classification"] == "ok":
            try:
                resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                links = extract_links(resp.text, url)
                for link in links:
                    if link not in visited:
                        queue.append(link)
            except Exception:
                pass

        time.sleep(DELAY)

    total = len(results)
    ok_count = sum(1 for r in results if r["classification"] == "ok")
    broken = [r for r in results if r["classification"] != "ok"]
    broken_count = len(broken)

    print("\n=== SUMMARY ===", flush=True)
    print(f"total_crawled: {total}", flush=True)
    print(f"http_200_count: {ok_count}", flush=True)
    print(f"broken_count: {broken_count}", flush=True)

    if broken_count > 0:
        print("\n=== FIRST 10 BROKEN URLs ===", flush=True)
        for r in broken[:10]:
            cls = r["classification"]
            url = r["url"]
            extra = ""
            if r["status"]:
                extra += f" [HTTP {r['status']}]"
            if r["final_url"] and r["final_url"] != url:
                extra += f" -> {r['final_url']}"
            if r["exception"]:
                extra += f" [{r['exception']}]"
            print(f"{cls:25} {url}{extra}", flush=True)

        print("\n=== BROKEN CLASSIFICATION BREAKDOWN ===", flush=True)
        c = Counter(r["classification"] for r in broken)
        for k, v in c.most_common():
            print(f"{k}: {v}", flush=True)


if __name__ == "__main__":
    main()
