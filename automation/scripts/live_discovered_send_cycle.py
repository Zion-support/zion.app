#!/usr/bin/env python3
"""Live discovered send cycle — sends to leads from app/data/discovered_leads.json."""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

DISCOVERED = Path("/Users/miami2/zion.app/app/data/discovered_leads.json")
LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log.jsonl")
REPORT = Path("/Users/miami2/zion.app/automation/reports/live-discovered-send-cycle-latest.json")
ACCOUNT = "kleber@ziontechgroup.com"
ALLOW_SEND = "LIVE_SEND_ALLOW_SEND" in os.environ

def is_already_sent(email):
    if not LOG_PATH.exists():
        return False
    el = email.lower()
    try:
        with open(LOG_PATH) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("status") == "sent" and r.get("to", "").lower() == el:
                            return True
                    except (json.JSONDecodeError, KeyError):
                        pass
    except Exception:
        pass
    return False

def send_discovered_email(to_email, subject, body):
    cmd = ["gog", "gmail", "send", "--to", to_email, "--subject", subject, "--body", body, "--account", ACCOUNT, "--no-input", "--json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return "sent", None
        return "failed", (r.stderr.strip() or r.stdout.strip() or f"exit {r.returncode}")
    except subprocess.TimeoutExpired:
        return "failed", "timeout"
    except Exception as e:
        return "failed", str(e)

def main():
    import os
    if not ALLOW_SEND:
        print(json.dumps({"status": "blocked", "message": "LIVE_SEND_ALLOW_SEND not set"}))
        return

    with open(DISCOVERED) as f:
        leads = json.load(f)

    report = {
        "mode": "live_discovered_send_cycle",
        "queue_send_ready": True,
        "targeted": 0,
        "duplicate_skips": 0,
        "live_send": 0,
        "failed": 0,
        "skipped_no_email": 0,
        "sent_emails": [],
        "errors": [],
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "account": ACCOUNT,
        "leads_source": str(DISCOVERED),
        "exit_code": 0
    }

    for i, lead in enumerate(leads):
        email = (lead.get("email") or "").strip().lower()
        name = lead.get("name", f"Lead #{i+1}")
        company = lead.get("company", "")
        subject = lead.get("subject", f"AI automation for {company}")

        if not email:
            report["skipped_no_email"] += 1
            continue

        if is_already_sent(email):
            report["duplicate_skips"] += 1
            continue

        report["targeted"] += 1
        body = (
            f"Olá {name or ''}, analisei seu perfil e identifiquei uma oportunidade relevante em AI Automation.\n\n"
            f"Se estiver interessado, podemos agendar uma conversa rápida.\n\n"
            f"Atenciosamente,\nKleber | Zion Tech Group\n{ACCOUNT}"
        )

        status, error = send_discovered_email(email, subject, body)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "to": email,
            "name": name,
            "company": company,
            "subject": subject,
            "source": lead.get("source", ""),
            "status": status,
            "error": error
        }
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        if status == "sent":
            report["live_send"] += 1
            report["sent_emails"].append({"to": email, "name": name, "company": company})
        else:
            report["failed"] += 1
            report["errors"].append({"to": email, "name": name, "error": error})

    report["exit_code"] = 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report))

if __name__ == "__main__":
    main()
