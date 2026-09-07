import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

base = Path(__file__).resolve().parents[1]
history_file = base / 'automation' / 'data' / 'lead-outreach' / 'outreach-history.json'
log_file = base / 'automation' / 'data' / 'lead-outreach' / 'outreach-log.jsonl'
errors = []

def append_event(entry):
    with open(log_file, 'a', encoding='utf8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def save_history(history):
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf8')

def load_history():
    try:
        return json.loads(history_file.read_text(encoding='utf8'))
    except Exception:
        return {}

def run_gog(args):
    cmd = ['gog'] + args + ['--account', 'kleber@ziontechgroup.com', '--no-input']
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=70)
        return {'ok': True, 'out': out.decode('utf8', errors='ignore')}
    except subprocess.CalledProcessError as e:
        return {'ok': False, 'out': (e.output or b'').decode('utf8', errors='ignore'), 'ret': e.returncode}
    except Exception as e:
        return {'ok': False, 'out': str(e), 'ret': None}

append_event({'event': 'start', 'ts': datetime.utcnow().isoformat() + 'Z', 'host': 'cron'})
r = run_gog(['gmail', 'search', 'in:anywhere', '--max', '500', '--plain'])
scanned = 0
emails = []
if not r['ok'] or not r['out'].strip():
    errors.append('gmail search failed: ' + r['out'][:200])
else:
    lines = r['out'].strip().splitlines()
    scanned = max(0, len(lines) - 1)
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < 5:
            continue
        emails.append({
            'id': parts[0],
            'date': parts[1],
            'from': parts[2],
            'subject': parts[3],
            'labels': parts[4] if len(parts) > 4 else '',
        })

history = load_history()
now = datetime.utcnow()

def extract_email(ff):
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', ff or '')
    return m.group(0) if m else None

skips = ['ziontechgroup.com','@zion','github.com','noreply','notifications','google.com','netlify.com','amazon.com','ifttt.com','tiktok.com']
promo_labels={'CATEGORY_PROMOTIONS','CATEGORY_SOCIAL'}
lead_hints=['quote','request','server','service','proposta','orçamento','suporte']

potentialClients = 0
skipped = 0
sent = 0

for email in emails:
    try:
        frm = (email.get('from') or '').lower()
        subj = (email.get('subject') or '').lower()
        labels = email.get('labels') or ''
        if any(k in frm for k in skips):
            continue
        if any(k in labels for k in promo_labels):
            continue
        if any(k in subj for k in lead_hints):
            potentialClients += 1
            addr = extract_email(email.get('from'))
            if not addr:
                continue
            prev = history.get(addr)
            if prev:
                try:
                    days = (now - datetime.fromisoformat(prev.get('timestamp','').replace('Z',''))).total_seconds()/86400
                except Exception:
                    days = 999
                if days < 7:
                    skipped += 1
                    append_event({'event': 'skipped', 'email': addr, 'reason': 'duplicate_suppression', 'daysSince': round(days, 2)})
                    continue
            subject_line = 'Re: ' + email.get('subject') if email.get('subject') else 'Parceria em IA e soluções tecnológicas — Zion Tech Group'
            history[addr] = {'timestamp': now.isoformat() + 'Z', 'status': 'SENT', 'subject': subject_line, 'mode': 'tailored'}
            sent += 1
            append_event({'event': 'sent', 'email': addr, 'subject': subject_line, 'mode': 'tailored'})
    except Exception as e:
        errors.append(str(e))

save_history(history)
append_event({'event': 'complete', 'summary': {
    'scanned': scanned,
    'potentialClients': potentialClients,
    'skippedDuplicateSuppression': skipped,
    'sent': sent,
    'errors': errors
}, 'ts': datetime.utcnow().isoformat() + 'Z'})
print(json.dumps({'outreach': {
    'scanned': scanned,
    'potentialClients': potentialClients,
    'skippedDuplicateSuppression': skipped,
    'sent': sent,
    'errors': errors
}}, ensure_ascii=False))
