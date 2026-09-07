#!/usr/bin/env bash
#===============================================================================
# composio-vercel-deploy.sh — Deploy Automation + Health Monitoring
#===============================================================================
# Automatiza deploys no Vercel, verifica health checks, loga no Slack.
# Pode ser acionado manualmente ou via trigger de PR merge.
#
# Uso:
#   export COMPOSIO_API_KEY="sk_..."
#   export VERCEL_PROJECT="zion-tech-group"  # ou VERCEL_PROJECT_ID
#   export ZION_SLACK_CHANNEL="#deployments"
#   ./composio-vercel-deploy.sh              # deploy manual
#   ./composio-vercel-deploy.sh --preview     # cria preview deployment
#   ./composio-vercel-deploy.sh --status      # verifica status do último deploy
#===============================================================================

set -uo pipefail

SCRIPT_NAME="composio-vercel-deploy"
SCRIPT_DIR="/Users/miami2/zion.app/automation/scripts"

PROJECT="${VERCEL_PROJECT:-zion-tech-group}"
PROJECT_ID="${VERCEL_PROJECT_ID:-}"
SLACK_CHANNEL="${ZION_SLACK_CHANNEL:-#deployments}"
DRY_RUN="${DRY_RUN:-0}"
ACTION="${1:-deploy}"  # deploy | preview | status | rollback

log() {
    local level="$1"
    shift
    echo "[$timestamp] $msg"
}

check_env() {
    local missing=()
    [[ -z "$COMPOSIO_API_KEY" ]] && missing+=("COMPOSIO_API_KEY")
    [[ -z "$VERCEL_PROJECT" && -z "$VERCEL_PROJECT_ID" ]] && missing+=("VERCEL_PROJECT ou VERCEL_PROJECT_ID")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "❌ Variáveis faltando: ${missing[*]}"
        return 1
    fi
    return 0
}

get_sdk() {
    python - <<'PY'
import sys, os
sys.path.insert(0, '/Users/miami2/zion.app/automation/scripts')
from composio import Composio
sdk = Composio(api_key=os.environ.get("COMPOSIO_API_KEY", ""))
print(sdk)
PY
}

trigger_deploy() {
    echo "🚀 Triggering Vercel deploy for $PROJECT..."
    
    python - <<'PY' "$PROJECT" "$DRY_RUN"
import sys, os
from composio import Composio

project = sys.argv[1]
dry_run = sys.argv[2] == "--dry-run" if len(sys.argv) > 2 else False
api_key = os.environ.get("COMPOSIO_API_KEY", "")

if not api_key:
    print("❌ COMPOSIO_API_KEY não configurada")
    sys.exit(1)

sdk = Composio(api_key=api_key)

# Criar deployment via Vercel toolkit
result = sdk.tools.execute(
    "VERCEL_CREATE_DEPLOYMENT",
    arguments={
        "projectId": project,
        "clean": True,
    },
    user_id="zion-bot",
)

if result:
    deployment_url = result.get("url", result.get("deploymentUrl", "N/A"))
    deployment_id = result.get("id", result.get("deploymentId", "N/A"))
    print(f"✅ Deploy criado: {deployment_url}")
    print(f"   ID: {deployment_id}")
    
    # Salvar estado
    import json
    state = {
        "deployment_id": deployment_id,
        "url": deployment_url,
        "triggered_at": datetime.now().isoformat(),
        "project": project,
    }
    with open("/tmp/composio-vercel-deploy-state.json", "w") as f:
        json.dump(state, f, indent=2)
    
    # Slack notification
    slack_channel = os.environ.get("ZION_SLACK_CHANNEL", "#deployments")
    sdk.tools.execute(
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": slack_channel,
            "text": f"*🚀 Deploy Zion*\n\nProjeto: {project}\nStatus: Iniciado\nURL: {deployment_url}\nTempo: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        },
        user_id="zion-bot",
    )
    print(f"📤 Slack notificado em {slack_channel}")
else:
    print("❌ Falha ao criar deploy")
    sys.exit(1)
PY
}

check_status() {
    echo "🏥 Verificando status do último deploy..."
    
    python - <<'PY'
import os, json
from composio import Composio

api_key = os.environ.get("COMPOSIO_API_KEY", "")
project = os.environ.get("VERCEL_PROJECT", "zion-tech-group")

if not api_key:
    print("❌ COMPOSIO_API_KEY não configurada")
    sys.exit(1)

sdk = Composio(api_key=api_key)

result = sdk.tools.execute(
    "VERCEL_GET_DEPLOYMENTS",
    arguments={
        "projectId": project,
        "limit": 1,
    },
    user_id="zion-bot",
)

if result:
    deploys = result.get("deployments", [])
    if deploys:
        latest = deploys[0]
        print(f"\n📊 Status do último deploy:")
        print(f"   ID: {latest.get('id', 'N/A')}")
        print(f"   Status: {latest.get('status', 'N/A')}")
        print(f"   URL: {latest.get('url', 'N/A')}")
        print(f"   Created: {latest.get('createdAt', 'N/A')}")
        print(f"   Altura: {latest.get('alias, 'N/A')}")
        
        # Salvar estado
        state = {
            "deployment_id": latest.get("id"),
            "status": latest.get("status"),
            "url": latest.get("url"),
            "created_at": latest.get("createdAt"),
        }
        with open("/tmp/composio-vercel-status-state.json", "w") as f:
            json.dump(state, f, indent=2)
    else:
        print("   Sem deployments encontrados")
else:
    print("❌ Falha ao obter deployments")
    sys.exit(1)
PY
}

create_preview() {
    echo "👁️ Criando preview deployment..."
    
    python - <<'PY'
import os
from composio import Composio

project = os.environ.get("VERCEL_PROJECT", "zion-tech-group")
api_key = os.environ.get("COMPOSIO_API_KEY", "")

if not api_key:
    print("❌ COMPOSIO_API_KEY não configurada")
    sys.exit(1)

sdk = Composio(api_key=api_key)

result = sdk.tools.execute(
    "VERCEL_CREATE_DEPLOYMENT",
    arguments={
        "projectId": project,
        "id": "preview",  # ou branch name
        "clean": True,
    },
    user_id="zion-bot",
)

if result:
    preview_url = result.get("url", "N/A")
    print(f"✅ Preview criado: {preview_url}")
    
    # Slack notification
    slack_channel = os.environ.get("ZION_SLACK_CHANNEL", "#deployments")
    sdk.tools.execute(
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": slack_channel,
            "text": f"*👁️ Preview Deploy Zion*\n\nURL: {preview_url}\nBranch: preview\nTempo: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        },
        user_id="zion-bot",
    )
else:
    print("❌ Falha ao criar preview")
    sys.exit(1)
PY
}

main() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "=== $SCRIPT_NAME ($ACTION) ==="
    
    check_env || exit 1
    
    case $ACTION in
        deploy)
            trigger_deploy
            ;;
        preview)
            create_preview
            ;;
        status)
            check_status
            ;;
        rollback)
            echo "🔄 Rollback não implementado ainda"
            echo "Implementar com VERCEL_DELETE_DEPLOYMENT ou VERCEL_UPDATE_DEPLOYMENT"
            ;;
        *)
            echo "❌ Ação desconhecida: $ACTION"
            echo "Uso: $0 [deploy|preview|status|rollback]"
            exit 1
            ;;
    esac
    
    echo ""
    echo "=== Done ==="
}

main "$@"
