#!/usr/bin/env python3
"""
test_monkey_pty_integration.py — Integração do monkey.c com PTY real via write(2)
Versão: 2026-09-04 v4 — monkey self-contained (openpty interno) + worker cross-read
TUNABLE: delay do monkey e timeout do worker ajustados para garantir que
o worker tem tempo de ler o TEST_MESSAGE após a injeção.

Fluxo de validação:
1. monkey self-contained cria PTY via openpty() interno
2. monkey escreve slave_path no shm (/monkey_shm)
3. harness lê slave_path via monkey_ctrl
4. worker thread re-abre slave por path (via validada em pty_cross_test_v2.py)
5. monkey injeta via write(2) no master (TEST_MESSAGE após count >= 20)
6. worker recebe e verifica se TEST_MESSAGE chegou
7. status do monkey via /dev/shm (monkey_ctrl)

Pré-requisitos: monkey e monkey_ctrl compilados no diretório monkey/
Execução: python3 test_monkey_pty_integration.py
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
import time
import threading
from pathlib import Path

MONKEY_BIN = Path("./monkey")
MONKEY_CTRL_BIN = Path("./monkey_ctrl")

TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"


class WorkerResult:
    """Container thread-safe para resultado do worker."""

    def __init__(self):
        self.dados_lidos = b""
        self.success = False
        self.error = None
        self.output = ""

    def set_success(self, dados_lidos, output):
        self.dados_lidos = dados_lidos
        self.success = True
        self.output = output

    def set_failure(self, reason, output=""):
        self.success = False
        self.error = reason
        self.output = output


def worker_thread(slave_path, result_container):
    """Worker que re-abre o slave PTY por path e lê os dados injetados."""
    import select

    try:
        slave_fd2 = os.open(slave_path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"  [worker] slave re-aberto por path: fd={slave_fd2}, path={slave_path}", flush=True)

        dados_lidos = b""
        timeout_seg = 5.0  # TEMPO MAIS LONGO PARA LER APÓS INJEÇÃO
        inicio = time.monotonic()
        last_print = 0

        while time.monotonic() - inicio < timeout_seg:
            ready, _, _ = select.select([slave_fd2], [], [], 0.1)
            if ready:
                chunk = os.read(slave_fd2, 4096)
                if chunk:
                    dados_lidos += chunk
                    agora = time.monotonic()
                    if agora - last_print > 0.2:
                        print(f"  [worker] lido {len(chunk)} bytes (total: {len(dados_lidos)}): {chunk!r}", flush=True)
                        last_print = agora
                    if TEST_MESSAGE in dados_lidos:
                        break
                else:
                    break

        os.close(slave_fd2)

        output = []
        if TEST_MESSAGE in dados_lidos:
            output.append(f"  [worker] SUCESSO: TEST_MESSAGE encontrado nos dados lidos!")
            output.append(f"  [worker] dados completos: {dados_lidos!r}")
            result_container.set_success(dados_lidos, "\n".join(output))
            print("\n".join(output), flush=True)
        else:
            output.append(f"  [worker] FALHA: TEST_MESSAGE não encontrado.")
            output.append(f"  [worker] dados lidos: {dados_lidos!r}")
            output.append(f"  [worker] esperado contém: {TEST_MESSAGE!r}")
            result_container.set_failure("TEST_MESSAGE não encontrado nos dados", "\n".join(output))
            print("\n".join(output), flush=True)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        msg = f"  [worker] ERRO: {e}\n{tb}"
        result_container.set_failure(str(e), msg)
        print(msg, flush=True)


def read_slave_path_from_shm():
    """Lê slave_path do shm via monkey_ctrl. Retorna path ou None."""
    result = subprocess.run(
        [os.path.abspath(str(MONKEY_CTRL_BIN))],
        capture_output=True,
        text=True,
        timeout=5,
    )
    ctrl_out = result.stdout.strip()
    print(f"  monkey_ctrl stdout: {ctrl_out}")
    match = re.search(r'slave=(/dev/ttys\d+)', ctrl_out)
    if match:
        return match.group(1)
    return None


def main():
    print(f"=== Teste de Integração: monkey.c + PTY real (write(2)) ===")
    print(f"Diretório: {Path.cwd()}")
    print(f"monkey bin: {MONKEY_BIN} (exists: {MONKEY_BIN.exists()}, size: {MONKEY_BIN.stat().st_size if MONKEY_BIN.exists() else 'N/A'})")
    print(f"monkey_ctrl bin: {MONKEY_CTRL_BIN} (exists: {MONKEY_CTRL_BIN.exists()})")
    print(f"TEST_MESSAGE: {TEST_MESSAGE!r}")

    if not MONKEY_BIN.exists():
        print(f"ERRO: {MONKEY_BIN} não encontrado. Compile primeiro: gcc -o monkey monkey.c")
        return 1
    if not MONKEY_CTRL_BIN.exists():
        print(f"ERRO: {MONKEY_CTRL_BIN} não encontrado. Compile primeiro: gcc -o monkey_ctrl monkey_ctrl.c")
        return 1

    # 1. Iniciar monkey self-contained (ele cria seu próprio PTY via openpty interno)
    print(f"\n[1] Iniciando monkey self-contained (openpty interno)...")
    print(f"  TEST_MESSAGE a ser injetada: {TEST_MESSAGE!r}")
    print(f"  Delay: 200000µs (200ms) — TEST_MESSAGE injetado após count>=20 (~4s)")

    monkey_abs = os.path.abspath(str(MONKEY_BIN))
    try:
        monkey_proc = subprocess.Popen(
            [monkey_abs, "200000"],  # delay 200ms, monkey cria seu próprio PTY
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"  monkey iniciado: pid={monkey_proc.pid}")
        # Dar tempo para o monkey criar shm e PTY
        time.sleep(1.0)  # TEMPO MAIS LONGO PARA SHM e INICIALIZAÇÃO
        import select as _select
        stderr_chunks = []
        while True:
            ready, _, _ = _select.select([monkey_proc.stderr], [], [], 0.1)
            if ready:
                chunk = monkey_proc.stderr.read(4096)
                if chunk:
                    stderr_chunks.append(chunk)
                else:
                    break
            else:
                break
        if stderr_chunks:
            print(f"  [monkey] stderr: {''.join(stderr_chunks)!r}")
    except Exception as e:
        print(f"ERRO ao iniciar monkey: {e}")
        return 1

    # 2. Ler slave_path do shm via monkey_ctrl
    print(f"\n[2] Lendo slave_path do shm via monkey_ctrl...")
    slave_path_from_monkey = read_slave_path_from_shm()

    if not slave_path_from_monkey:
        print(f"  ERRO: não pôde extrair slave_path do shm")
        monkey_proc.terminate()
        monkey_proc.wait(timeout=2)
        return 1

    print(f"  slave_path detectado: {slave_path_from_monkey}")

    # 3. Worker que re-abre slave por path — em THREAD (não bloqueia)
    print(f"\n[3] Iniciando worker (thread, re-abre slave por path)...")
    result_container = WorkerResult()

    worker = threading.Thread(
        target=worker_thread,
        args=(slave_path_from_monkey, result_container),
        name="pty-worker",
        daemon=True,
    )
    worker.start()

    # Dar tempo para o worker iniciar e abrir o slave
    time.sleep(0.1)  # TEMPO MENOR PARA INICIAÇÃO DO WORKER

    # 4. Dar tempo para monkey injetar dados (TEMPO MAIS LONGO)
    print("  Aguardando monkey injetar dados (5.0 segundos)...")
    time.sleep(5.0)  # TEMPO MAIS LONGO PARA INJEÇÃO

    # 5. Verificar status do monkey via /dev/shm usando monkey_ctrl
    print(f"\n[5] Verificando status do monkey via monkey_ctrl...")
    try:
        result = subprocess.run(
            [os.path.abspath(str(MONKEY_CTRL_BIN))],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print(f"  monkey_ctrl stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"  monkey_ctrl stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  monkey_ctrl: timeout (monkey pode estar ocupado)")
    except Exception as e:
        print(f"  monkey_ctrl: erro = {e}")

    # 6. Parar monkey
    print(f"\n[6] Parando monkey...")
    monkey_proc.terminate()
    try:
        monkey_proc.wait(timeout=3)
        print(f"  monkey encerrado (exitcode: {monkey_proc.returncode})")
    except subprocess.TimeoutExpired:
        print("  monkey não respondeu ao SIGTERM, enviando SIGKILL...")
        monkey_proc.kill()
        monkey_proc.wait(timeout=2)
        print(f"  monkey killado (exitcode: {monkey_proc.returncode})")

    # 7. Aguardar worker finalizar
    print(f"\n[7] Aguardando worker finalizar...")
    worker.join(timeout=3)
    if worker.is_alive():
        print("  Worker ainda ativo após timeout — finalizando de qualquer forma")
    else:
        print(f"  Worker finalizado")

    # 8. Resultado final
    print(f"\n=== RESULTADO ===")
    if result_container.success:
        print("✅ SUCESSO: monkey injetou dados via write(2) no PTY master e worker os leu!")
        print(f"   Slave path (do shm): {slave_path_from_monkey}")
        print(f"   TEST_MESSAGE: {TEST_MESSAGE!r}")
        print(f"   Dados lidos: {result_container.dados_lidos!r}")
        return 0
    else:
        print("❌ FALHA: worker não conseguiu ler TEST_MESSAGE injetado pelo monkey.")
        if result_container.error:
            print(f"   Erro: {result_container.error}")
        print(f"   Worker output:\n{result_container.output}")
        print(f"   slave_path (do shm): {slave_path_from_monkey}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
