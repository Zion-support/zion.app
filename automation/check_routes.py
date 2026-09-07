#!/usr/bin/env python3
"""Direct HTTP check for key Zion Tech Group routes."""
import requests
import json
import sys

BASE = "https://ziontechgroup.com"
ROUTES = [
    "/",
    "/public-roadmap",
    "/status-page",
    "/use-cases",
    "/solutions/healthcare",
    "/industries/financial-services",
    "/free-consultation",
    "/tools/phishing-analyzer",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})

print("=" * 70)
print(f"SITE INTEGRITY CHECK — {BASE}")
print("=" * 70)
print()

results = []
for path in ROUTES:
    url = BASE + path
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        status = resp.status_code
        final = resp.url
        is_redirect = final != url
        healthy = status == 200
        results.append((url, status, final, is_redirect, healthy))
        status_icon = "OK" if healthy else "XX"
        redirect_note = f" -> redirected to {final}" if is_redirect else ""
        print(f"[{status_icon}] {url}")
        print(f"    Status: {status}{redirect_note}")
        if not healthy:
            print(f"    ** ISSUE DETECTED **")
        print()
    except Exception as e:
        print(f"[ERR] {url}")
        print(f"    ERROR: {e}")
        print()
        results.append((url, None, None, False, False))

print("=" * 70)
print("SUMMARY")
print("=" * 70)
ok = sum(1 for r in results if r[4])
broken = sum(1 for r in results if not r[4])
print(f"Total routes checked: {len(results)}")
print(f"OK (200): {ok}")
print(f"Issues: {broken}")
print()

if broken > 0:
    print("PROBLEMS:")
    for url, status, final, is_redirect, healthy in results:
        if not healthy:
            if status is None:
                print(f"  - {url} -- connection/error")
            elif status != 200:
                print(f"  - {url} -- HTTP {status}" + (f" (redirected to {final})" if is_redirect else ""))

print()
print("=" * 70)
print("DETAILED RESULTS")
print("=" * 70)
print(json.dumps([
    {
        "url": r[0],
        "status": r[1],
        "final_url": r[2],
        "redirected": r[3],
        "healthy": r[4]
    }
    for r in results
], indent=2))
