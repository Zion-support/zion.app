#!/bin/bash
# Monkey Typing — Teste de shared memory via monkey_ctrl
# Valida shm_open/mmap no macOS sem exigir PTY

set -e
cd /Users/miami2/zion.app/automation/monkey

echo "=== Teste 1: leitura do shm antes de qualquer monkey rodando ==="
output=$(./monkey_ctrl 2>&1) || true
echo "Saída: $output"

echo ""
echo "=== Teste 2: escrita via monkey_ctrl ==="
./monkey_ctrl "status:test_write_ok"
echo "(escrito)"

echo ""
echo "=== Teste 3: leitura após escrita ==="
./monkey_ctrl
