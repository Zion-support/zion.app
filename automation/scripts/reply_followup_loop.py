#!/usr/bin/env python3
"""Reply-triggered followup loop for Zion autonomous growth.

Design:
- Scans outreach ledgers for real inbound reply signals from known statuses/labels.
- Sends a tailored follow-up only if a reply state is detected.
- Otherwise exits healthy with 0 followups to avoid spamming.
- No-op if no reply-detecting data source is available yet.
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path('/Users/miami2/zion.app')
DISCOVERED = REPO / 'app' / 'data' / 'discovered_leads.json'
LEDGER = REPO / 'outreach_monitor' / 'processed' / 'hot_followup_reply_ledger.jsonl'
LEDGER2 = REPO / 'lead-crm' / 'outreach_sent_history.jsonl'
LEDGER3 = REPO / 'lead-crm' / 'ceo_outreach_ledger.jsonl'
RUN_REPORT = REPO / 'automation' / 'reports' / 'reply-followup-loop-latest.json'
MAX_FOLLOWUPS_PER_RUN = 3
FOLLOWUP_DELAY_SEC = 1

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _now_iso() -> str:
    return _now().isoformat()

def _append_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

def _load_jsonl_sent_emails() -> dict:
    """Return email->last_record mapping from known outreach ledgers."""
    sent = {}
    for path in [LEDGER2, LEDGER3, LEDGER]:
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                to = str(obj.get('to') or obj.get('email') or '').strip().lower()
                if to:
                    sent[to] = obj
        except Exception:
            pass
    return sent


_TRUE_REPLY_RE = re.compile(r'\b(replied|reply|re)\b', re.IGNORECASE)
_HOT_LABEL_HINT_RE = re.compile(r'hot[- ]follow[- ]?up|reply|re:', re.IGNORECASE)

def _looks_real_reply(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if len(t) < 15:
        return False
    if _TRUE_REPLY_RE.search(t):
        return True
    if '>>>' in t or 'wrote:' in t.lower() or 'on ' in t.lower():
        return True
    return False

def _extract_reply_state_from_ledger(path: Path) -> dict:
    """Best-effort: infer whether inbound replies exist in ledger labels/fields."""
    replies = {}
    if not path.exists():
        return replies
    try:
        for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            to = str(obj.get('to') or obj.get('email') or '').strip().lower()
            if not to:
                continue
            status = str(obj.get('status') or obj.get('label') or obj.get('provider_status') or '').lower()
            subject = str(obj.get('subject') or '')
            body_snip = str(obj.get('body_snippet') or obj.get('text') or obj.get('body') or '')
            if _TRUE_REPLY_RE.search(status) or 'reply' in status:
                replies[to] = {'source': str(path), 'status': status, 'subject': subject}
                continue
            if _looks_real_reply(body_snip) and 'sent' != status:
                replies[to] = {'source': str(path), 'status': status or 'body_reply_like', 'subject': subject}
    except Exception:
        pass
    return replies

def _load_discovered():
    if not DISCOVERED.exists():
        return []
    try:
        d = json.loads(DISCOVERED.read_text(encoding='utf-8'))
        return d if isinstance(d, list) else []
    except Exception:
        return []

def _send_gog(to: str, subject: str, body: str):
    safe_subject = subject.replace('"', "'")
    body_file = REPO / 'automation' / 'reports' / f"body-{_now().timestamp()}-{to.split('@')[0]}.txt"
    body_file.write_text(body, encoding='utf-8')
    cmd = (
        'gog gmail send --to "' + to + '" --subject "'
        + safe_subject + '" --body-file "'
        + str(body_file)
        + '" --account kleber@ziontechgroup.com --no-input'
    )
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    mid = None
    for ln in (out.stdout or '').splitlines():
        if ln.startswith('message_id\t'):
            mid = ln.split('\t', 1)[1].strip()
    try:
        body_file.unlink()
    except Exception:
        pass
    if out.returncode != 0 or not mid:
        raise RuntimeError((out.stderr or out.stdout or 'gog failed').strip()[:300])
    return mid

def main():
    run_id = _now().strftime('%Y%m%d-%H%M%S')
    send_attempted = 0
    send_succeeded = 0
    send_failed = 0
    selected = []
    errors = []

    replies = {}
    for p in [LEDGER, LEDGER2, LEDGER3]:
        replies.update(_extract_reply_state_from_ledger(p))
    sent_map = _load_jsonl_sent_emails()
    discovered = _load_discovered()
    discovered_by_email = {
        str(x.get('email') or '').strip().lower(): x for x in discovered if isinstance(x, dict) and x.get('email')
    }

    for to, reply_meta in replies.items():
        if send_attempted >= MAX_FOLLOWUPS_PER_RUN:
            break
        if to in sent_map:
            continue
        lead = discovered_by_email.get(to)
        name = (lead.get('name') or 'Contact') if lead else 'Contact'
        name = str(name).split()[0]
        subject = reply_meta.get('subject') or f"Re: next step for {lead.get('company') if lead else 'your team'}"
        body = (
            f"{name},\n"
            "Thanks for the reply.\n"
            "Short next step:\n"
            "- 15-minute working session with measurable outcomes\n"
            "- A 30-day automation/AI pilot with clear KPIs\n\n"
            "If useful, I'll send a lightweight proposal first.\n\n"
            "Best,\n"
            "Kleber Garcia Alcatrão\n"
            "CEO, Zion Tech Group\n"
            "https://ziontechgroup.com"
        )
        send_attempted += 1
        try:
            mid = _send_gog(to, subject, body)
            send_succeeded += 1
            _append_jsonl(LEDGER, {
                'ts': _now_iso(),
                'to': to,
                'subject': subject,
                'message_id': mid,
                'status': 'followup_sent',
                'trigger': 'reply',
            })
            selected.append({'to': to, 'message_id': mid, 'subject': subject, 'trigger': 'reply'})
        except Exception as e:
            send_failed += 1
            errors.append({'to': to, 'error': str(e)[:300]})
        time.sleep(FOLLOWUP_DELAY_SEC)

    report = {
        'ts': _now_iso(),
        'run_id': run_id,
        'mode': 'reply_followup',
        'reply_signals_found': len(replies),
        'send_attempted': send_attempted,
        'send_succeeded': send_succeeded,
        'send_failed': send_failed,
        'selected': selected,
        'errors': errors,
    }
    RUN_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
