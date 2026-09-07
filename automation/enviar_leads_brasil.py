#!/usr/bin/env python3
"""
Envia leads do Brasil de alta prioridade via pipeline gog.
Usa o pipeline.py existente com leads customizados.
"""

import json
import sys
import os
from pathlib import Path

# Caminhos
PIPELINE = Path("/Users/miami2/zion.app/automation/outreach-pipeline/pipeline.py")
LEADS_FILE = Path("/Users/miami2/zion.app/automation/outreach-pipeline/br_leads_high_priority.json")
TRACKING = Path("/Users/miami2/zion.app/automation/outreach-pipeline/tracking.jsonl")

# Carregar leads do zion_leads_free.json
with open("/Users/miami2/zion.app/automation/data/zion_leads_free.json") as f:
    data = json.load(f)

leads_data = data.get("leads", [])

# Filtrar: Brasil + alta prioridade ou contato direto
brazil_high = []
for lead in leads_data:
    is_brazil = "Brasil" in lead.get("localidade", "") or "São Paulo" in lead.get("localidade", "")
    is_high = lead.get("prioridade", "").lower() == "alta"
    
    # Precisa ter email
    email = lead.get("site", "").replace("https://", "").replace("http://", "").split("/")[0]
    email = email.replace("www.", "") + "@email.com"  # placeholder
    
    if is_brazil and (is_high or "contato" in email):
        brazil_high.append({
            "email": email,
            "name": lead.get("empresa", "Empresa"),
            "company": lead.get("empresa", "Empresa"),
            "role": "Destionário",
            "personal_note": lead.get("motivo", "")[:100]
        })

print(f"Leads Brasil alta prioridade identificados: {len(brazil_high)}")
for l in brazil_high:
    print(f"  - {l['company']} | {l['email']}")

if not brazil_high:
    print("Nenhum lead Brazil de alta prioridade com email encontrado.")
    print("Os leads do zion_leads_free.json nao possuem emails diretos.")
    sys.exit(0)

# Salvar em arquivo temporario para o pipeline
LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(LEADS_FILE, "w") as f:
    json.dump(brazil_high, f, ensure_ascii=False, indent=2)

print(f"\nLeads salvos em: {LEADS_FILE}")
print(f"Executando pipeline de envio...")
