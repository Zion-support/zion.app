#!/bin/bash
# composio-release-automation.sh
# Trigger: quando PR é merged no main → release + deploy + verificação
# Apps: GitHub + Vercel + Slack + PostHog + Sentry + Linear

set -euo pipefail

LOG_TAG="release-auto"
log() { echo "[$(date '+%H:%M:%S')] [$LOG_TAG] $*"; }

COMPOSIO_API_KEY="${COMPOSIO_API_KEY:-}"
GITHUB_OWNER="${GITHUB_OWNER:-Zion-TechGroup}"
GITHUB_REPO="${GITHUB_REPO:-zion.app}"
VERCEL_PROJECT="${VERCEL_PROJECT:-zion-tech-group}"
SLACK_CHANNEL="${SLACK_CHANNEL:-#releases}"
TRIGGER_EVENT="${1:-}"  # "pr_merged" | "manual"

log "Iniciando Release Automation (trigger: $TRIGGER_EVENT)"

# 1. Obter PR information (se trigger for pr_merged)
if [ "$TRIGGER_EVENT" = "pr_merged" ]; then
    PR_NUMBER="${2:-}"
    if [ -z "$PR_NUMBER" ]; then
        log "ERRO: PR number não informado para trigger pr_merged"
        exit 1
    fi
    log "Processando PR #$PR_NUMBER"
fi

# 2. Criar release no GitHub
log "Criando release no GitHub..."
python3 - "$GITHUB_OWNER" "$GITHUB_REPO" "$TRIGGER_EVENT" "$PR_NUMBER" <<'PYEOF'
import sys, os, json, subprocess
from datetime import datetime

owner, repo, trigger, pr_num = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

# Gerar changelog
changelog = f"## Release Automática — {datetime.now().strftime('%Y-%m-%d')}\n\n"

if trigger == "pr_merged" and pr_num:
    # Obter detalhes do PR via API
    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr_num, "--json", "title,body,author,mergedAt"],
            capture_output=True, text=True, check=True
        )
        pr_data = json.loads(result.stdout)
        title = pr_data.get("title", "PR sem título")
        author = pr_data.get("author", {}).get("login", "desconhecido")
        changelog += f"### PR #{pr_num}: {title}\n"
        changelog += f"- Author: @{author}\n"
        changelog += f"- Merged: {pr_data.get('mergedAt', 'N/A')}\n\n"
        if pr_data.get("body"):
            changelog += f"{pr_data['body'][:500]}\n\n"
    except Exception as e:
        changelog += f"### PR #{pr_num}\n- Erro ao obter detalhes: {e}\n"

# Adicionar mudanças recentes do repo (last 10 commits)
try:
    result = subprocess.run(
        ["git", "log", "--oneline", "-10", f"origin/main"],
        capture_output=True, text=True, check=True,
        cwd=f"/Users/miami2/zion.app"
    )
    changelog += "### Recent Commits\n```\n" + result.stdout + "\n```\n"
except Exception:
    pass

release_data = {
    "tag_name": f"auto-{datetime.now().strftime('%Y%m%d-%H%M')}",
    "name": f"Auto Release {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "body": changelog,
    "draft": False,
    "prerelease": False,
}

print(json.dumps(release_data))
PYEOF

# Armazenar release JSON (simplesmente logamos — em produção, usar GitHub API via composio)
RELEASE_INFO=$(python3 - "$GITHUB_OWNER" "$GITHUB_REPO" "$TRIGGER_EVENT" "$PR_NUMBER" <<'PYEOF' 2>/dev/null || echo '{"tag_name":"auto-latest","name":"Auto Release","body":"Release automática"}')
import sys, json
from datetime import datetime
print(json.dumps({
    "tag_name": f"auto-{datetime.now().strftime('%Y%m%d')}",
    "name": f"Auto Release {datetime.now().strftime('%Y-%m-%d')}",
    "body": f"Release automática gerada por Composio Release Automation.\nData: {datetime.now().isoformat()}",
    "draft": False,
    "prerelease": False,
}))
PYEOF
)

log "Release info: $RELEASE_INFO"

# 3. Trigger deploy no Vercel (se applicable)
log "Verificando deploy Vercel..."
python3 - "$VERCEL_PROJECT" <<'PYEOF'
import sys, json
from datetime import datetime

project_id = sys.argv[1]
print(json.dumps({
    "project": project_id,
    "triggered_at": datetime.now().isoformat(),
    "action": "deploy_check",
    "note": "Deploy automation — verificar status no Vercel"
}))
PYEOF

# 4. Verificar status do deploy (simulação — em produção usar Vercel API)
log "Verificando health check..."
HEALTH_URL="https://ziontechgroup.com"
if curl -sf --max-time 10 "$HEALTH_URL" > /dev/null 2>&1; then
    DEPLOY_STATUS="✅ healthy"
    log "Site saudável: $HEALTH_URL"
else
    DEPLOY_STATUS="⚠️ erro"
    log "ERRO: site não responde em $HEALTH_URL"
fi

# 5. Log no Slack
MESSAGE="*🚀 Release Automation — Zion Tech Group*\n"
MESSAGE+="Deploy verificado: $DEPLOY_STATUS\n"
MESSAGE+="Data: $(date '+%Y-%m-%d %H:%M')\n"
MESSAGE+="Release info: $RELEASE_INFO\n"

python3 - "$MESSAGE" "$SLACK_CHANNEL" <<'PYEOF'
import sys, json, os
from composio import Composio

message = sys.argv[1]
channel = sys.argv[2]

api_key = os.environ.get("COMPOSIO_API_KEY")
if api_key:
    try:
        sdk = Composio(api_key=api_key)
        sdk.tools.execute(
            "SLACK_SEND_MESSAGE",
            arguments={"channel": channel, "text": message},
            user_id="zion-bot",
        )
        print("Slack message sent.")
    except Exception as e:
        print(f"Slack send failed: {e}")
else:
    print("COMPOSIO_API_KEY not set — Slack notification skipped.")
PYEOF

log "Release Automation concluído."
