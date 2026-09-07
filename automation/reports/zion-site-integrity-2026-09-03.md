# Zion Tech Group — Site Integrity Check
**Run date:** 2026-09-03 03:05 UTC-3  
**Scope:** `https://ziontechgroup.com` + 7 key doc routes  
**Sources:** `/Users/miami2/zion.app/automation` (integrity scripts + last JSON report), `/Users/miami2/zion-support/zion-support.github.io` (repo root + `public/` build + `_redirects` + deploy workflow + route HTML)

---

## 1. Checks

### 1.1 Live site pulse (curl, zero external dependencies)

| Route | HTTP | Notes |
|---|---|---|
| `/` | **200** | Homepage serves correctly (≈6 KB, correct title) |
| `/public-roadmap` | 404 | Page not found |
| `/status-page` | 404 | Page not found |
| `/use-cases` | 404 | Page not found |
| `/solutions/healthcare` | 404 | Page not found |
| `/industries/financial-services` | 404 | Page not found |
| `/free-consultation` | 404 | Page not found |
| `/tools/phishing-analyzer` | 404 | Page not found |

Slash variants were also 404 — no 301 fallback is active on the live edge.

### 1.2 Last automated crawl (`site-integrity-latest.json`)

- **312 pages** fetched across the site
- **2** returned HTTP 200
- **310** broken — essentially every path except the homepage
- Last run ≈ 47s, stored in `/Users/miami2/zion.app/automation/reports/site-integrity-latest.json`
- The crawl followed internal links only and classified everything it hit as `missing page` (404)

### 1.3 Repo HTML integrity (the build happened)

All 7 route folders exist under the repo root and contain real, distinct `index.html`:

| Route folder | Repo HTML bytes | Title (from HTML) |
|---|---|---|
| `public-roadmap/` | 1,312 | Public Roadmap — Zion Tech Group |
| `status-page/` | 1,317 | Status Page — Zion Tech Group |
| `use-cases/` | 830 | Use-cases \| Zion Tech Group |
| `solutions/healthcare/` | 3,498 | Healthcare Solutions \| Zion Tech Group |
| `industries/financial-services/` | 3,512 | Financial Services \| Zion Tech Group |
| `free-consultation/` | 3,858 | Free Consultation \| Zion Tech Group |
| `tools/phishing-analyzer/` | 927 | Phishing Analyzer \| Zion Tech Group |

Each carries a `<link rel="canonical" href="https://ziontechgroup.com/<path>/">`. The content is present, valid, and on-disk. This is not a content gap — it's a deployment/publishing gap.

### 1.4 Redirect rules (`_redirects`)

The root `_redirects` (1,022 rules, 56 KB) contains working rules for all 7 routes, e.g.:

```
/public-roadmap /public-roadmap/ 301
/public-roadmap/ /public-roadmap/index.html 200
/status-page /status-page/ 301
/status-page/ /status-page/index.html 200
/use-cases /use-cases/ 301
/use-cases/ /docs/use-cases/index.html 200
/solutions/healthcare /docs/solutions/healthcare/index.html 301
/solutions/healthcare/ /docs/solutions/healthcare/index.html 200
/industries/financial-services /docs/industries/financial-services/index.html 301
/industries/financial-services/ /docs/industries/financial-services/index.html 200
/free-consultation /free-consultation/ 301
/free-consultation/ /free-consultation/index.html 200
/tools/phishing-analyzer /tools/phishing-analyzer/ 200
/tools/phishing-analyzer/ /tools/phishing-analyzer/index.html 200
```

A smaller `public/_redirects` (6 lines) exists but it only covers 6 unrelated service/case-study routes — it predates the full routing table and is a stale artifact, not the active one.

### 1.5 Build artifact mismatch (the root cause)

