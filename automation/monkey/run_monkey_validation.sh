#!/bin/bash
# run_monkey_validation.sh
# Executar NO MAC (Miami2-5.local) e colar saída aqui.
# testa end-to-end: monkey self-contained + shm + worker cross-read

set -eo pipefail
WORKDIR="/Users/miami2/zion.app/automation/monkey"
LOGDIR="/Users/miami2/zion.app/automation/logs"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/monkey_validation_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOGFILE") 2>&1

echo "=== Início validação Monkey Typing ==="
echo "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Host: $(hostname)"
echo "Usuário: $(whoami)"
echo ""

cd "$WORKDIR"

echo "--- 1. Arquivos no diretório ---"
ls -la monkey.c monkey_ctrl.c test_monkey_pty_integration.py pty_cross_test_v2.py 2>&1 || true
echo ""

echo "--- 2. Compilação monkey.c ---"
rm -f monkey monkey_ctrl
gcc -o monkey monkey.c && echo "monkey.c: OK"
echo ""

echo "--- 3. Compilação monkey_ctrl.c ---"
gcc -o monkey_ctrl monkey_ctrl.c && echo "monkey_ctrl.c: OK"
echo ""

echo "--- 4. Verificar binaries ---"
ls -la monkey monkey_ctrl
file monkey monkey_ctrl
echo ""

echo "--- 5. Executar test_monkey_pty_integration.py ---"
rm -f /monkey_shm
python3 test_monkey_pty_integration.py 2>&1
INTEGRATION_EXIT=$?
echo ""
echo "EXIT_CODE integracao: $INTEGRATION_EXIT"
echo ""

echo "--- 6. hexdump shm após execução ---"
if [ -e /monkey_shm ]; then
    hexdump -C /monkey_shm 2>/dev/null | head -30 || echo "hexdump não disponível"
else
    echo "shm não encontrado (monkey pode ter unlinkado)"
fi
echo ""

echo "=== Fim validação Monkey Typing ==="
echo "Log salvo em: $LOGFILE"
