#!/bin/bash
# Diagnostic complet du état Zion — 03/09/2026
set -e
cd /Users/miami2/zion.app

echo "========================================="
echo "  DIAGNOSTIC ZION — ÉTAT CURRENT"
echo "========================================="
echo ""

echo "--- 1. BLOG: 4 posts créés en 02/09 ---"
for slug in ai-automation-brazilian-enterprises-2026 ai-automation-roi-calculator-guide-2026 how-to-choose-ai-automation-partner-enterprise it-services-partner-program-recurring-revenue-2026; do
  src="blog/$slug"
  pub="public/blog/$slug/index.html"
  if [ -f "$src" ]; then
    lines=$(wc -l < "$src")
    echo "  ✓ SOURCE: $slug ($lines lignes)"
  else
    echo "  ✗ SOURCE: $slug MISSING"
  fi
  if [ -f "$pub" ]; then
    bytes=$(wc -c < "$pub")
    echo "  ✓ PUBLIC: $slug/index.html ($bytes bytes)"
  else
    echo "  ✗ PUBLIC: $slug/index.html MISSING"
  fi
done
echo ""

echo "--- 2. BLOG INDEX (public/blog/index.html) ---"
if [ -f "public/blog/index.html" ]; then
  posts=$(grep -c 'class="post"' public/blog/index.html 2>/dev/null || echo "0")
  echo "  ✓ EXISTS: $(wc -c < public/blog/index.html) bytes, $posts posts listés"
else
  echo "  ✗ MISSING"
fi
echo ""

echo "--- 3. GIT STATUS (top-level) ---"
git status --short | head -10
echo "  ... ($(git status --short | wc -l) files total)"
echo ""

echo "--- 4. GIT LOG (derniers 5 commits) ---"
git log --oneline -5
echo ""

echo "--- 5. BLOG INDEX GIT TRACKING ---"
echo "  public/blog/index.html:"
git ls-files public/blog/index.html 2>/dev/null && echo "    TRACKED" || echo "    UNTRACKED"
echo "  blog/index.html:"
git ls-files blog/index.html 2>/dev/null && echo "    TRACKED" || echo "    UNTRACKED"
echo ""

echo "--- 6. GROWTH ENGINE ---"
if [ -f "automation/reports/growth-engine-report-latest.json" ]; then
  python3 -c "
import json
d=json.load(open('automation/reports/growth-engine-report-latest.json'))
print(f'  run_id: {d[\"run_id\"]}')
print(f'  status: {d[\"status\"]}')
print(f'  exit_code: {d[\"exit_code\"]}')
print(f'  ts: {d[\"ts\"]}')
" 2>/dev/null
else
  echo "  ✗ growth-engine-report-latest.json MISSING"
fi
echo ""

echo "--- 7. DISCOVERY LEADS (email_discovery_results.json) ---"
if [ -f "automation/data/email_discovery_results.json" ]; then
  python3 -c "
import json
log=set()
try:
    for l in open('outreach-send-log.jsonl'):
        if l.strip():
            r=json.loads(l)
            log.add(r['to'].lower())
except: pass
d=json.load(open('automation/data/email_discovery_results.json'))
total=len(d)
ready=0
for e in d:
    for m in e.get('personal_emails_found',[]):
        if m.lower() not in log and 'ziontechgroup' not in m.lower():
            ready+=1
print(f'  total entries: {total}')
print(f'  leads prêts pour envoi: {ready}')
" 2>/dev/null
else
  echo "  ✗ email_discovery_results.json MISSING"
fi
echo ""

echo "--- 8. COMPOSTIO SECRETS ---"
if [ -f ".composio/secrets.env" ]; then
  echo "  ✓ .composio/secrets.env EXISTS"
  grep -c '=$' .composio/secrets.env 2>/dev/null | xargs echo "  chaves vazias: "
else
  echo "  ✗ .composio/secrets.env MISSING"
fi
echo ""

echo "--- 9. SITE CHECK (HTTP status) ---"
for route in "/" "/blog/" "/services/" "/pricing/" "/partners/" "/free-tools-hub/"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://ziontechgroup.com$route" 2>/dev/null || echo "ERR")
  echo "  $route → HTTP $code"
done
echo ""

echo "========================================="
echo "  DIAGNOSTIC COMPLET — $(date)"
echo "========================================="
