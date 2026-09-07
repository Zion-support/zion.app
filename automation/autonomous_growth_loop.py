#!/usr/bin/env python3
"""
Autonomous Growth Engine — live run wrapper.

Environment:
  DRY_RUN_OUTREACH  - if unset, forced to 0 (live sends).
                        1 = dry-run (no actual sends).

Usage:
  python3 autonomous_growth_loop.py
"""

import os
import json
import time
import uuid
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
REPORT_DIR = WORKSPACE / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Force live sends unless the operator explicitly sets DRY_RUN_OUTREACH=1
dry_run = os.environ.get("DRY_RUN_OUTREACH", "0").strip()
if dry_run == "" or dry_run is None:
    os.environ["DRY_RUN_OUTREACH"] = "0"
    dry_run = "0"

run_id = str(uuid.uuid4())[:8]
ts_now = datetime.now(timezone.utc).isoformat()

report_path = REPORT_DIR / "growth-engine-report-latest.json"

# Thin wrapper: delegate the actual outreach to the existing send_cold_outreach_v2.py
outreach_script = WORKSPACE / "send_cold_outreach_v2.py"

payload = {
    "run_id": run_id,
    "ts": ts_now,
    "dry_run": dry_run == "1",
    "status": "running",
    "command": "python3 autonomous_growth_loop.py",
}

try:
    # Try V2 first
    if outreach_script.exists():
        import subprocess
        env = os.environ.copy()
        env["DRY_RUN_OUTREACH"] = dry_run
        result = subprocess.run(
            ["python3", str(outreach_script)],
            cwd=str(WORKSPACE),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        payload["exit_code"] = result.returncode
        payload["stdout"] = result.stdout[-4000:] if result.stdout else ""
        payload["stderr"] = result.stderr[-2000:] if result.stderr else ""
        payload["status"] = "ok" if result.returncode == 0 else "error"
    else:
        payload["status"] = "error"
        payload["error"] = "send_cold_outreach_v2.py not found in workspace"

except subprocess.TimeoutExpired:
    payload["status"] = "error"
    payload["error"] = "outreach script timed out (120s)"
except Exception as exc:
    payload["status"] = "error"
    payload["error"] = f"{type(exc).__name__}: {exc}"

# Merge stats from the actual send log (JSONL) written by send_cold_outreach_v2.py
send_log_path = WORKSPACE.parent / "outreach-send-log.jsonl"
if send_log_path.exists():
    try:
        with open(send_log_path) as f:
            send_lines = [json.loads(line) for line in f if line.strip()]
        payload["send_log_total"] = len(send_lines)
        sent_count = sum(1 for r in send_lines if r.get("status") == "sent")
        failed_count = sum(1 for r in send_lines if r.get("status") == "failed")
        payload["send_succeeded"] = sent_count
        payload["send_failed"] = failed_count
        payload["send_attempted"] = len(send_lines)
        # last send timestamp
        if send_lines:
            payload["last_send_ts"] = send_lines[-1].get("timestamp")
    except Exception:
        pass

report_path.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
