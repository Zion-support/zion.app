#!/bin/bash
# Teste de shm: monkey cria shm com /dev/null como PTY fallback
# monkey_ctrl lê + escreve no shm
cd /Users/miami2/zion.app/automation/monkey

echo "=== Teste de shm: criação via monkey + leitura controladora ==="
./monkey /dev/null 50000 &
monkey_pid=$!
sleep 0.5
./monkey_ctrl
kill $monkey_pid 2>/dev/null || true
wait $monkey_pid 2>/dev/null || true

echo ""
echo "=== Teste 2: escrita e leitura via monkey_ctrl ==="
./monkey_ctrl "status:shm_test_complete"
./monkey_ctrl
