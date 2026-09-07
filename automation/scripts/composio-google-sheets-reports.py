#!/usr/bin/env python3
"""
composio-google-sheets-reports.py
======================================
Relatórios automatizados para Google Sheets — métricas de growth, finanças, operações.

 Fluxos suportados:
   - Gerar relatório diário de métricas do site (PostHog) e salvar no Google Sheets
   - Atualizar dashboard financeiro com receita do Stripe
   - Criar relatório semanal de leads (HubSpot) no Google Sheets
   - Exportar métricas de deploy (Vercel) para planilha de operações

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export GOOGLE_SHEETS_SPREADSHEET_ID="..."
   export ZION_SLACK_CHANNEL="#reports"
   
   python composio-google-sheets-reports.py daily-metrics
   python composio-google-sheets-reports.py weekly-leads
   python composio-google-sheets-reports.py finance-dashboard
   python composio-google-sheets-reports.py daily --sheet "Relatório Diário"
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SPREADSHEET_ID = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#reports")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
SHEET_NAME = sys.argv[2] if len(sys.argv) > 2 else "Relatório Automático"

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

# ========== FUNÇÕES ==========

def sheet_check_config():
    """Verifica se planilha configurada existe."""
    if not SPREADSHEET_ID:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID não configurada")
        print("Exemplo: export GOOGLE_SHEETS_SPREADSHEET_ID='1abc123xyz...'")
        sys.exit(1)
    return SPREADSHEET_ID

def sheet_append_row(spreadsheet_id, sheet_name, values):
    """Adiciona linha ao sheet."""
    print(f"   📊 Adicionando linha em '{sheet_name}'...")
    
    result = tool_execute(
        get_sdk(),
        "GOOGLESHEETS_APPEND_ROW",
        arguments={
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "values": [values],
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Linha adicionada")
        return True
    return False

def sheet_update_cell(spreadsheet_id, sheet_name, cell, value):
    """Atualiza célula específica."""
    print(f"   📝 Atualizando {cell}...")
    
    result = tool_execute(
        get_sdk(),
        "GOOGLESHEETS_UPDATE_CELL",
        arguments={
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "cell": cell,
            "value": value,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Célula atualizada")
        return True
    return False

def get_today_header():
    """Gera header com data e hora."""
    now = datetime.now()
    return {
        "data": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M"),
        "timestamp": now.isoformat(),
    }

# ========== RELATÓRIOS ==========

def daily_metrics():
    """Relatório diário de métricas do site (PostHog → Google Sheets)."""
    print(f"\n📊 Gerando relatório diário de métricas...")
    sheet_check_config()
    header = get_today_header()
    
    # Obter métricas do PostHog
    sdk = get_sdk()
    
    print("   📡 Consultando PostHog...")
    posthog_result = tool_execute(
        sdk,
        "POSTHOG_FETCH_EVENTS",
        arguments={
            "api_key": os.environ.get("POSTHOG_API_KEY", ""),
            "url": os.environ.get("POSTHOG_URL", "https://app.posthog.com"),
            "days": 1,
        },
        user_id="zion-bot",
    )
    
    visitors = posthog_result.get("visitors", 0) if isinstance(posthog_result, dict) else 0
    events = posthog_result.get("events", 0) if isinstance(posthog_result, dict) else 0
    
    print(f"   Visitantes: {visitors} | Eventos: {events}")
    
    # Adicionar linha no sheet
    sheet_name = SHEET_NAME
    sheet_append_row(SPREADSHEET_ID, sheet_name, [
        header["data"],
        header["hora"],
        visitors,
        events,
        "posthog",
    ])
    
    # Slack notification
    message = f"*📊 Daily Metrics — {header['data']}*\n\n"
    message += f"🌐 Visitantes: **{visitors}**\n"
    message += f"⚡ Eventos: **{events}**\n"
    message += f"_Atualizado em {header['hora']}_"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )
    
    print(f"   📤 Slack notificado")

def weekly_leads():
    """Relatório semanal de leads (HubSpot → Google Sheets)."""
    print(f"\n📋 Gerando relatório semanal de leads...")
    sheet_check_config()
    header = get_today_header()
    
    sdk = get_sdk()
    
    print("   📡 Consultando HubSpot...")
    
    # Fetch deals recently closed
    deals_result = tool_execute(
        sdk,
        "HUBSPOT_LIST_DEALS",
        arguments={
            "properties": ["dealname", "amount", "dealstage", "closedate", "company"],
            "filter": {
                "createdate": {
                    "gte": (datetime.now() - timedelta(days=7)).isoformat(),
                },
            },
        },
        user_id="zion-bot",
    )
    
    deals = deals_result.get("deals", []) if isinstance(deals_result, dict) else []
    
    closed_won = [d for d in deals if d.get("dealstage") == "closedwon"]
    pipeline = [d for d in deals if d.get("dealstage") != "closedwon"]
    
    total_value = sum(int(d.get("amount", 0) or 0) for d in closed_won)
    
    print(f"   Deals fechados: {len(closed_won)} | Valor: R${total_value:,.2f}")
    print(f"   Em pipeline: {len(pipeline)}")
    
    # Adicionar no sheet
    sheet_append_row(SPREADSHEET_ID, SHEET_NAME, [
        header["data"],
        header["hora"],
        len(closed_won),
        total_value,
        len(pipeline),
        "hubspot",
    ])
    
    message = f"*📋 Weekly Leads Report — {header['data']}*\n\n"
    message += f"✅ Fechados: **{len(closed_won)}** (R${total_value:,.2f})\n"
    message += f"📊 Pipeline: **{len(pipeline)}**\n"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )
    
    print(f"   📤 Slack notificado")

def finance_dashboard():
    """Dashboard financeiro combinando Stripe + HubSpot."""
    print(f"\n💰 Gerando dashboard financeiro...")
    sheet_check_config()
    header = get_today_header()
    
    sdk = get_sdk()
    
    # Stripe — receita do dia
    print("   📡 Consultando Stripe...")
    stripe_result = tool_execute(
        sdk,
        "STRIPE_LIST_INVOICES",
        arguments={
            "status": "paid",
            "limit": 100,
        },
        user_id="zion-bot",
    )
    
    invoices = stripe_result.get("invoices", []) if isinstance(stripe_result, dict) else []
    today_invoices = [
        inv for inv in invoices 
        if inv.get("created", "")[:10] == datetime.now().strftime("%Y-%m-%d")
    ]
    today_revenue = sum(float(inv.get("amount_paid", 0) or 0) / 100 for inv in today_invoices)
    
    # MRR atual
    total_paid = sum(float(inv.get("amount_paid", 0) or 0) / 100 for inv in invoices)
    
    # HubSpot — deals fechados
    print("   📡 Consultando HubSpot...")
    hubspot_result = tool_execute(
        sdk,
        "HUBSPOT_LIST_DEALS",
        arguments={
            "properties": ["dealname", "amount", "dealstage", "closedate"],
            "filter": {
                "dealstage": {"eq": "closedwon"},
                "closedate": {
                    "gte": (datetime.now() - timedelta(days=30)).isoformat(),
                },
            },
        },
        user_id="zion-bot",
    )
    
    won_deals = hubspot_result.get("deals", []) if isinstance(hubspot_result, dict) else []
    mrr_hubspot = sum(int(d.get("amount", 0) or 0) for d in won_deals) / 100  # se em cents
    
    print(f"   Revenue hoje: R${today_revenue:,.2f}")
    print(f"   MRR estimado: R${mrr_hubspot:,.2f}")
    
    # Atualizar células do dashboard
    sheet_update_cell(SPREADSHEET_ID, SHEET_NAME, f"B{header['data'].replace('-', '')}", today_revenue)
    sheet_append_row(SPREADSHEET_ID, SHEET_NAME, [
        header["data"],
        header["hora"],
        today_revenue,
        mrr_hubspot,
        len(invoices),
        "finance",
    ])
    
    print(f"   ✅ Dashboard atualizado")

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if not ACTION:
        print("""
