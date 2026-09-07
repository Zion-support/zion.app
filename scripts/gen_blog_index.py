#!/usr/bin/env python3
"""Gera public/blog/index.html estático a partir dos posts em public/blog/*/"""
import os, sys
from pathlib import Path

PUBLIC_BLOG = Path("/Users/miami2/zion.app/public/blog")
OUT = PUBLIC_BLOG / "index.html"

posts = []
for d in sorted(PUBLIC_BLOG.iterdir(), reverse=True):
    if not d.is_dir():
        continue
    idx = d / "index.html"
    if not idx.exists():
        continue
    html = idx.read_text(encoding="utf-8")
    title = d.name.replace("-", " ").title()
    for line in html.splitlines():
        if "<title>" in line:
            t = line.split("<title>", 1)[1].split("</title>", 1)[0]
            t = t.replace(" — Zion Tech Group", "").strip()
            if t:
                title = t
            break
    posts.append((title, d.name))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Blog — Zion Tech Group</title>
  <meta name="description" content="AI automation, enterprise IT services, cybersecurity, cloud migration, and monetization strategies. Practical guides and insights from Zion Tech Group." />
  <link rel="canonical" href="https://ziontechgroup.com/blog/" />
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 24px; line-height: 1.7; color: #1a1a2e; }}
    h1 {{ font-size: 2rem; color: #7c3aed; margin-bottom: 8px; }}
    .sub {{ color: #64748b; margin-bottom: 32px; }}
    .post {{ border-bottom: 1px solid #e2e8f0; padding: 20px 0; }}
    .post h2 {{ margin: 0 0 8px 0; font-size: 1.2rem; }}
    .post h2 a {{ color: #1e293b; text-decoration: none; }}
    .post h2 a:hover {{ color: #7c3aed; }}
    .post .meta {{ color: #94a3b8; font-size: 0.85rem; }}
    .back {{ display: inline-block; margin-bottom: 24px; color: #7c3aed; text-decoration: none; font-weight: 600; }}
    footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.9rem; }}
    footer a {{ color: #7c3aed; }}
  </style>
</head>
<body>
  <a href="/" class="back">← Home</a>
  <h1>Blog</h1>
  <p class="sub">AI automation, enterprise IT services, cybersecurity, cloud, and business growth — practical guides from Zion Tech Group.</p>
"""
for title, slug in posts:
    html += f'  <div class="post"><h2><a href="/blog/{slug}/">{title}</a></h2><div class="meta">{slug.replace("-", " ")}</div></div>\n'

html += """  <footer>
    <p>Zion Tech Group — <a href="/">Home</a> · <a href="/services/">Services</a> · <a href="/contact/">Contact</a></p>
  </footer>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"Generated {OUT} with {len(posts)} posts")
for t, s in posts:
    print(f"  • {t} → /blog/{s}/")
