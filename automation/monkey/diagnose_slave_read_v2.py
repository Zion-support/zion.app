#!/usr/bin/env python3
"""
diagnose_slave_read_v2.py — Testa se o worker consegue ler TEST_MESSAGE do slave
usando subprocess.run para maior confiabilidade.
"""
from __future__ import annotations
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

MONKEY_BIN = Path("/Users/miami2/zion.app/automation/monkey/monkey")
MONKEY_CTRL_BIN = Path("/Users/miami2/zion.app/automation/monkey/monkey_ctrl")
TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"


def run_monkey_ctrl():
    """Lê shm via monkey_ctrl e retorna stdout."""
    try:
        result = subprocess.run(
            [str(MONKEY_CTRL_BIN)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1
    except Exception as e:
        return "", str(e), -1


def main():
    print("=== Diagnóstico v2: leitura do slave após injeção ===")
    
    # 1. Iniciar monkey
    print("[1] Iniciando monkey...")
    monkey = subprocess.Popen([str(MONKEY_BIN), "50000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"    PID: {monkey.pid}")
    time.sleep(0.5)  # esperar shm
    
    try:
        # 2. Ler shm até TEST_MESSAGE injetado
        print("[2] Aguardando injeção do TEST_MESSAGE...")
        slave_path = None
        start = time.time()
        attempt = 0
        while time.time() - start < 10:
            attempt += 1
            out, err, rc = run_monkey_ctrl()
            print(f"    Tentativa {attempt}: rc={rc}, stdout={out.strip()!r}")
            if "TEST_MESSAGE injected" in out:
                print("    ✅ TEST_MESSAGE injetado confirmado no shm")
                # Extrair slave_path
                m = re.search(r"slave=(/dev/ttys\d+)", out)
                if m:
                    slave_path = m.group(1)
                    print(f"    slave_path: {slave_path}")
                break
            time.sleep(0.3)
        
        if not slave_path:
            print("❌ TEST_MESSAGE não foi injetado dentro do timeout")
            print(f"    Último stdout: {out!r}")
            monkey.terminate()
            return 1
        
        # 3. Ler do slave e verificar TEST_MESSAGE
        print(f"[3] Lendo do slave {slave_path}...")
        
        all_data = bytearray()
        fd = os.open(slave_path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            t0 = time.time()
            while time.time() - t0 < 3.0:
                ready, _, _ = select.select([fd], [], [], 0.3)
                if ready:
                    try:
                        chunk = os.read(fd, 4096)
                        if not chunk:
                            break
                        all_data.extend(chunk)
                        print(f"    Lido {len(chunk)} bytes (total: {len(all_data)})")
                        if TEST_MESSAGE in all_data:
                            print(f"    ✅ TEST_MESSAGE encontrado!")
                            idx = all_data.index(TEST_MESSAGE)
                            print(f"    Contexto: ...{all_data[max(0,idx-30):idx+len(TEST_MESSAGE)+30]}...")
                            break
                    except Exception as e:
                        print(f"    Erro ao ler: {e}")
                        break
        finally:
            os.close(fd)
        
        if TEST_MESSAGE not in all_data:
            print(f"    ❌ TEST_MESSAGE não encontrado. Total lido: {len(all_data)} bytes")
            if len(all_data) > 0:
                print(f"    Últimos 200 bytes: {all_data[-200:]!r}")
        
    finally:
        monkey.terminate()
        try:
            monkey.wait(timeout=3)
            print(f"\n[4] Monkey parado (exitcode: {monkey.returncode})")
        except:
            monkey.kill()
            monkey.wait()
            print(f"\n[4] Monkey killado")
    
    print("\n=== RESULTADO ===")
    if TEST_MESSAGE in all_data:
        print("✅ SUCESSO: leitura do slave funciona")
        return 0
    else:
        print("❌ FALHA: não foi possível ler TEST_MESSAGE do slave")
        return 1


if __name__ == "__main__":
    sys.exit(main())
