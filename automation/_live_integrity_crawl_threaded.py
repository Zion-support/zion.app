#!/usr/bin/env python3
import subprocess, sys, threading

code = r'''
#!/usr/bin/env python3
"""Live site integrity crawl for https://ziontechgroup.com — threaded BFS."""
import sys
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://ziontechgroup.com"
SCHEME = "https"
HOST = "ziontechgroup.com"
MAX_WORKERS = 6
FETCH_TIMEOUT = 20

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (zion-integrity-crawl/1.0)"})

# shared state
visited = set()
queue = []
lock = None  # we'll use a simple list + set; threading with lock
from threading import Lock
_mu = Lock()

broken = []
redirects = []
total = 0
ok200 = 0

def strip_fragment(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

def is_internal(url):
    p = urlparse(url)
    return p.scheme in (SCHEME, "") and (p.netloc == HOST or p.netloc == "")

def normalize(url):
    url = strip_fragment(url)
    if urlparse(url).scheme == "":
        url = urljoin(BASE + "/", url)
    return url

def fetch(url):
    try:
        resp = session.get(url, allow_redirects=True, timeout=FETCH_TIMEOUT)
        return resp
    except Exception:
        return None

def process_url(url):
    global total, ok200
    url = normalize(url)
    with _mu:
        if url in visited:
            return
        visited.add(url)
        total += 1
        if url not in queue:
            queue.append(url)
    print(f"[{total}] FETCH {url}", flush=True)
    resp = fetch(url)
    if resp is None:
        with _mu:
            broken.append((url, "missing page (connection exception)"))
        return
    status = resp.status_code
    if len(resp.history) > 0:
        with _mu:
            for h in resp.history:
                redirects.append((url, h.url, h.status_code))
    if status == 200:
        with _mu:
            ok200 += 1
        html = resp.text
        if len(html) > 0:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception:
                soup = BeautifulSoup("", "html.parser")
            new_links = []
            for tag in soup.find_all(["a", "link"]):
                href = tag.get("href")
                if not href:
                    continue
                full = urljoin(url, href)
                full = normalize(full)
                if not is_internal(full):
                    continue
                new_links.append(full)
            with _mu:
                for l in new_links:
                    if l not in visited and l not in queue:
                        queue.append(l)
        return
    if 300 <= status < 400:
        final_url = resp.url
        if not is_internal(final_url):
            reason = f"stale redirect (3xx -> external {final_url})"
        else:
            reason = f"stale redirect (3xx internal, final {final_url} status {resp.status_code})"
        with _mu:
            broken.append((url, reason))
        return
    with _mu:
        broken.append((url, f"missing page (HTTP {status})"))

print(f"Starting threaded BFS crawl of {BASE}", flush=True)

# seed
with _mu:
    queue.append(BASE)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = set()
    while True:
        with _mu:
            if not queue:
                # no more work
                break
            batch = queue[:200]
            del queue[:200]
        for url in batch:
            f = ex.submit(process_url, url)
            futures.add(f)
        # drain completed
        done = {f for f in futures if f.done()}
        futures -= done
        for f in done:
            try:
                f.result()
            except Exception as e:
                print(f"worker exception: {e}", flush=True)
        # small pause to avoid hammering
        import time
        time.sleep(0.05)

print("\n===== INTEGRITY REPORT =====", flush=True)
print(f"Base URL: {BASE}", flush=True)
print(f"Total crawled: {total}", flush=True)
print(f"HTTP 200: {ok200}", flush=True)
print(f"Broken: {len(broken)}", flush=True)
print(f"Redirects tracked: {len(redirects)}", flush=True)
print("\n--- First 10 broken URLs ---", flush=True)
for i, (url, reason) in enumerate(broken[:10], 1):
    print(f"{i}. {url}  [{reason}]", flush=True)
if len(broken) == 0:
    print("\nSite healthy — no broken internal links found.", flush=True)
else:
    stale = sum(1 for _, r in broken if r.startswith("stale redirect"))
    missing = sum(1 for _, r in broken if r.startswith("missing page"))
    ext_err = sum(1 for _, r in broken if "external" in r.lower())
    print(f"\n--- Classification summary ---", flush=True)
    print(f"  stale redirect: {stale}", flush=True)
    print(f"  missing page: {missing}", flush=True)
    print(f"  external reference error: {ext_err}", flush=True)
print("\n===== END =====", flush=True)
'''

with open('/tmp/_live_crawl_threaded.py', 'w') as f:
    f.write(code)

proc = subprocess.run(
    [sys.executable, '/tmp/_live_crawl_threaded.py'],
    capture_output=True,
    text=True,
    timeout=600,
)
print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr, file=sys.stderr)
sys.exit(proc.returncode)
