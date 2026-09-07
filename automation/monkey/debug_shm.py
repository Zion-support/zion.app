#!/usr/bin/env python3
"""Mostra o conteúdo exato do shm em hexdump para debug."""
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


def hexdump(data: bytes, length=16):
    """Mostra hexdump de dados binários."""
    lines = []
    for i in range(0, len(data), length):
        chunk = data[i:i+length]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{i:04x}  {hex_part:<{length*3}}  |{ascii_part}|')
    return '\n'.join(lines)


def read_shm_bytes():
    """Lê o shm e retorna os bytes brutos."""
    try:
        result = subprocess.run(
            [str(MONKEY_CTRL)],
            capture_output=True,
            timeout=5,
        )
        # monkey_ctrl mostra o shm como string, mas podemos ler os bytes diretamente
        fd = os.open("/monkey_shm", os.O_RDONLY)
        try:
            data = os.read(fd, 4096)
            return data
        finally:
            os.close(fd)
    except Exception as e:
        print(f"Erro ao ler shm: {e}")
        return b""


def main():
    print("=== Debug: Conteúdo do shm ===")
    
    # Limpa shm
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
    time.sleep(0.5)
    
    try:
        if monkey.poll() is not None:
            out, err = monkey.communicate(timeout=2)
            print(f"❌ monkey morreu: rc={monkey.returncode}")
            print(f"    stdout: {out!r}")
            print(f"    stderr: {err!r}")
            return 1
        
        print("[2] Lendo shm a cada 1s por 15s...")
        for i in range(15):
            time.sleep(1.0)
            data = read_shm_bytes()
            print(f"\n--- T{i+1} (total {len(data)} bytes) ---")
            print(hexdump(data))
            
            # Tenta encontrar o TEST_MESSAGE
            if TEST_MESSAGE in data:
                idx = data.index(TEST_MESSAGE)
                print(f"\n✅ TEST_MESSAGE encontrado na posição {idx}!")
                break
            
            # Verifica se monkey ainda está vivo
            if monkey.poll() is not None:
                print("❌ monkey morreu!")
                out, err = monkey.communicate(timeout=2)
                print(f"    rc={monkey.returncode}, stderr={err!r}")
                break
        else:
            print("\n❌ TEST_MESSAGE não encontrado após 15s")
            
    finally:
        monkey.terminate()
        try:
            monkey.wait(timeout=3)
            print(f"\n[3] Monkey parado: rc={monkey.returncode}")
        except:
            monkey.kill()
            monkey.wait()
            print(f"\n[3] Monkey killado")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
