# PROMPT_FOR_AGENTS.md — Monkey Typing End-to-End Validation

**Purpose**: enable other agents to autonomously validate the Monkey Typing system on macOS and report results back.

---

## 1. Context & Objective

**Goal**: Validate Monkey Typing end-to-end on macOS (`Miami2-5.local`, Darwin 21.6.0, x86_64). The validation is:

1. `monkey` creates its own PTY internally via `openpty()` (self-contained, no PTY argument needed).
2. `monkey` writes the slave path to `/dev/shm` (`/monkey_shm`) via `shm_write_slave(slave_path)` (format: `slave=<path>\n`).
3. `monkey_ctrl` reads `/monkey_shm` and prints it (format: `Estado: %s\n`).
4. A worker thread re-opens the slave by path (regex `r'slave=(/dev/ttys\d+)'` to extract the path from `monkey_ctrl` stdout).
5. `monkey` injects `TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"` via `write(2)` after `count >= 20` (~2 seconds with default 100ms delay).
6. The worker confirms it reads `b"MONKEY_INTEGRATION_TEST_STRING_12345\n"` from the slave.
7. Result is documented in `CROSS_READ_VALIDATED.md`.

**Current state**: `monkey.c` (5864 bytes), `monkey_ctrl.c` (797 bytes), `test_monkey_pty_integration.py` (9049 bytes, v3 — self-contained monkey + shm slave_path + worker cross-read) are present in `/Users/miami2/zion.app/automation/monkey/`. Binaries `monkey` (51288 bytes) and `monkey_ctrl` (49720 bytes) exist but may be stale. Prior cross-read was validated via `pty_cross_test_v2.py` (exitcode 0, worker re-opened `/dev/ttys003`, read `b'MONKEY_TEST_STRING_12345\n'`, found `TEST_MESSAGE`). Integration test not yet cleanly executed.

---

## 2. Host & Environment

- **Working directory**: `/Users/miami2/zion.app/automation/monkey/`
- **macOS host**: `Miami2-5.local`, Darwin 21.6.0, arch x86_64, user `miami2`, `gcc` and `python3` available
- **macOS PTY devices**: `/dev/ttys*` (not `/dev/pts/*`); example: `/dev/ttys003`
- **Windows/MSYS2 fallback host**: only `test_all_monkey_pty.sh` and `test_monkey_pty_integration.py` accessible; `monkey.c` absent; `gcc`/`python3` not available → **cannot compile or run from here**
- **Cross-host rule**: if the current host is Windows/MSYS2 and `monkey.c` is absent, do NOT attempt compilation/execution; instead request the user to either paste `monkey.c` content or run on the Mac and share output

---

## 3. Technical Specifications

### Shared Memory
- Name: `/monkey_shm`
- Size: 4096 bytes
- `shm_open` with `O_CREAT | O_RDWR`, `0666`
- `ftruncate(fd, 4096)` after creation
- `mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0)`
- `shm_unlink(SHM_NAME)` before `shm_open` to avoid `ftruncate: Invalid argument` from residual objects
- On `monkey` exit: `shm_unlink(SHM_NAME)` (removes shm)

### monkey.c (current version)
- Includes `<util.h>` for `openpty()`/`ttyname()` on macOS
- `openpty(&master_fd, &slave_fd, slave_name, NULL, NULL)` — checked via return value, **not** assigned to `master_fd`
- `shm_init()`: `shm_unlink` first, then `shm_open`, `ftruncate`, `mmap`, `memset(0)`
- `shm_write_slave(path)`: writes `slave=%s\n` to shm, fills rest with null
- `shm_write_status(fmt, ...)`: preserves leading `slave=...` line across status writes; writes status like `status:ready, fd=%d, delay=%dus`, `status:running, fd:%d, delay:%dus`, etc.
- `monkey_run(fd, delay_us)`: writes random chars via `write(2)` in a loop with `usleep(delay_us)`; after `count >= 20`, injects `TEST_MESSAGE` via `write(2)`; on `EAGAIN`/`EWOULDBLOCK` backs off with `usleep(delay_us * 2)`
- Signals: `SIGINT`, `SIGTERM` set `running = 0`
- Cleanup: `close(master_fd)`, `close(slave_fd)`, `munmap`, `shm_unlink`
- Compiles on macOS with: `gcc -o monkey monkey.c` (no `-lrt`)