- **Root level:** 230 `index.html` subdirs, most route folders present (services, solutions, tools, public-roadmap, status-page, free-consultation, etc.)
- **`public/` dir:** only 78 `index.html` files, **none** of the 7 target route folders are present, and the sitemap inside `public/` doesn't reference any of them
- **`out/` dir:** essentially empty (only `_redirects`, `affiliate/`, `monetization/`, `stripe/`)
- **Deploy workflow** (`.github/workflows/deploy-static.yml`): uploads `public/` as the Pages artifact

So the build produced the full site in the repo root but the only directory that actually gets published to GitHub Pages is `public/`, which is missing the 7 routes (and many others). The root `_redirects` + root HTML never make it to the live site.

---

## 2. Fixes

### 2.1 Immediate (unblocks all 7 routes + most of the site)

**Publish the full build output, not only `public/`.**  
The deploy workflow currently uploads `public/`. Switch it to upload the repo root (or whichever folder holds the complete `index.html` tree + root `_redirects`). In `deploy-static.yml`:

```yaml
- uses: actions/upload-pages-artifact@v3
  with:
    path: .          # ← was: public/
```

This single change puts the root `_redirects` (1,022 rules) and all 230 route folders onto Pages.

### 2.2 If `public/` must stay the artifact root

Move/symlink the full content into `public/` before the artifact step, or rebuild the Next.js/SSG output so that `public/` receives everything. Either way the artifact root must carry:

- `_redirects` with all 1,022 rules
- `sitemap.xml`
- every route folder that the root currently has

### 2.3 Verify after deploy

Re-run the same curl probe against the 7 routes (and a sample of root-level paths). Expected: 200 on all. Confirm with:

```bash
for u in /public-roadmap /status-page /use-cases /solutions/healthcare \
         /industries/financial-services /free-consultation /tools/phishing-analyzer; do
  echo "$u: $(curl -s -o /dev/null -w '%{http_code}' "https://ziontechgroup.com$u")"
done
```

### 2.4 Ongoing

- Regenerate the integrity report (`site_integrity_focused_crawl.py`) after each deploy and store it in `reports/`; alert if HTTP 200 count != total crawled.
- Keep the root `_redirects` and `public/_redirects` in sync, or drop the stale `public/_redirects` to avoid confusion.

---

## 3. Results

### 3.1 What's working

- Homepage (`/`) returns 200 and is correct.
- The repo has real, valid HTML for all 7 requested routes — content is not missing.
- The root `_redirects` has correct rules for all 7 routes plus 1,022 total rules.

### 3.2 What's broken

- All 7 named routes return **404** on the live site.
- The broader crawl shows 310/312 paths broken — the site is essentially serving only the homepage.
- The deploy pipeline (`public/` artifact) is publishing a subset of the build that excludes these routes, their HTML, and the full `_redirects`/sitemap.

### 3.3 Status by route

| Route | Live | Repo HTML | Rule in `_redirects` | In `public/` artifact | Verdict |
|---|---|---|---|---|---|
| `/public-roadmap` | 404 | ✅ 1,312 B | ✅ yes | ❌ missing | Publish full build |
| `/status-page` | 404 | ✅ 1,317 B | ✅ yes | ❌ missing | Publish full build |
| `/use-cases` | 404 | ✅ 830 B | ✅ yes | ❌ missing | Publish full build |
| `/solutions/healthcare` | 404 | ✅ 3,498 B | ✅ yes | ❌ missing | Publish full build |
| `/industries/financial-services` | 404 | ✅ 3,512 B | ✅ yes | ❌ missing | Publish full build |
| `/free-consultation` | 404 | ✅ 3,858 B | ✅ yes | ❌ missing | Publish full build |
| `/tools/phishing-analyzer` | 404 | ✅ 927 B | ✅ yes | ❌ missing | Publish full build |

### 3.4 Bottom line

**This is a deployment configuration problem, not a content or routing-rules problem.** The content and the redirect rules both exist in the repo; the live site only publishes the `public/` subdirectory, which is missing all 7 routes (and most of the rest of the site). Fix the artifact path in the deploy workflow and the 7 routes — plus roughly 200 others — come back online.
