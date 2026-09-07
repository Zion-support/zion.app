#!/bin/bash
# deploy-blog.sh — builds blog content into static HTML and copies to public/
set -euo pipefail

BLOG_SRC="/Users/miami2/zion.app/blog"
PUBLIC_BLOG="/Users/miami2/zion.app/public/blog"

log() { echo "[deploy-blog] $(date '+%H:%M:%S') $*"; }

# Ensure output dir exists
mkdir -p "$PUBLIC_BLOG"

log "Scanning blog source for new/updated content..."

for dir in "$BLOG_SRC"/*/; do
  [ -d "$dir" ] || continue
  slug=$(basename "$dir")

  # Skip meta files
  case "$slug" in
    __next.*|index*) continue ;;
  esac

  index_file="$dir/index.html"

  if [ -f "$index_file" ]; then
    # Static HTML already exists — copy/update
    mkdir -p "$PUBLIC_BLOG/$slug"
    cp "$index_file" "$PUBLIC_BLOG/$slug/index.html"
    log "  updated: /blog/$slug/"
  else
    # Markdown/MDX source — generate HTML
    src_file="$dir/page.tsx"
    md_file="$dir/index.md"
    mdx_file="$dir/index.mdx"

    target_dir="$PUBLIC_BLOG/$slug"
    mkdir -p "$target_dir"

    # Extract frontmatter and content, generate HTML
    if [ -f "$md_file" ]; then
      python3 - "$md_file" "$target_dir/index.html" "$slug" <<'PYEOF'
import sys, re, datetime

md_path = sys.argv[1]
out_path = sys.argv[2]
slug = sys.argv[3]

with open(md_path, 'r') as f:
    content = f.read()

# Extract frontmatter
fm = {}
if content.startswith('---'):
    end = content.find('---', 3)
    if end != -1:
        fm_block = content[3:end].strip()
        for line in fm_block.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"\'')
        content = content[end+3:].strip()

title = fm.get('title', slug.replace('-', ' ').title())
desc = fm.get('description', '')
date = fm.get('date', datetime.date.today().isoformat())
keywords = fm.get('keywords', '')

# Convert markdown to HTML
def md_to_html(text):
    lines = text.split('\n')
    html = []
    in_code = False
    code_lines = []
    for line in lines:
        if line.startswith('```'):
            if in_code:
                html.append('<pre><code>' + '\n'.join(code_lines) + '</code></pre>')
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith('# '):
            html.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            html.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('- '):
            html.append(f'<li>{line[2:]}</li>')
        elif line.startswith('* ') or line.startswith('- '):
            html.append(f'<li>{line[2:]}</li>')
        elif line.strip().startswith('|'):
            html.append(f'<!-- table: {line} -->')
        elif line.strip() == '':
            continue
        else:
            html.append(f'<p>{line}</p>')
    if in_code:
        html.append('<pre><code>' + '\n'.join(code_lines) + '</code></pre>')
    # Wrap lists
    result = '\n'.join(html)
    result = re.sub(r'(?s)(<ul>)?<li>(.*?)</li>(</ul>)?', r'<ul><li>\2</li></ul>', result)
    return result

body = md_to_html(content)

# Build HTML
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} — Zion Tech Group</title>
  <meta name="description" content="{desc}" />
  <meta name="keywords" content="{keywords}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="article" />
  <meta property="article:published_time" content="{date}" />
  <link rel="canonical" href="https://ziontechgroup.com/blog/{slug}/" />
  <link rel="stylesheet" href="/css/style.css" />
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 24px; line-height: 1.7; color: #1a1a2e; }
    h1 { font-size: 2.2rem; color: #7c3aed; margin-bottom: 16px; }
    h2 { font-size: 1.5rem; color: #334155; margin-top: 32px; margin-bottom: 12px; }
    h3 { font-size: 1.2rem; color: #475569; margin-top: 24px; margin-bottom: 8px; }
    p { margin-bottom: 16px; }
    ul { margin-bottom: 16px; padding-left: 24px; }
    li { margin-bottom: 8px; }
    a { color: #7c3aed; }
    .meta { color: #64748b; font-size: 0.9rem; margin-bottom: 32px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; }
    .back { display: inline-block; margin-bottom: 24px; color: #7c3aed; text-decoration: none; font-weight: 600; }
    pre { background: #f1f5f9; padding: 16px; border-radius: 8px; overflow-x: auto; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
    th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }
    th { background: #f1f5f9; }
    blockquote { border-left: 4px solid #7c3aed; padding-left: 16px; color: #64748b; margin: 16px 0; }
  </style>
</head>
<body>
  <a href="/blog/" class="back">← Back to Blog</a>
  <div class="meta">{date} · {desc}</div>
  {body}
  <footer style="margin-top:48px; padding-top:24px; border-top:1px solid #e2e8f0; color:#64748b; font-size:0.9rem;">
    <p>Zion Tech Group — AI & IT Services for Measurable Growth</p>
    <p><a href="/">Home</a> · <a href="/services/">Services</a> · <a href="/contact/">Contact</a></p>
  </footer>
</body>
</html>'''

with open(out_path, 'w') as f:
    f.write(html)
print(f"Generated: {out_path}")
PYEOF
      log "  generated: /blog/$slug/"
    fi
  fi
done

# Update blog index
log "Regenerating blog index..."
python3 - "$BLOG_SRC" "$PUBLIC_BLOG/index.html" <<'PYEOF'
import os, datetime

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
    # Parse title from HTML
    with open(idx) as f:
        html = f.read()
    title = slug = entry
    for line in html.split('\n'):
        if '<title>' in line:
            title = line.split('<title>')[1].split('</title>')[0].replace(' — Zion Tech Group', '')
            break
    posts.append((title, entry))

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Blog — Zion Tech Group</title>
  <meta name="description" content="AI automation, enterprise IT services, cybersecurity, cloud migration, and monetization strategies. Practical guides and insights from Zion Tech Group." />
  <link rel="canonical" href="https://ziontechgroup.com/blog/" />
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 24px; }
    h1 { font-size: 2rem; color: #7c3aed; margin-bottom: 8px; }
    .sub { color: #64748b; margin-bottom: 32px; }
    .post { border-bottom: 1px solid #e2e8f0; padding: 20px 0; }
    .post h2 { margin: 0 0 8px 0; font-size: 1.2rem; }
    .post h2 a { color: #1e293b; text-decoration: none; }
    .post h2 a:hover { color: #7c3aed; }
    .post .meta { color: #94a3b8; font-size: 0.85rem; }
    .back { display: inline-block; margin-bottom: 24px; color: #7c3aed; text-decoration: none; }
  </style>
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
PYEOF

log "Blog deploy complete."
