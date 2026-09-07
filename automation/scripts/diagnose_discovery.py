import json
from pathlib import Path

disc = json.loads(Path('email_discovery_results.json').read_text())
total = len(disc)
print(f'Total entries: {total}')
print()

empty_personal = [e for e in disc if not e.get('personal_emails_found')]
has_personal = [e for e in disc if e.get('personal_emails_found')]
print(f'Has personal_emails_found: {len(has_personal)}')
print(f'Empty personal_emails_found: {len(empty_personal)}')
print()

print('=== Sample entries with empty personal_emails_found ===')
for e in empty_personal[:5]:
    print(f'  empresa: {e["empresa"]}')
    print(f'    dominio: {e.get("dominio","")}')
    print(f'    assunto_original: {e.get("assunto_original","")}')
    print(f'    servico: {e.get("servico","")}')
    print(f'    personal_emails_found: {e.get("personal_emails_found",[])}')
    print(f'    sources: {e.get("sources",[])}')
    print()
