#!/usr/bin/env python3
"""Teste minimalista: monkey + shm + leitura direta."""
from __future__ import annotations
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MONKEY = Path("/Users/miami2/zion.app/automation/monkey/monkey")
MONKEY_CTRL = Path("/Users/miami2/zion.app/automation/monkey/monkey_ctrl")
TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"


def main():
    print("=== Teste minimalista monkey+shm ===")
    
    # Garantir shm limpo
    try:
        os.unlink("/monkey_shm")
    except:
        pass
    
    print("[1] Iniciando monkey com delay=50000...")
    monkey = subprocess.Popen(
        [str(MONKEY), "50000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"    PID: {monkey.pid}")
    
    # Dar tempo para inicializar
    time.sleep(0.5)
    
    try:
        # Verificar se monkey está vivo
        if monkey.poll() is not None:
            stdout, stderr = monkey.communicate(timeout=2)
            print(f"❌ Monkey morreu imediatamente!")
            print(f"    stdout: {stdout!r}")
            print(f"    stderr: {stderr!r}")
            return 1
        
        print("[2] Verificando shm...")
        for i in range(20):
            time.sleep(0.3)
            try:
                result = subprocess.run(
                    [str(MONKEY_CTRL)],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                stdout = result.stdout.strip()
                print(f"    T{i+1}: {stdout!r}")
                
                if "TEST_MESSAGE injected" in stdout:
                    print("    ✅ TEST_MESSAGE injetado!")
                    # Extrair slave_path
                    m = re.search(r"slave=(/dev/ttys\d+)", stdout)
                    if m:
                        print(f"    slave_path: {m.group(1)}")
                    # Mostrar mais detalhes
                    print(f"    chars: {re.search(r'chars:(\d+)', stdout)}")
                    print(f"    writes: {re.search(r'writes:(\d+)', stdout)}")
                    break
            except Exception as e:
                print(f"    Erro: {e}")
        
        if "TEST_MESSAGE injected" not in stdout:
            print("❌ TEST_MESSAGE não injetado")
            print(f"    Último stdout: {stdout!r}")
            
    finally:
        print("[3] Parando monkey...")
        monkey.terminate()
        try:
            monkey.wait(timeout=3)
            print(f"    Exit: {monkey.returncode}")
        except:
            monkey.kill()
            monkey.wait()
            print(f"    Kill exit: {monkey.returncode}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
