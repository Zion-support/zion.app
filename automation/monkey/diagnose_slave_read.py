#!/usr/bin/env python3
"""
diagnose_slave_read.py — Testa se o worker consegue ler TEST_MESSAGE do slave
após fechar e re-abrir o fd (simulando o que o harness faz).
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


def run(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(timeout=5)
    return out, err, p.returncode


def main():
    print("=== Diagnóstico: leitura do slave após injeção ===")
    
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
        while time.time() - start < 10:
            out, err, rc = run(str(MONKEY_CTRL_BIN))
            if "TEST_MESSAGE injected" in out:
                print("    ✅ TEST_MESSAGE injetado confirmado no shm")
                # Extrair slave_path
                m = re.search(r"slave=(/dev/ttys\d+)", out)
                if m:
                    slave_path = m.group(1)
                    print(f"    slave_path: {slave_path}")
                break
            time.sleep(0.2)
        
        if not slave_path:
            print("❌ TEST_MESSAGE não foi injetado dentro do timeout")
            monkey.terminate()
            return 1
        
        # 3. Abir slave, fechar, re-abrir (como faz o harness)
        print(f"[3] Testando leitura do slave {slave_path}...")
        
        # Abre pela primeira vez
        fd1 = os.open(slave_path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"    Aberto fd1={fd1}")
        
        # Lê um pouco para consumir dados pré-existentes
        ready, _, _ = select.select([fd1], [], [], 0.5)
        if ready:
            data = os.read(fd1, 4096)
            print(f"    Lido do fd1: {len(data)} bytes (descartando)")
        
        # Fecha
        os.close(fd1)
        print(f"    Fechado fd1")
        
        # Pequeno delay
        time.sleep(0.2)
        
        # Re-abre (como faz o worker thread)
        fd2 = os.open(slave_path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"    Re-aberto fd2={fd2}")
        
        # Lê com blocking (timeout via select)
        all_data = bytearray()
        t0 = time.time()
        while time.time() - t0 < 3.0:
            ready, _, _ = select.select([fd2], [], [], 0.3)
            if ready:
                try:
                    chunk = os.read(fd2, 4096)
                    if not chunk:
                        break
                    all_data.extend(chunk)
                    if TEST_MESSAGE in all_data:
                        print(f"    ✅ TEST_MESSAGE encontrado! Total: {len(all_data)} bytes")
                        print(f"    Dados ao redor: {all_data[max(0, all_data.index(TEST_MESSAGE)-30):all_data.index(TEST_MESSAGE)+len(TEST_MESSAGE)+30]!r}")
                        break
                except Exception as e:
                    print(f"    Erro ao ler: {e}")
                    break
            else:
                # Sem dados no momento, continua
                pass
        
        if TEST_MESSAGE not in all_data:
            print(f"    ❌ TEST_MESSAGE não encontrado. Total lido: {len(all_data)} bytes")
            print(f"    Últimos 300 bytes: {all_data[-300:]!r}")
        
        os.close(fd2)
        
    finally:
        monkey.terminate()
        try:
            monkey.wait(timeout=3)
        except:
            monkey.kill()
            monkey.wait()
        print(f"\n[4] Monkey parado (exitcode: {monkey.returncode})")
    
    print("\n=== RESULTADO ===")
    if TEST_MESSAGE in all_data if 'all_data' in dir() else False:
        print("✅ SUCESSO: leitura do slave funciona")
        return 0
    else:
        print("❌ FALHA: não foi possível ler TEST_MESSAGE do slave")
        return 1


if __name__ == "__main__":
    sys.exit(main())
