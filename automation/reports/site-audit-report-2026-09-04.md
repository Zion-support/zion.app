# Site Audit Report — 2026-09-04

## Executed

- Full crawl + HTTP status check against live site.
- Total pages listed: 693
- 404 pages found: 44 (6.3%)

## Confirmed 404s (high-impact, content routes)

- `/industries/insurance/`
- `/industries/legal/`

These are real content routes missing their HTML files; not numeric-suffix artifacts or stale sitemap entries.

## Other 404s

- 42 additional 404 pages of lower or ambiguous impact (mixed patterns — numeric suffixes, missing blog post HTML, placeholder slugs, etc.). Full list available in the raw audit artifact if needed.

## Notes

- No canonical path leaks found for the two high-impact routes.
- No evidence these routes exist under alternate paths (e.g. `/services/`, `/industries/`, `/docs/`) — both are unresolved content gaps.
- Audit log: `/Users/miami2/.hermes/cache/terminal-output/out-2147483647-61414-512.log`
