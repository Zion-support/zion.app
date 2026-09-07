import os, sys

blog_src = sys.argv[1]
out_path = sys.argv[2]

posts = []
for entry in sorted(os.listdir(blog_src), reverse=True):
    p = os.path.join(blog_src, entry)
    if not os.path.isdir(p):
        continue
    if entry.startswith('__next'):
        continue
    idx = os.path.join(p, 'index.html')
    if not os.path.exists(idx):
        continue
    with open(idx) as f:
        html = f.read()
    title = slug = entry
    for line in html.split('\n'):
        if '<title>' in line:
            title = line.split('<title>')[1].split('</title>')[0].replace(' — Zion Tech Group', '')
            break
    posts.append((title, entry))

css = """
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 24px; }
    h1 { font-size: 2rem; color: #7c3aed; margin-bottom: 8px; }
    .sub { color: #64748b; margin-bottom: 32px; }
    .post { border-bottom: 1px solid #e2e8f0; padding: 20px 0; }
    .post h2 { margin: 0 0 8px 0; font-size: 1.2rem; }
    .post h2 a { color: #1e293b; text-decoration: none; }
    .post h2 a:hover { color: #7c3aed; }
    .post .meta { color: #94a3b8; font-size: 0.85rem; }
    .back { display: inline-block; margin-bottom: 24px; color: #7c3aed; text-decoration: none; }
"""

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Blog — Zion Tech Group</title>
  <meta name="description" content="AI automation, enterprise IT services, cybersecurity, cloud migration, and monetization strategies. Practical guides and insights from Zion Tech Group." />
  <link rel="canonical" href="https://ziontechgroup.com/blog/" />
  <style>{css}</style>
</head>
<body>
  <a href="/" class="back">← Home</a>
  <h1>Blog</h1>
  <p class="sub">AI automation, enterprise IT services, cybersecurity, cloud, and business growth — practical guides from Zion Tech Group.</p>
'''
for title, slug in posts:
    html += f'  <div class="post"><h2><a href="/blog/{slug}/">{title}</a></h2><div class="meta">{slug.replace("-", " ")}</div></div>\n'

html += '''  <footer><p style="margin-top:48px; color:#94a3b8; font-size:0.9rem;">Zion Tech Group — <a href="/">Home</a></p></footer>
</body>
</html>'''

with open(out_path, 'w') as f:
    f.write(html)
print(f"Generated: {out_path} with {len(posts)} posts")
