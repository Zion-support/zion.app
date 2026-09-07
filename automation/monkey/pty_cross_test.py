#!/usr/bin/env python3
"""Teste: PTY real com slave aberto (processo zumbi dedicado) + injeção via write(2) no mestre + leitura cruzada."""
import os
import sys
import pty
import time
import select
import multiprocessing
import ctypes

TEST_MESSAGE = b"MONKEY_TEST_STRING_12345\n"

def slave_worker(slave_fd):
    """Processo dedicado que mantém o slave aberto e lê do mesmo."""
    try:
        os.set_blocking(slave_fd, False)
        buf = b""
        deadline = time.time() + 10.0
        while time.time() < deadline:
            rl, _, _ = select.select([slave_fd], [], [], 0.2)
            if rl:
                chunk = os.read(slave_fd, 4096)
                if chunk:
                    buf += chunk
                    print(f"[worker] lido {len(chunk)} bytes, total {len(buf)}: {chunk!r}")
                    # se encontrar a string de teste, registra sucesso via shared memory-like via pipe
                    if TEST_MESSAGE in buf:
                        print(f"[worker] ACHOU TEST_MESSAGE no slave!")
            # timeout genérico
            if len(buf) > 0:
                break
        print(f"[worker] FIM: total lido={len(buf)}, buf={buf!r}")
    except Exception as e:
        print(f"[worker] ERRO: {type(e).__name__}: {e}")

def main():
    print(f"=== Teste PTY com slave aberto + injeção cross-read ===")
    print(f"kernel={os.uname().release}, arch={os.uname().machine}, pid={os.getpid()}")
    print(f"stderr é tty: {os.isatty(sys.stderr.fileno())}")

    try:
        master_fd, slave_fd = pty.openpty()
    except Exception as e:
        print(f"pty.openpty() FALHOU: {type(e).__name__}: {e}")
        return 1

    slave_path = os.ttyname(slave_fd)
    print(f"pty.openpty() OK: master_fd={master_fd}, slave_fd={slave_fd}, slave={slave_path}")

    # Inicia processo worker que mantém slave aberto
    print("[worker] iniciando processo dedicado no slave...")
    proc = multiprocessing.Process(target=slave_worker, args=(slave_fd,))
    proc.start()

    # Dá um tempo pro worker iniciar
    time.sleep(0.5)

    # Injeta no mestre
    print(f"[inj] injetando {len(TEST_MESSAGE)} bytes no mestre via write(2)...")
    try:
        n = os.write(master_fd, TEST_MESSAGE)
        print(f"[inj] write() OK: {n} bytes escritos no fd={master_fd}")
    except Exception as e:
        print(f"[inj] write() FALHOU: {type(e).__name__}: {e}")
        proc.terminate()
        proc.join(timeout=2)
        os.close(master_fd)
        os.close(slave_fd)
        return 1

    # Agora conte o worker
    proc.join(timeout=8)
    if proc.is_alive():
        print("[worker] não terminou no timeout — matando...")
        proc.terminate()
        proc.join(timeout=2)

    print(f"[rd] worker terminado com exitcode={proc.exitcode}")

    # Fecha descritores
    try:
        os.close(master_fd)
    except:
        pass
    try:
        os.close(slave_fd)
    except:
        pass
    print("[cl] descritores fechados")

    print("RESULTADO FINAL:")
    print("  Se worker leu TEST_MESSAGE no slave -> injeção via write(2) no mestre FUNCIONOU em PTY real com slave vivo.")
    print("  Se worker não leu -> algo bloqueou o cross-channel.")
    return 0

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