📋 Google Sheets Reports — Uso:

  python composio-google-sheets-reports.py daily-metrics
      Relatório diário de visitantes e eventos (PostHog)

  python composio-google-sheets-reports.py weekly-leads
      Relatório semanal de leads e deals (HubSpot)

  python composio-google-sheets-reports.py finance-dashboard
      Dashboard financeiro combinando Stripe + HubSpot

  python composio-google-sheets-reports.py daily <nome_do_sheet>
      Relatório diário genérico para sheet específico

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export GOOGLE_SHEETS_SPREADSHEET_ID='1abc123xyz...'
  export ZION_SLACK_CHANNEL='#reports'
  python composio-google-sheets-reports.py daily-metrics
""")
        return
    
    sheet_check_config()
    
    if DRY_RUN:
        print("🔍 Modo dry-run — não executando ações")
        print(f"   Ação: {ACTION}")
        print(f"   Planilha: {SPREADSHEET_ID}")
        return
    
    if ACTION == "daily-metrics":
        daily_metrics()
    elif ACTION == "weekly-leads":
        weekly_leads()
    elif ACTION == "finance-dashboard":
        finance_dashboard()
    elif ACTION == "daily":
        # Relatório genérico
        print(f"\n📊 Gerando relatório diário para '{SHEET_NAME}'...")
        header = get_today_header()
        sheet_append_row(SPREADSHEET_ID, SHEET_NAME, [
            header["data"],
            header["hora"],
            "relatorio",
            "automático",
            datetime.now().isoformat(),
        ])
        print(f"   ✅ Adicionado em {SHEET_NAME}")
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        print("Use 'python composio-google-sheets-reports.py' para ver opções")
        sys.exit(1)
    
    print(f"\n✅ Relatório '{ACTION}' concluído")

if __name__ == "__main__":
    main()
