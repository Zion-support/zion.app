#!/usr/bin/env python3
"""zion_email_interaction_agent.py - Email intelligence processing agent.
Delegates to the gog-based email pipeline in lead-crm.
"""
import subprocess, sys, os

def main():
    # Probe auth first
    r = subprocess.run(['gog', 'gmail', 'search', 'in:anywhere', '--max', '1', '--plain', '--no-input', '--account', 'kleber@ziontechgroup.com'],
                      capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        print('AUTH_BLOCKED: gog gmail probe failed')
        return 1
    
    # Check for unread emails - process inbox
    r2 = subprocess.run(['gog', 'gmail', 'search', 'is:unread', '--max', '25', '--plain', '--no-input', '--account', 'kleber@ziontechgroup.com'],
                       capture_output=True, text=True, timeout=15)
    if r2.returncode != 0:
        print('SCAN_FAILED: unread search failed')
        return 1
    
    lines = [l for l in r2.stdout.splitlines() if l.strip() and not l.startswith('ID\t')]
    if len(lines) <= 1:
        print('NO_UNREAD_EMAILS')
        return 0
    
    print(f'FOUND {len(lines)-1} unread emails')
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) >= 4:
            email_id, date, sender, subject = parts[0], parts[1], parts[2], parts[3]
            print(f'  [{date}] {sender} - {subject}')
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
