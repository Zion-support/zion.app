#!/usr/bin/env python3
"""Converte email_discovery_results.json → zion_leads_free.json (formato do send_cold_outreach_v2.py)"""
import json, re

disc = json.load(open("automation/data/email_discovery_results.json"))
log = set()
try:
    for line in open("outreach-send-log.jsonl"):
        if line.strip():
            r = json.loads(line)
            log.add(r["to"].lower())
except: pass

leads = []
for entry in disc:
    empresa = entry.get("empresa", "")
    dominio = entry.get("dominio", "")
    servico = entry.get("servico", "AI Automation")
    site = entry.get("primary_site", "")
    for email in entry.get("personal_emails_found", []):
        el = email.lower()
        if el in log or "ziontechgroup" in el:
            continue
        leads.append({
            "empresa": empresa,
            "dominio": dominio,
            "site": site,
            "contato_proventivo": email,
            "email": email,
            "servico_relevante": servico,
            "servicos_interesse": [servico],
        })

# Deduplicar por email
seen = set()
uniq = []
for l in leads:
    k = l["email"].lower()
    if k not in seen:
        seen.add(k)
        uniq.append(l)

print(f"Leads prontos para envio: {len(uniq)}")
for l in uniq:
    print(f"  {l['email']} ← {l['empresa']} [{l['servico_relevante']}]")

json.dump(uniq, open("automation/data/zion_leads_free.json", "w"), indent=2, ensure_ascii=False)
print(f"\nSalvo em automation/data/zion_leads_free.json ({len(uniq)} leads)")
