#!/usr/bin/env python3
"""Teste v2: PTY real com worker que RE-ABRE o slave por caminho (evita fd herdado via fork)."""
import os
import sys
import pty
import time
import select
import multiprocessing

TEST_MESSAGE = b"MONKEY_TEST_STRING_12345\n"

def slave_worker(slave_path):
    """Worker que abre o slave por caminho (não fd herdado do fork)."""
    try:
        print(f"[worker] abrindo slave por caminho: {slave_path}")
        fd = os.open(slave_path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"[worker] slave aberto: fd={fd}")
        try:
            buf = b""
            deadline = time.time() + 12.0
            while time.time() < deadline:
                rl, _, _ = select.select([fd], [], [], 0.2)
                if rl:
                    chunk = os.read(fd, 4096)
                    if chunk:
                        buf += chunk
                        print(f"[worker] lido {len(chunk)} bytes, total {len(buf)}: {chunk!r}")
                        if TEST_MESSAGE in buf:
                            print(f"[worker] ACHOU TEST_MESSAGE no slave!")
                            break
                else:
                    # sem dados prontos
                    pass
            print(f"[worker] FIM: total lido={len(buf)}, buf={buf!r}")
        finally:
            os.close(fd)
            print(f"[worker] fd={fd} fechado")
    except Exception as e:
        print(f"[worker] ERRO: {type(e).__name__}: {e}")

def main():
    print(f"=== Teste PTY v2: worker re-abre slave por caminho ===")
    print(f"kernel={os.uname().release}, arch={os.uname().machine}, pid={os.getpid()}")
    print(f"stderr é tty: {os.isatty(sys.stderr.fileno())}")

    try:
        master_fd, slave_fd = pty.openpty()
    except Exception as e:
        print(f"pty.openpty() FALHOU: {type(e).__name__}: {e}")
        return 1

    slave_path = os.ttyname(slave_fd)
    print(f"pty.openpty() OK: master_fd={master_fd}, slave_fd={slave_fd}, slave={slave_path}")

    print("[worker] iniciando processo que re-abre o slave por caminho...")
    proc = multiprocessing.Process(target=slave_worker, args=(slave_path,))
    proc.start()

    time.sleep(0.5)

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

    proc.join(timeout=10)
    if proc.is_alive():
        print("[worker] não terminou no timeout — matando...")
        proc.terminate()
        proc.join(timeout=2)

    print(f"[rd] worker terminado com exitcode={proc.exitcode}")

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
    print("  Se worker leu TEST_MESSAGE no slave -> injeção via write(2) no mestre FUNCIONOU com worker que re-abre slave por caminho.")
    print("  Se worker não leu -> problema persiste mesmo com re-abertura por caminho.")
    return 0

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
