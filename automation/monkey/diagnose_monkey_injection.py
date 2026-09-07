#!/usr/bin/env python3
"""
diagnose_monkey_injection.py — Diagnóstico direto: verifica se monkey injeta
TEST_MESSAGE no PTY e se um worker pode ler.

Executar NO MAC:
    python3 diagnose_monkey_injection.py
"""
from __future__ import annotations
import os
import re
import select
import subprocess
import sys
import threading
import time
from pathlib import Path

MONKEY_BIN = Path("/Users/miami2/zion.app/automation/monkey/monkey")
MONKEY_CTRL_BIN = Path("/Users/miami2/zion.app/automation/monkey/monkey_ctrl")
TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"

def run(*args: str) -> tuple[str, str, int]:
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(timeout=10)
    return out, err, p.returncode

def get_slave_path() -> str | None:
    if not MONKEY_CTRL_BIN.exists():
        print("❌ monkey_ctrl não encontrado"); return None
    out, err, rc = run(str(MONKEY_CTRL_BIN))
    if rc != 0:
        print(f"❌ monkey_ctrl falhou (rc={rc}): {err}"); return None
    m = re.search(r"slave=(/dev/ttys\d+)", out)
    if not m:
        print(f"❌ slave path não encontrado no shm:\n{out}"); return None
    return m.group(1)

def main() -> None:
    print("=== Diagnóstico de Injeção Monkey ===")
    print(f"monkey: {MONKEY_BIN} (exists: {MONKEY_BIN.exists()})")
    print(f"monkey_ctrl: {MONKEY_CTRL_BIN} (exists: {MONKEY_CTRL_BIN.exists()})")
    print(f"TEST_MESSAGE: {TEST_MESSAGE!r}")
    print()

    # 1. Iniciar monkey
    print("[1] Iniciando monkey com delay=50000µs (0.05s)...")
    try:
        monkey = subprocess.Popen([str(MONKEY_BIN), "50000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"    PID: {monkey.pid}")
    except Exception as e:
        print(f"❌ Falha ao iniciar monkey: {e}"); return

    try:
        # 2. Aguardar TEST_MESSAGE ser injetado (delay 50ms * 20 = 1s)
        print("[2] Aguardando injeção do TEST_MESSAGE (~3 segundos)...")
        time.sleep(3)

        # 3. Ler shm
        print("[3] Lendo shm via monkey_ctrl...")
        out, err, rc = run(str(MONKEY_CTRL_BIN))
        print(f"    stdout: {out.strip()!r}")
        print(f"    rc: {rc}")
        if "TEST_MESSAGE injected" in out:
            print("    ✅ TEST_MESSAGE injetado (conforme shm)")
        else:
            print("    ❌ TEST_MESSAGE NÃO encontrado no shm")
        slave = get_slave_path()
        if not slave:
            print("❌ Não foi possível obter slave_path"); return
        print(f"    slave_path: {slave}")

        # 4. Ler do slave diretamente
        print(f"[4] Lendo do slave {slave} diretamente...")
        try:
            fd = os.open(slave, os.O_RDONLY | os.O_NONBLOCK)
        except Exception as e:
            print(f"❌ Falha ao abrir slave {slave}: {e}"); return

        try:
            # Ler até encontrar TEST_MESSAGE ou timeout
            all_data = bytearray()
            start = time.time()
            found = False
            while time.time() - start < 5.0:
                ready, _, _ = select.select([fd], [], [], 0.5)
                if ready:
                    try:
                        chunk = os.read(fd, 4096)
                        if not chunk:
                            break
                        all_data.extend(chunk)
                        if TEST_MESSAGE in all_data:
                            found = True
                            print(f"    ✅ TEST_MESSAGE encontrado após {len(all_data)} bytes lidos!")
                            print(f"    Dados ao redor: {all_data[max(0, all_data.index(TEST_MESSAGE)-20):all_data.index(TEST_MESSAGE)+len(TEST_MESSAGE)+20]!r}")
                            break
                    except BlockingIOError:
                        pass
                if time.time() - start > 4.5:
                    print(f"    ⏱️  Timeout após 5s, {len(all_data)} bytes lidos sem TEST_MESSAGE")
                    print(f"    Últimos 200 bytes: {all_data[-200:]!r}")
                    break
            if not found:
                print(f"    ❌ TEST_MESSAGE NÃO encontrado nos dados lidos")
                print(f"    Total lido: {len(all_data)} bytes")
                # Mostrar os dados completos para análise
                print(f"    Dados completos: {bytes(all_data)!r}")
        finally:
            os.close(fd)

        # 5. Status final
        print("[5] Status final do monkey...")
        out, err, rc = run(str(MONKEY_CTRL_BIN))
        print(f"    {out.strip()}")

    finally:
        # Parar monkey
        print("[6] Parando monkey...")
        monkey.terminate()
        try:
            monkey.wait(timeout=3)
            print(f"    Exit code: {monkey.returncode}")
        except subprocess.TimeoutExpired:
            monkey.kill()
            monkey.wait()
            print("    ⚠️  Forçado com kill")

    print()
    if "TEST_MESSAGE injected" in out or found:
        print("✅ DIAGNÓSTICO: Injeção funciona, problema pode ser no reader do harness")
    else:
        print("❌ DIAGNÓSTICO: monkey.c não está injetando TEST_MESSAGE corretamente — precisamos investigar o código")

if __name__ == "__main__":
    main()
