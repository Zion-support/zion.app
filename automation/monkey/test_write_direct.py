#!/usr/bin/env python3
"""Teste de escrita direta no master do PTY — testa se write(2) no master
funciona e se o slave pode ler os dados."""
from __future__ import annotations
import os
import pty
import select
import sys
import time
from pathlib import Path

TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"


def main():
    print("=== Teste de write(2) direto no PTY ===")
    
    print("[1] Criando PTY com pty.openpty()...")
    try:
        master_fd, slave_fd = pty.openpty()
        print(f"    master_fd={master_fd}, slave_fd={slave_fd}")
        slave_path = os.ttyname(slave_fd)
        print(f"    slave_path: {slave_path}")
    except Exception as e:
        print(f"    ❌ pty.openpty() falhou: {e}")
        return 1
    
    try:
        # Testar write no master
        print("[2] Testando write(2) no master_fd...")
        written = os.write(master_fd, TEST_MESSAGE)
        print(f"    Escritos {written} bytes no master_fd={master_fd}")
        
        # Ler no slave
        print("[3] Lendo dados do slave_fd...")
        buf = b""
        deadline = time.time() + 3.0
        while time.time() < deadline:
            rl, _, _ = select.select([slave_fd], [], [], 0.2)
            if rl:
                chunk = os.read(slave_fd, 4096)
                if chunk:
                    buf += chunk
                    print(f"    Lido chunk {len(chunk)} bytes: {chunk!r}")
                    if TEST_MESSAGE in buf:
                        print(f"    ✅ TEST_MESSAGE encontrado no slave!")
                        print(f"    Total lido: {len(buf)} bytes")
                        print(f"    Dados completos: {buf!r}")
                        break
            else:
                pass  # sem dados no momento
        
        if TEST_MESSAGE not in buf:
            print(f"    ❌ TEST_MESSAGE não encontrado no slave")
            print(f"    Total lido: {len(buf)} bytes")
            print(f"    Dados: {buf!r}")
            return 1
        
        # Testar escrita em lote
        print("[4] Testando write(2) em lote no master...")
        batch = b"RANDOM_DATA_" + os.urandom(100) + b"\n"
        written = os.write(master_fd, batch)
        print(f"    Escritos {written} bytes")
        
        # Ler no slave
        buf2 = b""
        deadline = time.time() + 3.0
        while time.time() < deadline:
            rl, _, _ = select.select([slave_fd], [], [], 0.2)
            if rl:
                chunk = os.read(slave_fd, 4096)
                if chunk:
                    buf2 += chunk
                    print(f"    Lido chunk {len(chunk)} bytes")
                    if len(buf2) > 0:
                        print(f"    Dados: {buf2[-100:]!r}")
                        break
            else:
                pass
        
        print(f"    Total lido do batch: {len(buf2)} bytes")
        if batch[:20] in buf2:
            print(f"    ✅ Batch encontrado no slave!")
        else:
            print(f"    ⚠ Batch não encontrado (pode ter sido misturado com outros dados)")
        
        print("\n=== RESULTADO ===")
        print("✅ write(2) no master_fd funciona — dados chegam ao slave")
        return 0
        
    finally:
        print("\n[5] Limpeza...")
        try:
            os.close(master_fd)
            print(f"    master_fd={master_fd} fechado")
        except:
            pass
        try:
            os.close(slave_fd)
            print(f"    slave_fd={slave_fd} fechado")
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
