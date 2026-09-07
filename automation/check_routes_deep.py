#!/usr/bin/env python3
"""Deep route check: status + canonical + noindex + basic content markers."""
import requests
import re
import json
from bs4 import BeautifulSoup

BASE = "https://ziontechgroup.com"
ROUTES = [
    ("/", "Homepage"),
    ("/public-roadmap", "Public Roadmap"),
    ("/status-page", "Status Page"),
    ("/use-cases", "Use Cases"),
    ("/solutions/healthcare", "Solutions / Healthcare"),
    ("/industries/financial-services", "Industries / Financial Services"),
    ("/free-consultation", "Free Consultation"),
    ("/tools/phishing-analyzer", "Tools / Phishing Analyzer"),
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})

print("=" * 70)
print("DEEP SITE INTEGRITY CHECK — https://ziontechgroup.com")
print("=" * 70)
print()

deep_results = []
for path, label in ROUTES:
    url = BASE + path
    print(f"--- {label} : {url} ---")
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        status = resp.status_code
        final = resp.url
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Canonical
        canonical = ""
        for link in soup.find_all("link", rel="canonical"):
            canonical = link.get("href", "")

        # Meta robots
        robots_meta = ""
        for meta in soup.find_all("meta", attrs={"name": "robots"}):
            ct = meta.get("content", "")
            if ct:
                robots_meta = str(ct)

        # Title
        title = ""
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else ""

        # Check for key indicators
        issues = []
        if status != 200:
            issues.append(f"HTTP {status}")
        if not canonical:
            issues.append("missing canonical")
        elif canonical != final:
            issues.append(f"canonical mismatch: {canonical}")

        if robots_meta and "noindex" in str(robots_meta).lower():
            issues.append(f"noindex present: {robots_meta}")

        if not title:
            issues.append("missing <title>")

        # Check body has meaningful content (more than just nav)
        body_text = soup.get_text(separator=" ", strip=True)
        word_count = len(body_text.split())
        if word_count < 50:
            issues.append(f"thin content: ~{word_count} words")

        healthy = len(issues) == 0
        status_icon = "OK" if healthy else "XX"

        print(f"  Status: {status} (final: {final})")
        print(f"  Title: {title[:80]}")
        print(f"  Canonical: {canonical or '(none)'}")
        print(f"  Robots: {robots_meta or '(none)'}")
        print(f"  Content words: ~{word_count}")
        if issues:
            print(f"  ISSUES: {'; '.join(issues)}")
        else:
            print(f"  All checks passed")
        print()

        deep_results.append({
            "label": label,
            "url": url,
            "final_url": final,
            "status": status,
            "title": title,
            "canonical": canonical,
            "robots": robots_meta,
            "word_count": word_count,
            "issues": issues,
            "healthy": healthy,
        })

    except Exception as e:
        print(f"  ERROR: {e}")
        print()
        deep_results.append({
            "label": label,
            "url": url,
            "status": None,
            "error": str(e),
            "healthy": False,
        })

print("=" * 70)
print("SUMMARY")
print("=" * 70)
ok = [r for r in deep_results if r.get("healthy")]
broken = [r for r in deep_results if not r.get("healthy")]
print(f"Total: {len(deep_results)}")
print(f"All clear: {len(ok)}")
print(f"Issues: {len(broken)}")
print()
if broken:
    print("ROUTES WITH ISSUES:")
    for r in broken:
        print(f"  - {r['label']} ({r['url']})")
        if r.get("issues"):
            for i in r["issues"]:
                print(f"      {i}")
        if r.get("error"):
            print(f"      error: {r['error']}")
print()
print("=" * 70)
print("JSON OUTPUT")
print("=" * 70)
print(json.dumps(deep_results, indent=2))
