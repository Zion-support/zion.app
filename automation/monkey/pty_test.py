#!/usr/bin/env python3
"""Teste concreto de Monkey Typing via PTY real em Python (sem TTY interativo necessário)."""
import os
import sys
import pty
import time
import select
import signal

def test_posix_openpt():
    """Abordagem 1: openpty nativo via os.posix_openpt + grantpt + unlockpt."""
    print("[1] testando os.posix_openpt()...")
    try:
        master_fd = os.posix_openpt(os.O_RDWR | os.O_NOCTTY)
        os.grantpt(master_fd)
        os.unlockpt(master_fd)
        slave_path = os.ttyname(master_fd)
        print(f"    openpty nativo OK: master_fd={master_fd}, slave={slave_path}")
        return master_fd, slave_path
    except Exception as e:
        print(f"    openpty nativo FALHOU: {type(e).__name__}: {e}")
        return None, None

def test_pty_openpty():
    """Abordagem 2: pty.openpty() padrão."""
    print("[2] testando pty.openpty()...")
    try:
        master_fd, slave_fd = pty.openpty()
        slave_path = os.ttyname(slave_fd)
        os.close(slave_fd)
        print(f"    pty.openpty() OK: master_fd={master_fd}, slave={slave_path}")
        return master_fd, slave_path
    except Exception as e:
        print(f"    pty.openpty() FALHOU: {type(e).__name__}: {e}")
        return None, None

def test_injection(master_fd, slave_path, label):
    """Testa injeção de keystrokes via write(2) no PTY mestre."""
    print(f"\n[{label}] testando injeção de keystrokes no PTY mestre...")
    test_str = "echo 'TYPING_TEST_OK'\n"
    try:
        bytes_written = os.write(master_fd, test_str.encode())
        print(f"    write() OK: {bytes_written} bytes injetados, fd={master_fd}, slave={slave_path}")
        return True
    except Exception as e:
        print(f"    write() FALHOU: {type(e).__name__}: {e}")
        return False

def test_read_back(master_fd, timeout=2.0):
    """Tenta ler o que sai do PTY mestre após injeção."""
    print(f"[rd] testando leitura do PTY mestre (timeout={timeout}s)...")
    try:
        end = time.time() + timeout
        data = b""
        while time.time() < end:
            rl, _, _ = select.select([master_fd], [], [], 0.2)
            if rl:
                chunk = os.read(master_fd, 4096)
                if chunk:
                    data += chunk
                    print(f"    lido {len(chunk)} bytes (total {len(data)})")
            else:
                break
        if data:
            decoded = data.decode(errors="replace")
            print(f"    dado recebido ({len(data)} bytes): {repr(decoded[:400])}")
            return decoded
        else:
            print("    sem dado recebido no tempo limite (comum se slave não tá rodando nada)")
            return None
    except Exception as e:
        print(f"    leitura FALHOU: {type(e).__name__}: {e}")
        return None

def cleanup(master_fd):
    try:
        os.close(master_fd)
        print(f"[cl] master_fd={master_fd} fechado")
    except Exception as e:
        print(f"[cl] erro ao fechar master_fd={master_fd}: {e}")

def main():
    print(f"=== Teste concreto Monkey Typing via PTY Python (macOS) ===")
    print(f"kernel: {os.uname().release}, arch: {os.uname().machine}, pid: {os.getpid()}")
    print(f"cwd: {os.getcwd()}")
    print(f"stderr é tty: {os.isatty(sys.stderr.fileno())}")
    print()

    master = None
    slave_path = None

    # Abordagem 1
    m1, s1 = test_posix_openpt()
    if m1 is not None:
        master, slave_path = m1, s1

    # Abordagem 2 (só se a 1 falhar)
    if master is None:
        m2, s2 = test_pty_openpty()
        if m2 is not None:
            master, slave_path = m2, s2

    if master is None:
        print("\nRESULTADO: nenhum método abriu PTY mestre. PTY não disponível neste contexto.")
        return 1

    # Injeta keystrokes
    ok = test_injection(master, slave_path, "inj")

    # Ler de volta o que aparece (se houver algo sendo executado no slave)
    _ = test_read_back(master)

    cleanup(master)
    print("\nRESULTADO FINAL:")
    if ok:
        print("  -> Injecao de keystrokes via write(2) no PTY mestre FUNCIONOU.")
        print("     Estas abordagens podem ser o caminho para validar o monkey.c em macOS.")
    else:
        print("  -> Injecao falhou.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
