#!/usr/bin/env python3
"""Diagnose Pages branch + probe 8 routes + check out/ vs docs/."""
import json, os
from urllib.parse import urljoin
import requests

BASE = "https://ziontechgroup.com"
ROUTES = ["/", "/public-roadmap", "/status-page", "/use-cases",
          "/solutions/healthcare", "/industries/financial-services",
          "/free-consultation", "/tools/phishing-analyzer"]

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
})

print("=== LIVE BRANCH DIAGNOSTIC ===")
for path in ["/_redirects", "/"]:
    url = BASE + path
    try:
        r = s.get(url, timeout=10)
        print(f"\n{url} -> {r.status_code}")
        if path == "/_redirects":
            lines = r.text.splitlines()[:40]
            print("--- _redirects (first 40 lines) ---")
            for ln in lines:
                print(ln)
    except Exception as e:
        print(f"{url} ERROR: {e}")

print("\n\n=== SPECIFIC SUBROUTES (live _redirects + direct probes) ===")
for sub in ["/industries/insurance/", "/industries/legal/"]:
    # Direct .html probe
    html_url = BASE + sub + "index.html"
    r_html = s.get(html_url, timeout=10)
    print(f"\n{html_url} -> {r_html.status_code} ({len(r_html.content)}B)")
    # Clean route probe
    clean_url = BASE + sub
    r_clean = s.get(clean_url, timeout=10, allow_redirects=True)
    print(f"{clean_url} -> {r_clean.status_code} (final: {r_clean.url})")

print("\n\n=== CANONICAL ROUTES PROBE ===")
for r in ROUTES:
    url = BASE + r if r != "/" else BASE
    try:
        resp = s.get(url, timeout=15, allow_redirects=True)
        print(f"{resp.status_code:3d} {r:40s} -> {resp.url} ({len(resp.content)}B)")
    except Exception as e:
        print(f"ERR {r:40s} -> {e}")

print("\n\n=== REPO: out/ FILE LIST ===")
for root, dirs, files in os.walk("/Users/miami2/zion-support/zion-support.github.io/out"):
    rel = os.path.relpath(root, "/Users/miami2/zion-support/zion-support.github.io/out")
    if rel == ".":
        for f in sorted(files):
            print(f"out/{f}")
    else:
        for f in sorted(files):
            print(f"out/{rel}/{f}")
        if files:
            pass