### monkey_ctrl.c (current version)
- Opens `/monkey_shm`, `mmap`s it
- Prints with `printf("Estado: %s\n", ptr)`
- Compiles on macOS with: `gcc -o monkey_ctrl monkey_ctrl.c` (no `-lrt`)

### test_monkey_pty_integration.py (v3, current)
- `TEST_MESSAGE = b"MONKEY_INTEGRATION_TEST_STRING_12345\n"`
- `WorkerResult` container (fields: `slave_path`, `bytes_read`, `found_test_message`, `error`, `exitcode`)
- `worker_thread(slave_path, result_container)`: opens slave by path with `O_RDONLY | O_NONBLOCK`; uses `select` with 2.5s timeout; reads in a loop; checks for `TEST_MESSAGE`; sets result fields
- `read_slave_path_from_shm()`: runs `monkey_ctrl` (absolute path `/Users/miami2/zion.app/automation/monkey/monkey_ctrl`) via `subprocess.run`; regex `r'slave=(/dev/ttys\d+)'` to extract `slave_path`; returns path or None
- `main()`: starts `monkey` via `subprocess.Popen` with **no PTY argument** (self-contained); waits briefly; reads `slave_path_from_monkey` from shm; if path found, creates worker thread with that path; waits for worker; reports success/failure with details
- If `slave_path` not found: reports failure with `monkey_ctrl` stdout

---

## 4. Execution Plan (macOS)

### Step 1: Verify/Sync Sources
- Read `monkey.c`, `monkey_ctrl.c`, `test_monkey_pty_integration.py` to confirm current state
- If any source is missing or corrupted, report immediately

### Step 2: Compile (if needed)
```bash
cd /Users/miami2/zion.app/automation/monkey/
gcc -o monkey monkey.c
gcc -o monkey_ctrl monkey_ctrl.c
```
- No `-lrt` flag on macOS
- If compilation fails, capture error and report

### Step 3: Run Integration Test
```bash
cd /Users/miami2/zion.app/automation/monkey/
python3 test_monkey_pty_integration.py
```
- Capture stdout, stderr, exit code
- If the script hangs, terminate after reasonable timeout (e.g. 30s) and report

### Step 4: Validate Result
Success criteria:
- `test_monkey_pty_integration.py` exits with code 0
- Output shows: monkey started, shm created, slave path extracted (e.g., `/dev/ttys00X`), worker opened slave, worker read bytes, worker found `TEST_MESSAGE`
- Worker result: `found_test_message = True`

Failure modes to diagnose:
- `slave_path` not found: check `monkey_ctrl` output, check if `monkey` is running, check shm format
- Worker timeout: check if slave path is correct, check if `monkey` is actually injecting (check `count >= 20` timing)
- Write errors: check `monkey` stderr for `write` failures
- `EAGAIN`/`EWOULDBLOCK`: normal if slave not reading; monkey backs off

### Step 5: Document
- Update `CROSS_READ_VALIDATED.md` (or create new section) with:
  - Date/time of validation
  - Host (Miami2-5.local, Darwin 21.6.0)
  - Test outcome (pass/fail)
  - Slave path used
  - Bytes read by worker
  - Whether `TEST_MESSAGE` was found
  - Full stdout/stderr captured
  - Any errors and diagnosis
  - Next steps if applicable

---

## 5. Decision Tree

```
Is current host macOS (Darwin) with /Users/miami2/zion.app/automation/monkey/ accessible?
├── YES → proceed with execution plan above
└── NO (Windows/MSYS2 or other) → check if monkey.c is present
    ├── monkey.c present → can compile, but PTY devices may differ; proceed with caution
    └── monkey.c absent → BLOCKED: request user to either
        a) paste monkey.c content here, or
        b) run on Mac and share output, or
        c) provide SSH/Mac access
        DO NOT fabricate results; report blocker clearly
```

