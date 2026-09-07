#!/usr/bin/env python3
"""Zion Tech Group live integrity check — stepwise probe + BFS crawl."""
import sys, json, re, os
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import requests
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
BASE_NETLOC = urlparse(BASE).netloc
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ZionIntegrity/1.0)"})

def norm(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment="", scheme=p.scheme.lower(), netloc=p.netloc.lower()))

def is_internal(url):
    return urlparse(url).netloc.lower() == BASE_NETLOC

def probe(url):
    try:
        r = session.get(url, timeout=15, allow_redirects=True)
        return r.status_code, r.url
    except Exception as e:
        return None, str(e)

def classify(url, status, final_url, err):
    if err is not None:
        return "missing page" if is_internal(url) else "external reference error"
    if status is None:
        return "missing page"
    if 200 <= status < 300:
        return "ok"
    if is_internal(url):
        if final_url and urlparse(final_url).netloc.lower() != BASE_NETLOC:
            return "stale redirect"
        return "missing page" if status >= 400 else "stale redirect"
    return "external reference error"

def extract_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all(["a"], href=True):
        href = tag["href"]
        full = norm(urljoin(page_url, href))
        if not is_internal(full):
            continue
        path = urlparse(full).path
        if path.endswith((".png",".jpg",".jpeg",".gif",".svg",".ico",".css",".js",".woff",".woff2",".ttf",".eot")):
            continue
        links.append(full)
    # dedupe
    seen = set()
    out = []
    for l in links:
        if l not in seen:
            seen.add(l)
            out.append(l)
    return out

def run():
    total, ok200, broken = 0, 0, []
    visited = set()
    queue = deque()

    # seed homepage
    print("Seeding from https://ziontechgroup.com ...", file=sys.stderr)
    visited.add(BASE)
    queue.append(BASE)

    # also try to seed from sitemap
    try:
        sr = session.get(f"{BASE}/sitemap.xml", timeout=20)
        if sr.status_code == 200:
            sitemap_urls = re.findall(r'<loc>(.*?)</loc>', sr.text)
            for u in sitemap_urls:
                u = norm(u)
                if is_internal(u) and u not in visited:
                    visited.add(u)
                    queue.append(u)
            print(f"Sitemap seeded {len(sitemap_urls)} URLs", file=sys.stderr)
    except Exception as e:
        print(f"Sitemap skipped: {e}", file=sys.stderr)

    print(f"Queue: {len(queue)} URLs. Starting crawl...", file=sys.stderr)
    while queue and total < 5000:
        url = queue.popleft()
        total += 1
        status, final_or_err = probe(url)
        if isinstance(final_or_err, str):
            err = final_or_err
            final_url = None
        else:
            err = None
            final_url = final_or_err

        if status is not None and 200 <= status < 300:
            ok200 += 1
            # extract links from page
            try:
                html = session.get(url, timeout=15).text
                for link in extract_links(html, url):
                    if link not in visited:
                        visited.add(link)
                        queue.append(link)
            except Exception:
                pass
        else:
            cls = classify(url, status, final_url, err)
            broken.append({
                "url": url,
                "status": status if err is None else f"ERR: {err}",
                "classification": cls,
                "final_url": final_url,
            })

        if total % 100 == 0:
            print(f"  crawled {total}, 200s: {ok200}, broken: {len(broken)}", file=sys.stderr)

    print(f"\n=== INTEGRITY CHECK REPORT ===", file=sys.stderr)
    print(f"Site: {BASE}", file=sys.stderr)
    print(f"Total crawled (internal pages): {total}", file=sys.stderr)
    print(f"HTTP 200 count: {ok200}", file=sys.stderr)
    print(f"Broken count: {len(broken)}", file=sys.stderr)

    # classification summary
    cls_counts = {}
    for b in broken:
        c = b["classification"]
        cls_counts[c] = cls_counts.get(c, 0) + 1

    print("\nFirst 10 broken URLs:", file=sys.stderr)
    for i, b in enumerate(broken[:10], 1):
        print(f"  {i}. {b['url']}", file=sys.stderr)
        print(f"     Status: {b['status']}  |  Classification: {b['classification']}", file=sys.stderr)
    if cls_counts:
        print("\nClassification summary:", file=sys.stderr)
        for c, n in sorted(cls_counts.items()):
            print(f"  {c}: {n}", file=sys.stderr)

    report = {
        "site": BASE,
        "total_crawled": total,
        "http_200_count": ok200,
        "broken_count": len(broken),
        "broken_urls": broken[:10],
        "classification_summary": cls_counts,
    }
    out_path = "/Users/miami2/zion.app/automation/reports/site-integrity-latest.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nJSON report: {out_path}", file=sys.stderr)
    return report

if __name__ == "__main__":
    run()
