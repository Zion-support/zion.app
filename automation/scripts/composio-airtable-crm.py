#!/usr/bin/env python3
"""
composio-airtable-crm.py
==========================
Airtable CRM — gestão de leads, pipeline, e clientes do Zion.

 Fluxos:
   - Criar/Atualizar records no Airtable
   - Listar pipeline de leads
   - Sync HubSpot → Airtable
   - Gerar relatórios de pipeline
   - Notificar Slack sobre mudanças

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#crm"
   export AIRTABLE_BASE_ID="..."
   export AIRTABLE_TABLE_ID="..."
   
   python composio-airtable-crm.py list-leads
   python composio-airtable-crm.py create-lead "Empresa X" "email@x.com" "Lead Quente"
   python composio-airtable-crm.py sync-hubspot
   python composio-airtable-crm.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_ID = os.environ.get("AIRTABLE_TABLE_ID", "")
ZION_SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#crm")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
COMPANY = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
EMAIL = None
STATUS = None

if len(sys.argv) > 3:
    EMAIL = sys.argv[3]
if len(sys.argv) > 4:
    STATUS = " ".join(sys.argv[4:])

# ========== SDK ==========
def get_sdk():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    return Composio(api_key=COMPOSIO_API_KEY)

def tool_execute(sdk, tool_name, args, user_id="zion-bot"):
    try:
        return sdk.tools.execute(tool_name, arguments=args, user_id=user_id)
    except Exception as e:
        print(f"  ⚠️  Erro em {tool_name}: {e}")
        return None

def slack_notify(message):
    """Notifica Slack."""
    sdk = get_sdk()
    return tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": ZION_SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )

# ========== CRM FUNCTIONS ==========

def list_leads(table_id=None):
    """Lista leads do pipeline."""
    table = table_id or AIRTABLE_TABLE_ID
    print(f"   📋 Listando leads do pipeline...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "AIRTABLE_LIST_RECORDS",
        arguments={
            "base_id": AIRTABLE_BASE_ID,
            "table_id": table,
        },
        user_id="zion-bot",
    )
    
    records = result.get("records", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(records)} leads encontrados")
    
    for record in records[:10]:
        fields = record.get("fields", {})
        company = fields.get("Empresa", fields.get("Company", "N/A"))
        status = fields.get("Status", fields.get("Stage", "N/A"))
        email = fields.get("Email", "N/A")
        print(f"     {company} — {status} — {email}")
    
    return records

def create_lead(company, email, status="Lead Quente"):
    """Cria lead no Airtable."""
    print(f"   📋 Criando lead: {company} ({email})...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "AIRTABLE_CREATE_RECORD",
        arguments={
            "base_id": AIRTABLE_BASE_ID,
            "table_id": AIRTABLE_TABLE_ID,
            "fields": {
                "Empresa": company,
                "Email": email,
                "Status": status,
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Source": "Composio Automation",
            },
        },
        user_id="zion-bot",
    )
    
    if result:
        record_id = result.get("id", result.get("recordId", ""))
        print(f"   ✅ Lead criado: {record_id}")
        slack_notify(f"*📋 Novo Lead — {datetime.now().strftime('%H:%M')}*\n\n**Empresa:** {company}\n**Email:** {email}\n**Status:** {status}")
        return record_id
    return None

def sync_hubspot_to_airtable():
    """Sync HubSpot deals → Airtable."""
    print(f"   🔄 Syncando HubSpot → Airtable...")
    
    sdk = get_sdk()
    
    # Fetch HubSpot deals
    hubspot_result = tool_execute(
        sdk,
        "HUBSPOT_LIST_DEALS",
        arguments={
            "properties": ["dealname", "amount", "dealstage", "closedate", "company"],
            "limit": 50,
        },
        user_id="zion-bot",
    )
    
    deals = hubspot_result.get("deals", []) if isinstance(hubspot_result, dict) else []
    print(f"   ✅ {len(deals)} deals encontrados no HubSpot")
    
    # Create in Airtable
    created = 0
    for deal in deals:
        fields = {
            "Empresa": deal.get("company", {}).get("name", "N/A"),
            "Deal Name": deal.get("dealname", "N/A"),
            "Valor": deal.get("amount", 0),
            "Status": deal.get("dealstage", "N/A"),
            "Data Fechamento": deal.get("closedate", ""),
        }
        
        airtable_result = tool_execute(
            sdk,
            "AIRTABLE_CREATE_RECORD",
            arguments={
                "base_id": AIRTABLE_BASE_ID,
                "table_id": AIRTABLE_TABLE_ID,
                "fields": fields,
            },
            user_id="zion-bot",
        )
        
        if airtable_result:
            created += 1
    
    print(f"   ✅ {created} records syncados para Airtable")
    slack_notify(f"*🔄 Sync HubSpot → Airtable — {datetime.now().strftime('%H:%M')}*\n\n{created} deals syncados para CRM")
    return created

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Airtable CRM — Uso:

  python composio-airtable-crm.py list-leads
      Lista pipeline de leads no Airtable

  python composio-airtable-crm.py create-lead "Empresa" "email@x.com" "Lead Quente"
      Cria lead no Airtable

  python composio-airtable-crm.py sync-hubspot
      Sync HubSpot deals → Airtable

  python composio-airtable-crm.py --dry-run
      Testa configuração sem criar records

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export AIRTABLE_BASE_ID='appXXXXXXXXXXXXXX'
  export AIRTABLE_TABLE_ID='tblXXXXXXXXXXXXXX'
  python composio-airtable-crm.py create-lead "Empresa X" "contato@empresa.com" "Lead Quente"
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não criando records")
        if ACTION == "create-lead":
            print(f"   Empresa: {COMPANY}")
            print(f"   Email: {EMAIL}")
            print(f"   Status: {STATUS}")
        return
    
    if ACTION == "list-leads":
        list_leads()
    
    elif ACTION == "create-lead":
        if not COMPANY or not EMAIL:
            print("❌ Empresa e email necessários")
            print("Uso: python composio-airtable-crm.py create-lead \"Empresa\" \"email@x.com\" [status]")
            sys.exit(1)
        create_lead(COMPANY, EMAIL, STATUS or "Lead Quente")
    
    elif ACTION == "sync-hubspot":
        sync_hubspot_to_airtable()
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
