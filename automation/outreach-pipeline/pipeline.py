#!/usr/bin/env python3
"""
Pipeline de Cold Outreach via Gmail (gog CLI).
- Lê leads.json
- Deduplica contra tracking.jsonl
- Renderiza template com personalização
- Envia via gog gmail send (ou simula em DRY_RUN=1)
- Registra cada tentativa no tracking.jsonl
- Respeita rate limit e max sends por execução
"""

from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

import json
import subprocess
import sys
import time

# ---- imports locais ----
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg


def load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(name: str) -> Template:
    path = cfg.TEMPLATES_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Template não encontrado: {path}")
    raw = path.read_text(encoding="utf-8")
    return Template(raw)


def load_sent_tracking() -> set:
    """Retorna conjunto de chaves 'template|email' já enviadas."""
    if not cfg.TRACKING_FILE.exists():
        return set()
    keys = set()
    for line in cfg.TRACKING_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            keys.add(f"{rec.get('template','')}|{rec.get('email','')}")
        except json.JSONDecodeError:
            continue
    return keys


def append_tracking(rec: Dict[str, Any]) -> None:
    """Adiciona um registro ao tracking.jsonl (append-only)."""
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    cfg.TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg.TRACKING_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def run_gog_send(account: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """Executa `gog gmail send` e retorna {ok, stdout, stderr, returncode}."""
    cmd = [
        "gog", "gmail", "send",
        "--account", account,
        "--to", to,
        "--subject", subject,
        "--body", body,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "Timeout após 60s", "returncode": -1}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "Comando gog não encontrado no PATH", "returncode": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}


def render_email(template: Template, lead: Dict[str, Any], template_name: str) -> Dict[str, Any]:
    """Renderiza subject + body a partir do template e do lead."""
    ctx: Dict[str, str] = {
        "name": lead.get("name", "Destinatário"),
        "company": lead.get("company", "sua empresa"),
        "role": lead.get("role", ""),
        "personal_note": lead.get("personal_note", ""),
    }
    subject_map = {
        "cold_outreach": f"Introdução — {ctx['company']} / {ctx['role']}",
        "follow_up": f"Seguimento — {ctx['company']}",
    }
    subject = subject_map.get(template_name, f"Contato — {ctx['company']}")
    try:
        body = template.substitute(**ctx)
    except KeyError as e:
        body = f"[Aviso: variável {e.args[0]} não fornecida no lead]"
    return {"subject": subject, "body": body}


def pipeline(
    leads_file: Optional[Path] = None,
    template_name: str = "cold_outreach",
    max_sends: Optional[int] = None,
    dry_run: Optional[bool] = None,
    account: Optional[str] = None,
) -> Dict[str, Any]:
    leads_file = leads_file or cfg.LEADS_FILE
    template_name = template_name or "cold_outreach"
    max_sends = max_sends if max_sends is not None else cfg.MAX_SENDS_PER_RUN
    dry_run = dry_run if dry_run is not None else cfg.DRY_RUN
    account = account or cfg.GMAIL_ACCOUNT

    leads = load_json(leads_file)
    template = load_template(template_name)
    sent_keys = load_sent_tracking()

    pending: List[Dict[str, Any]] = []
    skipped_existing = 0
    for lead in leads:
        email = lead.get("email")
        if not email:
            continue
        key = f"{template_name}|{email.lower()}"
        if key in sent_keys:
            skipped_existing += 1
            continue
        pending.append(lead)
        if len(pending) >= max_sends:
            break

    total_pending = len(pending)

    stats: Dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "account": account,
        "template": template_name,
        "dry_run": dry_run,
        "total_pending": total_pending,
        "skipped_existing": skipped_existing,
        "sent": 0,
        "failed": 0,
        "retries_used": 0,
        "details": [],
    }

    for idx, lead in enumerate(pending, start=1):
        email = lead["email"]
        rendered = render_email(template, lead, template_name)
        subject = rendered["subject"]
        body = rendered["body"]

        if dry_run:
            print(f"[DRY] {idx}/{total_pending} -> {email} | {subject}")
            rec: Dict[str, Any] = {
                "template": template_name,
                "email": email,
                "subject": subject,
                "status": "dry_run",
                "ts": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
            append_tracking(rec)
            stats["sent"] += 1
            stats["details"].append({"email": email, "subject": subject, "status": "dry_run"})
            continue

        last_error: Optional[str] = None
        for attempt in range(1 + cfg.RETRY_ON_FAILURE):
            res = run_gog_send(account, email, subject, body)
            if res["ok"]:
                print(f"[OK] {idx}/{total_pending} -> {email} | {subject}")
                rec = {
                    "template": template_name,
                    "email": email,
                    "subject": subject,
                    "status": "sent",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "error": None,
                }
                append_tracking(rec)
                stats["sent"] += 1
                stats["details"].append({"email": email, "subject": subject, "status": "sent"})
                break
            else:
                last_error = res.get("stderr") or res.get("stdout") or "erro desconhecido"
                if attempt < cfg.RETRY_ON_FAILURE:
                    wait = cfg.RATE_LIMIT_SLEEP * (2 ** attempt)
                    print(f"[RETRY] {idx}/{total_pending} -> {email} (tentativa {attempt+1}/{1+cfg.RETRY_ON_FAILURE}): {last_error} — aguardando {wait}s")
                    time.sleep(wait)
                else:
                    print(f"[FAIL] {idx}/{total_pending} -> {email} | {subject} | {last_error}")
                    rec = {
                        "template": template_name,
                        "email": email,
                        "subject": subject,
                        "status": "failed",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "error": last_error,
                    }
                    append_tracking(rec)
                    stats["failed"] += 1
                    stats["details"].append({"email": email, "subject": subject, "status": "failed", "error": last_error})
        else:
            stats["retries_used"] += cfg.RETRY_ON_FAILURE

        # Rate limit entre envios (exceto no último ou em dry_run)
        if not dry_run and idx < total_pending:
            time.sleep(cfg.RATE_LIMIT_SLEEP)

    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline de cold outreach via Gmail")
    parser.add_argument("--leads", type=Path, default=None, help="Caminho para leads.json")
    parser.add_argument("--template", type=str, default="cold_outreach", help="Nome do template")
    parser.add_argument("--max-sends", type=int, default=None, help="Limite de envios nesta execução")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Simular sem enviar")
    parser.add_argument("--account", type=str, default=None, help="Conta Gmail (padrao: kleber@ziontechgroup.com)")
    parser.add_argument("--json-output", action="store_true", help="Imprimir stats em JSON no stdout")
    args = parser.parse_args()

    stats = pipeline(
        leads_file=args.leads,
        template_name=args.template,
        max_sends=args.max_sends,
        dry_run=args.dry_run or (cfg.DRY_RUN if args.dry_run is None else False),
        account=args.account,
    )

    if args.json_output:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print("\n=== RESUMO ===")
        for k, v in stats.items():
            if k != "details":
                print(f"  {k}: {v}")
        print(f"\nDetalhes salvos em: {cfg.TRACKING_FILE}")
        if stats["details"]:
            print("\nPrimeiras 10 tentativas:")
            for d in stats["details"][:10]:
                print(f"  [{d['status']}] {d['email']} | {d['subject'][:60]}")

    sys.exit(0 if stats["failed"] == 0 else 2)
