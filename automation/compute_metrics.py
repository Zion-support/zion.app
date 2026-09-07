import json
from pathlib import Path
from collections import Counter

log_path = Path('/Users/miami2/zion-pages-repo/lead-crm/outreach-log.jsonl')
lines = [l for l in log_path.read_text().splitlines() if l.strip()]
total = len(lines)

send_count = 0
recip_counter = Counter()
auth_fail = 0
hot_fu = 0
latest_ts = None

for l in lines:
    r = json.loads(l)
    ev = r.get('event','?')
    if ev == 'send':
        send_count += 1
        recip_counter[r['to']] += 1
        ts = r.get('ts','')
        if ts and (latest_ts is None or ts > latest_ts):
            latest_ts = ts
    errs = r.get('errors', [])
    if isinstance(errs, list):
        for e in errs:
            if 'No auth for gmail' in str(e):
                auth_fail += 1

duplicates_suppressed = sum(c-1 for c in recip_counter.values() if c > 1)
unique_recipients = len(recip_counter)
unique_domains = len(set(r.split('@')[-1] for r in recip_counter.keys() if '@' in r))
unique_subjects = len(set(r.get('subject','') for r in [json.loads(l) for l in lines] if r.get('subject')))

print('totalRuns:', total)
print('sendsAttempted:', send_count)
print('duplicatesSuppressed:', duplicates_suppressed)
print('authFailures:', auth_fail)
print('hotFollowups:', hot_fu)
print('latestComplete:', latest_ts)
print('uniqueRecipients:', unique_recipients)
print('uniqueDomains:', unique_domains)
print('uniqueSubjects:', unique_subjects)
