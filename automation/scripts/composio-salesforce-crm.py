#!/usr/bin/env python3
"""
composio-salesforce-crm.py
==========================
Salesforce CRM — gestão enterprise de clientes grandes do Zion.

 Fluxos:
   - Listar/contatos de clientes grandes
   - Criar oportunidades
   - Sync HubSpot → Salesforce (para enterprise deals)
   - Relatórios de pipeline enterprise
   - Notificar Slack

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export SALESFORCE_INSTANCE_URL="https://ziontechgroup.my.salesforce.com"
   export SALESFORCE_ACCESS_TOKEN="..."
   export ZION_SLACK_CHANNEL="#salesforce"
   
   python composio-salesforce-crm.py list-accounts
   python composio-salesforce-crm.py list-opportunities
   python composio-salesforce-crm.py create-opportunity "Empresa X" 50000 "Prospecting"
   python composio-salesforce-crm.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SALESFORCE_INSTANCE_URL = os.environ.get("SALESFORCE_INSTANCE_URL", "")
SALESFORCE_ACCESS_TOKEN = os.environ.get("SALESFORCE_ACCESS_TOKEN", "")
ZION_SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#salesforce")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
ACCOUNT_NAME = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
OPPORTUNITY_AMOUNT = None
OPPORTUNITY_STAGE = None

if len(sys.argv) > 3:
    OPPORTUNITY_AMOUNT = sys.argv[3]
if len(sys.argv) > 4:
    OPPORTUNITY_STAGE = " ".join(sys.argv[4:])

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
    """Notifica no Slack."""
    sdk = get_sdk()
    return tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": ZION_SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )

# ========== CRM FUNCTIONS ==========

def list_accounts():
    """Lista accounts (empresas) no Salesforce."""
    print(f"   🏢 Listando accounts no Salesforce...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SALESFORCE_LIST_ACCOUNTS",
        arguments={
            "instance_url": SALESFORCE_INSTANCE_URL,
            "access_token": SALESFORCE_ACCESS_TOKEN,
            "limit": 50,
        },
        user_id="zion-bot",
    )
    
    accounts = result.get("records", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(accounts)} accounts encontradas")
    
    for account in accounts[:10]:
        name = account.get("Name", "N/A")
        industry = account.get("Industry", "N/A")
        revenue = account.get("AnnualRevenue", "N/A")
        print(f"     {name} ({industry}) — R${revenue}")
    
    return accounts

def list_opportunities():
    """Lista opportunities (oportunidades) no Salesforce."""
    print(f"   💰 Listando opportunities...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SALESFORCE_LIST_OPPORTUNITIES",
        arguments={
            "instance_url": SALESFORCE_INSTANCE_URL,
            "access_token": SALESFORCE_ACCESS_TOKEN,
            "limit": 50,
        },
        user_id="zion-bot",
    )
    
    opps = result.get("records", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(opps)} opportunities encontradas")
    
    for opp in opps[:10]:
        name = opp.get("Name", "N/A")
        amount = opp.get("Amount", 0)
        stage = opp.get("StageName", "N/A")
        close_date = opp.get("CloseDate", "N/A")
        print(f"     {name} — R${amount} — {stage} — {close_date}")
    
    return opps

def create_opportunity(account_name, amount, stage="Prospecting"):
    """Cria opportunity no Salesforce."""
    print(f"   💰 Criando opportunity: {account_name} — R${amount} — {stage}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SALESFORCE_CREATE_OPPORTUNITY",
        arguments={
            "instance_url": SALESFORCE_INSTANCE_URL,
            "access_token": SALESFORCE_ACCESS_TOKEN,
            "Name": f"Zion Services — {account_name}",
            "Amount": int(amount) if amount else 0,
            "StageName": stage,
            "CloseDate": datetime.now().strftime("%Y-%m-%d"),
            "Description": f"Oportunidade criada automaticamente pelo Salesforce Agent.",
        },
        user_id="zion-bot",
    )
    
    if result:
        opp_id = result.get("id", result.get("OpportunityId", ""))
        print(f"   ✅ Opportunity criado: {opp_id}")
        slack_notify(f"*💰 Nova Opportunity — {datetime.now().strftime('%H:%M')}*\n\n**Account:** {account_name}\n**Valor:** R${amount}\n**Stage:** {stage}")
        return opp_id
    print(f"   ⚠️  Falha ao criar opportunity")
    return None

def sync_hubspot_to_salesforce():
    """Sync HubSpot enterprise deals → Salesforce."""
    print(f"   🔄 Syncando HubSpot → Salesforce (enterprise deals)...")
    
    sdk = get_sdk()
    
    # Fetch HubSpot deals com valor alto (enterprise = > R$50k)
    hubspot_result = tool_execute(
        sdk,
        "HUBSPOT_LIST_DEALS",
        arguments={
            "properties": ["dealname", "amount", "dealstage", "closedate", "company"],
            "filter": {
                "amount": {"gt": 50000},
            },
            "limit": 50,
        },
        user_id="zion-bot",
    )
    
    deals = hubspot_result.get("deals", []) if isinstance(hubspot_result, dict) else []
    print(f"   ✅ {len(deals)} enterprise deals encontrados no HubSpot")
    
    created = 0
    for deal in deals:
        fields = {
            "Name": f"Zion Services — {deal.get('company', {}).get('name', 'N/A')}",
            "Amount": deal.get("amount", 0),
            "StageName": deal.get("dealstage", "Prospecting"),
            "CloseDate": deal.get("closedate", datetime.now().strftime("%Y-%m-%d")),
            "Description": f"Syncado do HubSpot. Deal: {deal.get('dealname', '')}",
        }
        
        salesforce_result = tool_execute(
            sdk,
            "SALESFORCE_CREATE_OPPORTUNITY",
            arguments={
                "instance_url": SALESFORCE_INSTANCE_URL,
                "access_token": SALESFORCE_ACCESS_TOKEN,
                **fields,
            },
            user_id="zion-bot",
        )
        
        if salesforce_result:
            created += 1
            print(f"   ✅ Syncado: {deal.get('dealname', 'N/A')}")
    
    print(f"   ✅ {created} opportunities syncados para Salesforce")
    slack_notify(f"*🔄 Sync HubSpot → Salesforce — {datetime.now().strftime('%H:%M')}*\n\n{created} enterprise opportunities syncados")
    return created

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Salesforce CRM — Uso:

  python composio-salesforce-crm.py list-accounts
      Lista accounts (empresas) no Salesforce

  python composio-salesforce-crm.py list-opportunities
      Lista opportunities no Salesforce

  python composio-salesforce-crm.py create-opportunity "Empresa" 50000 "Prospecting"
      Cria opportunity no Salesforce

  python composio-salesforce-crm.py sync-hubspot
      Sync HubSpot enterprise deals → Salesforce

  python composio-salesforce-crm.py --dry-run
      Testa configuração sem executar

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export SALESFORCE_INSTANCE_URL='https://ziontechgroup.my.salesforce.com'
  export SALESFORCE_ACCESS_TOKEN='...'
  python composio-salesforce-crm.py create-opportunity "Empresa X" 100000 "Prospecting"
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não executando")
        if ACTION == "create-opportunity":
            print(f"   Account: {ACCOUNT_NAME}")
            print(f"   Valor: R${OPPORTUNITY_AMOUNT}")
            print(f"   Stage: {OPPORTUNITY_STAGE}")
        return
    
    if ACTION == "list-accounts":
        list_accounts()
        slack_notify(f"*🏢 Salesforce Accounts — {datetime.now().strftime('%H:%M')}*\n\nAccounts listados")
    
    elif ACTION == "list-opportunities":
        list_opportunities()
        slack_notify(f"*💰 Salesforce Opportunities — {datetime.now().strftime('%H:%M')}*\n\nOpportunities listados")
    
    elif ACTION == "create-opportunity":
        if not ACCOUNT_NAME or not OPPORTUNITY_AMOUNT:
            print("❌ Account e valor necessários")
            print("Uso: python composio-salesforce-crm.py create-opportunity \"Empresa\" 50000 [stage]")
            sys.exit(1)
        create_opportunity(ACCOUNT_NAME, OPPORTUNITY_AMOUNT, OPPORTUNITY_STAGE or "Prospecting")
    
    elif ACTION == "sync-hubspot":
        sync_hubspot_to_salesforce()
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
