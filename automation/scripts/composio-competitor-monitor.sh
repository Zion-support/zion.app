#!/usr/bin/env bash
#===============================================================================
# composio-competitor-monitor.sh — Growth Competitor Watch Agent
#===============================================================================
# Monitora sites de concorrentes com Firecrawl + Browser Tool,
# analisa mudanças com Perplexity AI, e notifica no Slack + Notion.
#
# Uso:
#   export COMPOSIO_API_KEY="sk_..."
#   export ZION_PROSPECT_URLS="https://concorrente1.com,https://concorrente2.com"
#   export ZION_SLACK_CHANNEL="#growth"
#   export ZION_NOTION_DB_ID="..."
#   ./composio-competitor-monitor.sh
#   ./composio-competitor-monitor.sh --dry-run
#===============================================================================

set -uo pipefail

SCRIPT_NAME="composio-competitor-monitor"
SCRIPT_DIR="/Users/miami2/zion.app/automation/scripts"

PROSPECT_URLS="${ZION_PROSPECT_URLS:-}"
SLACK_CHANNEL="${ZION_SLACK_CHANNEL:-#growth}"
NOTION_DB_ID="${ZION_NOTION_DB_ID:-}"
DRY_RUN="${DRY_RUN:-0}"

STATE_FILE="/tmp/composio-competitor-monitor-state.json"
PYTHON="$SCRIPT_DIR/composio-competitor-monitor.py"

#========== FUNÇÕES ==========

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)  echo "[$timestamp] 📡 $msg" ;;
        OK)    echo "[$timestamp] ✅ $msg" ;;
        WARN)  echo "[$timestamp] ⚠️  $msg" ;;
        ERR)   echo "[$timestamp] ❌ $msg" ;;
    esac
}

check_env() {
    local missing=()
    
    [[ -z "$COMPOSIO_API_KEY" ]] && missing+=("COMPOSIO_API_KEY")
    [[ -z "$PROSPECT_URLS" ]] && missing+=("ZION_PROSPECT_URLS")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERR "Variáveis faltando: ${missing[*]}"
        log INFO "Configure antes de rodar:"
        for var in "${missing[@]}"; do
            echo "  export $var='...'"
        done
        return 1
    fi
    
    return 0
}

#========== MAIN ==========

main() {
    log INFO "=== Competitor Monitor starting ==="
    
    check_env || exit 1
    
    if [[ ! -f "$SCRIPT_DIR/composio-competitor-monitor.py" ]]; then
        log ERR "Script Python não encontrado: composio-competitor-monitor.py"
        log INFO "Criar em: $SCRIPT_DIR/composio-competitor-monitor.py"
        exit 1
    fi
    
    if [[ $DRY_RUN -eq 1 ]]; then
        log WARN "Dry-run: não executando monitoramento"
        exit 0
    fi
    
    log INFO "Iniciando monitoramento de concorrentes..."
    log INFO "URLs monitoradas: $PROSPECT_URLS"
    log INFO "Slack channel: $SLACK_CHANNEL"
    
    python "$SCRIPT_DIR/composio-competitor-monitor.py"
    local rc=$?
    
    if [[ $rc -eq 0 ]]; then
        log OK "Competitor monitor concluído"
    else
        log ERR "Competitor monitor falhou (exit $rc)"
    fi
    
    exit $rc
}

main "$@"
