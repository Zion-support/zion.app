#!/usr/bin/env bash
#===============================================================================
# composio-orchestrator.sh — Master Runner para Automação Composio do Zion
#===============================================================================
# Executa todos os scripts Composio em sequência, gerenciando estado, logs e relatórios consolidados.
#
# Scripts executados (ordem prioritária):
#   1. composio-daily-digest.py          — Daily Status Digest (GitHub+Slack+Linear+PostHog+Sentry+Vercel)
#   2. composio-release-automation.sh     — Release Automation (Trigger: PR merged)
#   3. composio-lead-intelligence-pipeline.py — Lead Intelligence (Firecrawl+Perplexity+HubSpot+Notion+Linear)
#   4. composio-lead-auto-reply.py        — Auto-Triage + Auto-Reply (Gmail+HubSpot+Notion+Linear)
#   5. composio-devops-event-agent.py     — Event-Driven Agent (PR merge, Sentry, PostHog, Vercel)
#
# Uso:
#   ./composio-orchestrator.sh                  # Executa tudo
#   ./composio-orchestrator.sh --only daily     # Só daily digest
#   ./composio-orchestrator.sh --only leads    # Só intelligence + auto-reply
#   ./composio-orchestrator.sh --only devops   # Só event agent + release
#   ./composio-orchestrator.sh --dry-run        # Simula sem executar
#   ./composio-orchestrator.sh --report         # Gera relatório consolidado
#
# Variáveis de ambiente:
#   COMPOSIO_API_KEY, ZION_GITHUB_OWNER, ZION_GITHUB_REPO, ZION_VERCEL_PROJECT,
#   ZION_SLACK_CHANNEL, POSTHOG_API_KEY, POSTHOG_URL, ZION_PROSPECT_URLS,
#   ZION_NOTION_DB_ID, ZION_LINEAR_TEAM_ID, ZION_GMAIL_LABEL_PROCESSING,
#   GITHUB_OWNER, GITHUB_REPO, VERCEL_PROJECT, SLACK_CHANNEL,
#   COMPOSIO_WEBHOOK_URL, COMPOSIO_WEBHOOK_SECRET
#===============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="/Users/miami2/zion.app"
SCRIPTS_DIR="$ROOT_DIR/automation/scripts"
STATE_DIR="/tmp/composio-orchestrator-state"
REPORT_FILE="/tmp/composio-orchestrator-report.json"

# Priority-ordered script list
declare -A SCRIPT_INFO
SCRIPT_INFO[daily]="name: Daily Digest | file: composio-daily-digest.py | priority: P0"
SCRIPT_INFO[release]="name: Release Automation | file: composio-release-automation.sh | priority: P0"
SCRIPT_INFO[leads]="name: Lead Intelligence Pipeline | file: composio-lead-intelligence-pipeline.py | priority: P1"
SCRIPT_INFO[auto_reply]="name: Lead Auto-Reply | file: composio-lead-auto-reply.py | priority: P1"
SCRIPT_INFO[devops]="name: DevOps Event Agent | file: composio-devops-event-agent.py | priority: P2"

PRIORITY_ORDER=(daily release leads auto_reply devops)

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#========== CONFIG ==========

VERBOSE=0
DRY_RUN=0
REPORT_MODE=0
ONLY_LIST=()
SKIP_LIST=()

# Parse args
for arg in "$@"; do
    case $arg in
        --verbose|-v) VERBOSE=1 ;;
        --dry-run|-n) DRY_RUN=1 ;;
        --report|-r) REPORT_MODE=1 ;;
        --only)
            shift
            IFS=',' read -ra ONLY_LIST <<< "$1"
            ;;
        --skip)
            shift
            IFS=',' read -ra SKIP_LIST <<< "$1"
            ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

#========== FUNÇÕES ==========

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)  echo -e "${BLUE}[$timestamp]${NC} $msg" ;;
        OK)    echo -e "${GREEN}[$timestamp]${NC} ✅ $msg" ;;
        WARN)  echo -e "${YELLOW}[$timestamp]${NC} ⚠️  $msg" ;;
        ERR)   echo -e "${RED}[$timestamp]${NC} ❌ $msg" ;;
        DEBUG) [[ $VERBOSE -eq 1 ]] && echo -e "${YELLOW}[$timestamp]${NC} 🔍 $msg" ;;
    esac
}

run_script() {
    local name="$1"
    local script_path="$2"
    local is_python="$3"
    
    log INFO "Executando: $name"
    
    if [[ $DRY_RUN -eq 1 ]]; then
        log WARN "Dry-run: não executando $name"
        return 0
    fi
    
    if [[ ! -f "$script_path" ]]; then
        log ERR "Script não encontrado: $script_path"
        return 1
    fi
    
    local start_time=$(date +%s)
    local output_file="/tmp/composio-orchestrator-${name}.log"
    
    if [[ $is_python -eq 1 ]]; then
        python "$script_path" > "$output_file" 2>&1
    else
        bash "$script_path" > "$output_file" 2>&1
    fi
    
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $exit_code -eq 0 ]]; then
        log OK "$name concluído em ${duration}s"
        [[ $VERBOSE -eq 1 ]] && cat "$output_file" | tail -5
        return 0
    else
        log ERR "$name falhou (exit $exit_code) em ${duration}s"
        [[ $VERBOSE -eq 1 ]] && cat "$output_file" | tail -10
        return 1
    fi
}

