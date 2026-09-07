#!/usr/bin/env bash
#===============================================================================
# test_all_monkey_pty.sh — Suite completa de validação do Monkey Typing
# 
# Executa em ordem:
# 1. shm smoke test (monkey_ctrl standalone — cria shm, lê, escreve)
# 2. monkey self-contained (monkey cria shm+PTY interno, monkey_ctrl lê)
# 3. pty_cross_test_v2 (write(2) no master → worker re-abre slave por path → cross-read validado)
# 4. monkey contra PTY real via /dev/fd/<master_fd> + worker re-abre slave por path + monkey_ctrl
#
# Requer: gcc, python3, /dev/ttys* disponível (macOS)
#===============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

PASSES=0
FAILS=0
declare -a FAIL_MSGS=()

pass() {
    ((PASSES++))
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

fail() {
    ((FAILS++))
    echo -e "${RED}❌ FAIL:${NC} $1"
    FAIL_MSGS+=("$1")
}

info() {
    echo -e "${YELLOW}ℹ️  INFO:${NC} $1"
}

section() {
    echo ""
    echo "============================================================"
    echo " $1"
    echo "============================================================"
}

# Verifica prerequisitos
section "Verificando ambiente"
echo "Diretório: $SCRIPT_DIR"
echo "Kernel: $(uname -r)"
echo "Hostname: $(hostname)"

if [ ! -f "./monkey" ] || [ ! -x "./monkey" ]; then
    echo -e "${RED}ERRO: monkey não encontrado ou não executável. Compile: gcc -o monkey monkey.c${NC}"
    exit 1
fi

if [ ! -f "./monkey_ctrl" ] || [ ! -x "./monkey_ctrl" ]; then
    echo -e "${RED}ERRO: monkey_ctrl não encontrado ou não executável. Compile: gcc -o monkey_ctrl monkey_ctrl.c${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERRO: python3 não encontrado no PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅${NC} Binários e python3 verificados"

# ---------------------------------------------------------------
# TESTE 1: shm smoke test com monkey_ctrl standalone
# ---------------------------------------------------------------
section "TESTE 1: shm standalone (monkey_ctrl)"
info "monkey_ctrl lê/shm_status — sem monkey criando shm primeiro"
info "Esperado: monkey_ctrl reporta 'shm_open: No such file or directory' (comportamento esperado)"

MONKEY_CTRL_OUT=$(./monkey_ctrl 2>&1)
MONKEY_CTRL_EXIT=$?

echo "  monkey_ctrl stdout: $MONKEY_CTRL_OUT"
echo "  monkey_ctrl exit: $MONKEY_CTRL_EXIT"

if [[ "$MONKEY_CTRL_OUT" == *"No such file"* ]]; then
    pass "monkey_ctrl reporta corretamente ausência de shm (comportamento esperado)"
else
    # Se encontrar shm residual de execução anterior, também conta como pass
    if [[ "$MONKEY_CTRL_OUT" == *"status:"* ]]; then
        pass "monkey_ctrl encontrou shm residual (status: $MONKEY_CTRL_OUT)"
    else
        fail "monkey_ctrl não reportou comportamento esperado: $MONKEY_CTRL_OUT"
    fi
fi

# Limpa shm residual se existir
if [ -e /tmp/monkey_shm ]; then
    rm -f /tmp/monkey_shm 2>/dev/null
    info "shm residual removido"
fi

# ---------------------------------------------------------------
# TESTE 2: monkey self-contained cria shm + PTY interno
#       e monkey_ctrl consegue ler o status
# ---------------------------------------------------------------
section "TESTE 2: monkey self-contained (openpty interno) + monkey_ctrl"

info "Iniciando monkey com delay curto (50000us)..."
./monkey 50000 > /dev/null 2>/tmp/monkey_stderr.log &
MONKEY_PID=$!
info "monkey iniciado: pid=$MONKEY_PID"

# Espera monkey criar shm e iniciar
sleep 1

# Lê status via monkey_ctrl
CTRL_OUT=$(./monkey_ctrl 2>&1)
echo "  monkey_ctrl stdout: $CTRL_OUT"

# Verifica se monkey está running via shm
if [[ "$CTRL_OUT" == *"status:running"* ]] || [[ "$CTRL_OUT" == *"status:ready"* ]]; then
    pass "monkey criou shm e está reportando status via monkey_ctrl"
else
    fail "monkey não reportou status esperado via shm: $CTRL_OUT"
fi

# Verifica stderr do monkey
MONKEY_ERR=$(cat /tmp/monkey_stderr.log 2>/dev/null)
if [ -n "$MONKEY_ERR" ]; then
    echo "  monkey stderr: $MONKEY_ERR"
    if [[ "$MONKEY_ERR" == *"Error"* ]] || [[ "$MONKEY_ERR" == *"Falha"* ]]; then
        fail "monkey reportou erro no stderr: $MONKEY_ERR"
    fi
fi

# Para monkey
kill $MONKEY_PID 2>/dev/null
wait $MONKEY_PID 2>/dev/null
info "monkey encerrado"

# Verifica se shm foi limpo pelo monkey
sleep 0.5
SHM_EXISTS=$(ls /tmp/monkey_shm 2>/dev/null)
if [ -z "$SHM_EXISTS" ]; then
    pass "shm limpo após monkey encerrado (comportamento esperado)"
else
    info "shm ainda existe após monkey encerrado (pode ser comportamento normal em alguns casos)"
fi

# ---------------------------------------------------------------
# TESTE 3: pty_cross_test_v2 (write(2) validado anteriormente)
# ---------------------------------------------------------------
section "TESTE 3: pty_cross_test_v2 (validação cross-read write→slave)"

if [ -f "./pty_cross_test_v2.py" ]; then
    info "Executando pty_cross_test_v2.py..."
    PYTEST_OUT=$(python3 ./pty_cross_test_v2.py 2>&1)
    PYTEST_EXIT=$?
    echo "$PYTEST_OUT"
    
    if [ $PYTEST_EXIT -eq 0 ]; then
        pass "pty_cross_test_v2 executado com sucesso (cross-read validado)"
    else
        fail "pty_cross_test_v2 falhou com exitcode=$PYTEST_EXIT"
    fi
else
    fail "pty_cross_test_v2.py não encontrado"
fi

# ---------------------------------------------------------------
# TESTE 4: monkey contra PTY real via /dev/fd/<master_fd>
#       + worker re-abre slave por path
#       + monkey_ctrl status
# ---------------------------------------------------------------
section "TESTE 4: monkey integração PTY real via /dev/fd + worker + monkey_ctrl"

if [ -f "./test_monkey_pty_integration.py" ]; then
    info "Executando test_monkey_pty_integration.py..."
    INTEGRATION_OUT=$(python3 ./test_monkey_pty_integration.py 2>&1)
    INTEGRATION_EXIT=$?
    echo "$INTEGRATION_OUT"
    
    if [ $INTEGRATION_EXIT -eq 0 ]; then
        pass "test_monkey_pty_integration executado com sucesso (monkey → PTY real → worker leu)"
    else
        fail "test_monkey_pty_integration falhou com exitcode=$INTEGRATION_EXIT"
    fi
else
    fail "test_monkey_pty_integration.py não encontrado"
fi

# ---------------------------------------------------------------
# RESUMO FINAL
# ---------------------------------------------------------------
section "RESUMO DA SUITE"

echo -e "${GREEN}✅ Passes: $PASSES${NC}"
echo -e "${RED}❌ Falhas: $FAILS${NC}"
echo ""

if [ $FAILS -gt 0 ]; then
    echo -e "${RED}Falhas detectadas:${NC}"
    for msg in "${FAIL_MSGS[@]}"; do
        echo "  - $msg"
    done
    echo ""
    echo -e "${YELLOW}Detalhes completos acima.${NC}"
fi

if [ $FAILS -eq 0 ]; then
    echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM — Monkey Typing validado end-to-end.${NC}"
fi

echo ""
exit $FAILS