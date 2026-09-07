#!/usr/bin/env python3
"""Live site integrity crawl for https://ziontechgroup.com"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

BASE = "https://ziontechgroup.com"
MAX_PAGES = 300
DELAY = 0.25

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ZionSiteIntegrityCrawl/1.0)"
})

def is_internal(url):
    """Only follow links within ziontechgroup.com"""
    parsed = urlparse(url)
    return parsed.netloc == "ziontechgroup.com" or parsed.netloc == ""

def classify_broken(status_code, url, history):
    """Classify why a URL might be broken."""
    if status_code == 0:
        return "external_reference_error"
    if status_code in (404, 410):
        # Check if it redirects to something that 404s
        if history:
            final = history[-1]
            if final.status_code == 404:
                return "missing_page"
        return "missing_page"
    if status_code in (301, 302, 307, 308):
        # Redirect but final destination may be bad
        return "stale_redirect"
    if status_code >= 500:
        return "server_error"
    return "unknown"

def crawl():
    visited = set()
    to_visit = [BASE]
    results = {
        "total": 0,
        "ok": 0,
        "broken": 0,
        "broken_urls": [],
        "errors": []
    }

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            status = resp.status_code
            results["total"] += 1

            if status == 200:
                results["ok"] += 1
            else:
                results["broken"] += 1
                cls = classify_broken(status, url, resp.history)
                results["broken_urls"].append({
                    "url": url,
                    "status": status,
                    "final_url": resp.url,
                    "classification": cls,
                    "redirect_chain": [r.url for r in resp.history] + [resp.url]
                })
                if len(results["broken_urls"]) <= 15:
                    print(f"BROKEN [{cls}] {status} {url} -> {resp.url}")

            # Only parse links if we got a successful HTML response
            if status == 200 and "text/html" in resp.headers.get("content-type", ""):
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    # Skip anchors, javascript,mailto, tel
                    if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                        continue
                    full_url = urljoin(url, href)
                    if is_internal(full_url) and full_url not in visited:
                        to_visit.append(full_url)

        except requests.exceptions.RequestException as e:
            results["errors"].append({"url": url, "error": str(e)})
            results["broken"] += 1
            results["broken_urls"].append({
                "url": url,
                "status": 0,
                "final_url": None,
                "classification": "external_reference_error",
                "redirect_chain": []
            })
            print(f"ERROR {url} -> {e}")

        time.sleep(DELAY)

    # Sort broken URLs by status then URL
    results["broken_urls"].sort(key=lambda x: (x["status"], x["url"]))
    return results

if __name__ == "__main__":
    print(f"Starting crawl of {BASE}...")
    print(f"Max pages: {MAX_PAGES}, Delay: {DELAY}s")
    print("-" * 60)

    t0 = time.time()
    results = crawl()
    elapsed = time.time() - t0

    print("-" * 60)
    print(f"Crawl complete in {elapsed:.1f}s")
    print(f"Total crawled: {results['total']}")
    print(f"HTTP 200:      {results['ok']}")
    print(f"Broken:        {results['broken']}")

    if results["broken_urls"]:
        print(f"\nFirst 10 broken URLs:")
        for i, b in enumerate(results["broken_urls"][:10], 1):
            print(f"  {i}. [{b['classification']}] {b['status']} {b['url']}")
            if b['final_url'] and b['final_url'] != b['url']:
                print(f"     redirects to: {b['final_url']}")

    if results["errors"]:
        print(f"\nConnection errors ({len(results['errors'])}):")
        for e in results["errors"][:5]:
            print(f"  {e['url']}: {e['error']}")

    print("\nDone.")