should_run() {
    local name="$1"
    
    # Check skip list
    for skip in "${SKIP_LIST[@]}"; do
        if [[ "$name" == "$skip" ]]; then
            return 1
        fi
    done
    
    # Check only list
    if [[ ${#ONLY_LIST[@]} -gt 0 ]]; then
        local found=0
        for only in "${ONLY_LIST[@]}"; do
            if [[ "$name" == "$only" ]]; then
                found=1
                break
            fi
        done
        if [[ $found -eq 0 ]]; then
            return 1
        fi
    fi
    
    return 0
}

generate_report() {
    log INFO "Gerando relatório consolidado..."
    
    local report_json="{\n"
    report_json+="  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\n"
    report_json+="  \"mode\": \"$(if [[ $DRY_RUN -eq 1 ]]; then echo 'dry-run'; else echo 'live'; fi)\",\n"
    report_json+="  \"scripts\": [\n"
    
    local first=1
    for name in "${PRIORITY_ORDER[@]}"; do
        local script_path=""
        local is_python=0
        
        case $name in
            daily) script_path="$SCRIPTS_DIR/composio-daily-digest.py"; is_python=1 ;;
            release) script_path="$SCRIPTS_DIR/composio-release-automation.sh"; is_python=0 ;;
            leads) script_path="$SCRIPTS_DIR/composio-lead-intelligence-pipeline.py"; is_python=1 ;;
            auto_reply) script_path="$SCRIPTS_DIR/composio-lead-auto-reply.py"; is_python=1 ;;
            devops) script_path="$SCRIPTS_DIR/composio-devops-event-agent.py"; is_python=1 ;;
        esac
        
        if [[ $first -eq 0 ]]; then
            report_json+=",\n"
        fi
        first=0
        
        local state_file="/tmp/composio-orchestrator-${name}-state.json"
        
        report_json+="    {\n"
        report_json+="      \"name\": \"$name\",\n"
        report_json+="      \"path\": \"$script_path\",\n"
        report_json+="      \"status\": \"$(if should_run "$name"; then echo 'scheduled'; else echo 'skipped'; fi)\",\n"
        report_json+="      \"priority\": \"${SCRIPT_INFO[$name]}\"\n"
        report_json+="    }"
    done
    
    report_json+="\n  ]\n"
    report_json+="}\n"
    
    echo -e "$report_json" > "$REPORT_FILE"
    log OK "Relatório gerado: $REPORT_FILE"
}

#========== PRÉ-TESTES ==========

check_composio_key() {
    if [[ -z "${COMPOSIO_API_KEY:-}" ]]; then
        log WARN "COMPOSIO_API_KEY não configurada — scripts que exigem Composio podem falhar"
        log INFO "Configure com: export COMPOSIO_API_KEY='sk_...'"
        return 1
    fi
    return 0
}

check_dependencies() {
    local missing=()
    
    if ! command -v python &> /dev/null; then
        missing+=("python")
    fi
    
    if ! command -v bash &> /dev/null; then
        missing+=("bash")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERR "Dependências faltando: ${missing[*]}"
        return 1
    fi
    
    return 0
}

#========== MAIN ==========

main() {
    log INFO "=== Composio Orchestrator starting ==="
    log INFO "Mode: $(if [[ $DRY_RUN -eq 1 ]]; then echo 'DRY-RUN'; else echo 'LIVE'; fi)"
    log INFO "Only: ${ONLY_LIST[*]:-all}"
    log INFO "Skip: ${SKIP_LIST[*]:-none}"
    
    # Pre-checks
    check_dependencies || exit 1
    check_composio_key || true  # não é fatal, alguns scripts podem funcionar sem
    
    # Create state dir
    mkdir -p "$STATE_DIR"
    
    # Generate pre-run report
    if [[ $REPORT_MODE -eq 1 ]]; then
        generate_report
        log INFO "Apenas relatório — encerrando"
        return 0
    fi
    
    # Execute scripts in priority order
    local failed=0
    local executed=0
    
    for name in "${PRIORITY_ORDER[@]}"; do
        if should_run "$name"; then
            local script_path=""
            local is_python=0
            
            case $name in
                daily) script_path="$SCRIPTS_DIR/composio-daily-digest.py"; is_python=1 ;;
                release) script_path="$SCRIPTS_DIR/composio-release-automation.sh"; is_python=0 ;;
                leads) script_path="$SCRIPTS_DIR/composio-lead-intelligence-pipeline.py"; is_python=1 ;;
                auto_reply) script_path="$SCRIPTS_DIR/composio-lead-auto-reply.py"; is_python=1 ;;
                devops) script_path="$SCRIPTS_DIR/composio-devops-event-agent.py"; is_python=1 ;;
            esac
            
            run_script "$name" "$script_path" "$is_python"
            local rc=$?
            if [[ $rc -eq 0 ]]; then
                ((executed++))
            else
                ((failed++))
            fi
        else
            log DEBUG "Pulando: $name"
        fi
    done
    
    # Summary
    log INFO "=== Resumo ==="
    log OK "Executados: $executed"
    [[ $failed -gt 0 ]] && log ERR "Falhados: $failed"
    
    if [[ $failed -gt 0 ]]; then
        log WARN "Alguns scripts falharam — verificar logs em /tmp/composio-orchestrator-*.log"
    fi
    
    # Generate post-run report if not just report mode
    if [[ $REPORT_MODE -eq 0 ]]; then
        generate_report
    fi
    
    log INFO "=== Orchestrator complete ==="
}

main "$@"
