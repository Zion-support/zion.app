#!/usr/bin/env python3
"""Live send cycle — wraps send_cold_outreach_v2.py for cron (one-line JSON summary)."""
from pathlib import Path
import json, subprocess, sys

SCRIPT = Path(__file__).resolve().parent.parent / "send_cold_outreach_v2.py"
try:
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=300)
    out = r.stdout.strip()
    err = r.stderr.strip()
    # try to parse JSON summary from stdout
    try:
        summary = json.loads(out)
    except Exception:
        summary = {"raw_stdout": out, "raw_stderr": err}
    summary["exit_code"] = int(r.returncode)
    print(json.dumps(summary))
except subprocess.TimeoutExpired:
    print(json.dumps({"status": "timeout", "timeout_s": 300}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
