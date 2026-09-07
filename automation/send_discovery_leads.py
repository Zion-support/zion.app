#!/usr/bin/env python3
"""Wrapper: converte zion_leads_free.json (lista) → formato send_cold_outreach_v2.py e envia"""
import json, subprocess, sys, os
from pathlib import Path

LEADS_PATH = Path("/Users/miami2/zion.app/automation/data/zion_leads_free.json")
WRAPPER_PATH = Path("/tmp/zion_outreach_wrapper.json")

# Ler leads (formato lista)
with open(LEADS_PATH) as f:
    leads_list = json.load(f)

# Converter para formato { "leads": [...] }
wrapper = {"leads": leads_list}
WRAPPER_PATH.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2))
print(f"Converted {len(leads_list)} leads → {WRAPPER_PATH}")

# Rodar send_cold_outreach v2 com o arquivo convertido
env = os.environ.copy()
result = subprocess.run(
    ["python3", "/Users/miami2/zion.app/automation/send_cold_outreach_v2.py"],
    capture_output=True, text=True, timeout=120, env=env
)
print(result.stdout[-3000:] if result.stdout else "")
if result.stderr:
    print("STDERR:", result.stderr[-1000:])
print(f"EXIT CODE: {result.returncode}")