---

## 6. Constraints (from user profile)

- **Never create external accounts** or handle credentials in the user's name
- **Credentials rule**: replace any API keys/tokens/passwords/secrets with `[REDACTED]`
- **Language**: PT-BR for reports/roadmaps/scripts; English for technical details in code/logs
- **Verification**: after any `write_file`, confirm with `ls -la` and/or read back before declaring done
- **Disk trust**: trust disk state over assertions; if something is missing, recreate it rather than claim it exists
- **No fabrication**: if a result cannot be produced, report the blocker honestly
- **Standby discipline**: do not advance without a concrete trio (o quê + onde + como); treat `[standby]` / redirect markers / empty input as noise
- **User**: Kleber Garcia Alcatrão — CEO Zion Tech Group (ziontechgroup.com)

---

## 7. Known Issues & Resolutions

| Issue | Resolution |
|-------|------------|
| `ld: library not found for -lrt` | Remove `-lrt` from compile command (macOS native shm_open/mmap) |
| `ftruncate: Invalid argument` / `Falha shm_init` | `shm_unlink(SHM_NAME)` before `shm_open` in `shm_init()` |
| `openpty()` return-value overwrite | Check return value: `if (openpty(&master_fd, &slave_fd, slave_name, NULL, NULL) < 0)` |
| `tty.h`/`pty.h` not found on macOS | Use `<util.h>` for `openpty()`/`ttyname()` |
| Harness v1 bug: `TypeError: expected str, bytes or os.PathLike object, not code` | Rewrote v2 using `threading.Thread` for worker; v3 for self-contained monkey |
| Harness v3 scoping bug: `slave_path_from_monkey` used before assignment | Rewrote `main()` to start monkey first, then read shm, then create worker |
| Harness v3 patch mismatches | Rewrote harness wholesale to avoid incremental patch drift |
| Cross-read not validated (earlier) | Resolved via `pty_cross_test_v2.py`: worker re-opens slave by path, reads injected bytes, finds `TEST_MESSAGE` |

---

## 8. Files Reference

All in `/Users/miami2/zion.app/automation/monkey/`:

| File | Size | Role |
|------|------|------|
| `monkey.c` | 5864 bytes | PTY injector source (self-contained openpty) |
| `monkey_ctrl.c` | 797 bytes | shm status reader/writer source |
| `monkey` | 51288 bytes | Compiled monkey binary (may be stale) |
| `monkey_ctrl` | 49720 bytes | Compiled controller binary (may be stale) |
| `test_monkey_pty_integration.py` | 9049 bytes | Integration harness (v3, self-contained) |
| `pty_cross_test_v2.py` | 3319 bytes | Previously validated cross-read test |
| `test_all_monkey_pty.sh` | 6961 bytes | Full test suite script |
| `CROSS_READ_VALIDATED.md` | 5913 bytes | Validation documentation |

---

## 9. Expected Output (success case)

```
=== monkey.c ===
[monkey.c content shown]

✅ Compilation successful
✅ monkey started (PID ...)
✅ shm created at /monkey_shm
✅ slave_path extracted: /dev/ttys00X
✅ Worker opened slave /dev/ttys00X (fd=N)
✅ Worker read N bytes
✅ Worker found TEST_MESSAGE: b'MONKEY_INTEGRATION_TEST_STRING_12345\n'
✅ Integration test PASSED (exit code 0)
```

---

## 10. Sign-Off Criteria

- [ ] `monkey.c` and `monkey_ctrl.c` compiled successfully on macOS (or confirmed already compiled and current)
- [ ] `test_monkey_pty_integration.py` executed with exit code 0
- [ ] Worker read `b"MONKEY_INTEGRATION_TEST_STRING_12345\n"` from slave
- [ ] Result documented in `CROSS_READ_VALIDATED.md`
- [ ] All output captured as evidence

---

*End of prompt.*
