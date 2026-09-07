#!/bin/bash
set -e
cd /Users/miami2/zion.app/automation/monkey

python3 - << 'PY'
import os, sys, time, tty, pty, select, signal

master, slave = pty.openpty()
slave_name = os.ttyname(slave)
master_name = os.ttyname(master)

print(f"PTY_PAIR_READY={master_name}", flush=True)
print(f"PTY_SLAVE_READY={slave_name}", flush=True)

pid = os.fork()
if pid == 0:
    os.close(master)
    os.setsid()
    os.dup2(slave, 0)
    os.dup2(slave, 1)
    os.dup2(slave, 2)
    os.close(slave)
    os.execv("/bin/bash", ["bash", "--norc", "--noecho", "-c",
        "stty raw -echo; exec bash --norc --noecho"])
    sys.exit(1)

os.close(slave)
time.sleep(0.2)
print(f"SLAVE_PID={pid}", flush=True)
PY
