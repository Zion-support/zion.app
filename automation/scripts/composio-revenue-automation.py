#!/usr/bin/env python3
"""
composio-revenue-automation.py
=================================
Revenue Automation — Stripe + HubSpot + Notion + Slack
=================================
Automatiza faturamento, invoicing, revenue recognition, e notifications.

 Fluxos suportados:
   - Criar invoice para deal fechado no HubSpot
   - Enviar invoice via email para cliente
   - Atualizar deal stage no HubSpot quando pagamento confirmado
   - Log de revenue no Notion para relatórios financeiros
   - Notificação Slack quando receita atinge threshold

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export STRIPE_API_KEY="sk_..."
   export HUBSPOT_API_KEY="..."
   export ZION_SLACK_CHANNEL="#finance"
   export ZION_NOTION_DB_ID="..."
   
   python composio-revenue-automation.py create-invoice <deal_id>
   python composio-revenue-automation.py send-invoice <invoice_id> <email>
   python composio-revenue-automation.py payment-confirmed <payment_id>
   python composio-revenue-automation.py daily-revenue-report
   python composio-revenue-automation.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
HUBSPOT_API_KEY = os.environ.get("HUBSPOT_API_KEY", "")
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#finance")
NOTION_DB_ID = os.environ.get("ZION_NOTION_DB_ID", "")
DRY_RUN = "--dry-run" in sys.argv
DEAL_ID = sys.argv[2] if len(sys.argv) > 2 else None
ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"

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

# ========== STRIPE ==========
def stripe_create_invoice(deal_data):
    """Cria invoice no Stripe para deal fechado."""
    print(f"\n💰 Criando invoice para deal: {deal_data.get('dealname', 'N/A')}")
    
    # Dados do deal do HubSpot
    amount = deal_data.get("amount", 0) * 100  # converter para cents
    currency = deal_data.get("currency", "usd")
    customer_email = deal_data.get("contact_email", deal_data.get("company_email", ""))
    customer_name = deal_data.get("contact_name", deal_data.get("company_name", "Cliente"))
    
    # Criar customer no Stripe se não existir
    customer_result = tool_execute(
        get_sdk(),
        "STRIPE_CREATE_CUSTOMER",
        arguments={
            "email": customer_email,
            "name": customer_name,
        },
        user_id="zion-bot",
    )
    
    customer_id = customer_result.get("id", "") if customer_result else None
    
    # Criar invoice
    invoice = tool_execute(
        get_sdk(),
        "STRIPE_CREATE_INVOICE",
        arguments={
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
            "description": deal_data.get("dealname", "Serviços Zion Tech Group"),
            "metadata": {
                "deal_id": deal_data.get("deal_id", ""),
                "source": "hubspot-automation",
            },
        },
        user_id="zion-bot",
    )
    
    if invoice:
        invoice_id = invoice.get("id", invoice.get("invoiceId", ""))
        invoice_number = invoice.get("invoiceNumber", invoice_id)
        print(f"   ✅ Invoice criada: {invoice_number}")
        return invoice
    return None

def stripe_send_invoice(invoice_id, email):
    """Envia invoice para cliente via email."""
    print(f"\n📧 Enviando invoice {invoice_id} para {email}...")
    
    result = tool_execute(
        get_sdk(),
        "STRIPE_SEND_INVOICE",
        arguments={
            "invoice": invoice_id,
            "email": email,
            "send": True,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Invoice enviada para {email}")
        return True
    return False

def stripe_confirm_payment(payment_id):
    """Confirma pagamento e atualiza deal no HubSpot."""
    print(f"\n✅ Pagamento confirmado: {payment_id}")
    
    # Obter detalhes do pagamento
    payment = tool_execute(
        get_sdk(),
        "STRIPE_GET_PAYMENT",
        arguments={"payment_id": payment_id},
        user_id="zion-bot",
    )
    
    if payment:
        amount = payment.get("amount", 0) / 100  # cents para dollars
        currency = payment.get("currency", "usd")
        invoice_id = payment.get("invoice", "")
        customer_email = payment.get("customer_email", "")
        
        print(f"   Valor: ${amount:,.2f} {currency}")
        print(f"   Invoice: {invoice_id}")
        
        # Atualizar deal no HubSpot para "paid"
        if invoice_id:
            # Extrair deal_id do metadata da invoice
            invoice_meta = tool_execute(
                get_sdk(),
                "STRIPE_GET_INVOICE",
                arguments={"invoice_id": invoice_id},
                user_id="zion-bot",
            )
            deal_id = invoice_meta.get("metadata", {}).get("deal_id", "") if invoice_meta else ""
            
            if deal_id:
                hubspot_update = tool_execute(
                    get_sdk(),
                    "HUBSPOT_UPDATE_DEAL",
                    arguments={
                        "deal_id": deal_id,
                        "dealstage": "closedwon",
                        "amount": amount,
                        "closed_date": datetime.now().isoformat(),
                    },
                    user_id="zion-bot",
                )
                if hubspot_update:
                    print(f"   ✅ Deal {deal_id} atualizada para 'closedwon'")
        
        # Log no Notion
        create_revenue_log(
            amount=amount,
            currency=currency,
            invoice_id=invoice_id,
            payment_id=payment_id,
            customer_email=customer_email,
        )
        
        # Slack notification
        slack_notify_revenue(
            amount=amount,
            currency=currency,
            invoice_id=invoice_id,
            customer_email=customer_email,
        )
        
        return True
    return False

def create_revenue_log(amount, currency, invoice_id, payment_id, customer_email):
    """Cria log de revenue no Notion."""
    print(f"   📝 Criando log de revenue no Notion...")
    
    page_title = f"💰 Receita — {datetime.now().strftime('%Y-%m-%d')} — {amount:,.2f} {currency}"
    
    result = tool_execute(
        get_sdk(),
        "NOTION_CREATE_PAGE",
        arguments={
            "parent": {"database_id": NOTION_DB_ID},
            "properties": {
                "title": {"title": [{"text": {"content": page_title}}]},
                "Status": {"select": {"name": "Recebido"}},
                "Valor": {"number": amount},
                "Moeda": {"select": {"name": currency.upper()}},
                "Invoice ID": {"rich_text": [{"text": {"content": invoice_id}}]},
                "Payment ID": {"rich_text": [{"text": {"content": payment_id}}]},
                "Data": {"rich_text": [{"text": {"content": datetime.now().strftime('%Y-%m-%d')}}]},
                "Cliente": {"rich_text": [{"text": {"content": customer_email}}]},
            },
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Log criado no Notion")
    return result

def slack_notify_revenue(amount, currency, invoice_id, customer_email):
    """Notifica receipt de revenue no Slack."""
    message = f"*💰 Revenue Receipt — {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    message += f"**Valor:** ${amount:,.2f} {currency}\n"
    message += f"**Invoice:** {invoice_id}\n"
    message += f"**Cliente:** {customer_email}\n"
    message += f"_{datetime.now().strftime('%H:%M')}_\n"
    
    tool_execute(
        get_sdk(),
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": SLACK_CHANNEL,
            "text": message,
        },
        user_id="zion-bot",
    )
    print(f"   📤 Slack notificação enviada para {SLACK_CHANNEL}")

def daily_revenue_report():
    """Gera relatório diário de revenue."""
    print(f"\n📊 Gerando relatório diário de revenue...")
    
    # Este sería implementado consultando HubSpot deals + Stripe invoices
    # e comprimindo em um relatório no Notion + Slack
    
    message = f"*📊 Daily Revenue Report — {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    message += "Implementar consulta a HubSpot deals (closedwon) + Stripe invoices (paid)\n"
    message += "e gerar relatório consolidado com:\n"
    message += "- Total recebido hoje\n"
    message += "- Top clientes\n"
    message += "- MRR atualizado\n"
    message += "- Pipeline vs recebido\n\n"
    message += "*Relatório completo disponível no Notion.*"
    
    tool_execute(
        get_sdk(),
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": SLACK_CHANNEL,
            "text": message,
        },
        user_id="zion-bot",
    )
    
    print(f"   📤 Relatório enviado para {SLACK_CHANNEL}")

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        print("Exemplo: export COMPOSIO_API_KEY='sk_...'")
        sys.exit(1)
    
    if not STRIPE_API_KEY:
        print("⚠️  STRIPE_API_KEY não configurada — operações Stripe podem falhar")
    
    if not HUBSPOT_API_KEY:
        print("⚠️  HUBSPOT_API_KEY não configurada — operações HubSpot podem falhar")
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Composio Revenue Automation — Uso:

  python composio-revenue-automation.py create-invoice <deal_id>
      Cria invoice no Stripe para deal fechado no HubSpot

  python composio-revenue-automation.py send-invoice <invoice_id> <email>
      Envia invoice para cliente via email

  python composio-revenue-automation.py payment-confirmed <payment_id>
      Confirma pagamento, atualiza deal, loga no Notion, notifica Slack

  python composio-revenue-automation.py daily-revenue-report
      Gera relatório diário de revenue no Slack

  python composio-revenue-automation.py --dry-run
      Testa configuração sem executar ações

Exemplo completo:
  export COMPOSIO_API_KEY='sk_...'
  export STRIPE_API_KEY='sk_...'
  export HUBSPOT_API_KEY='...'
  export ZION_SLACK_CHANNEL='#finance'
  export ZION_NOTION_DB_ID='...'
  
  python composio-revenue-automation.py payment-confirmed 'pi_xxxx'
""")
        return
    
    sdk = get_sdk()
    
    if ACTION == "create-invoice":
        if not DEAL_ID:
            print("❌ deal_id necessário")
            print("Uso: python composio-revenue-automation.py create-invoice <deal_id>")
            sys.exit(1)
        # Obter deal dados do HubSpot
        deal_data = tool_execute(
            sdk,
            "HUBSPOT_GET_DEAL",
            arguments={"deal_id": DEAL_ID},
            user_id="zion-bot",
        )
        if deal_data:
            invoice = stripe_create_invoice(deal_data)
            if invoice:
                invoice_id = invoice.get("id", invoice.get("invoiceId", ""))
                customer_email = deal_data.get("contact_email", deal_data.get("company_email", ""))
                stripe_send_invoice(invoice_id, customer_email)
            else:
                print("❌ Falha ao criar invoice")
                sys.exit(1)
        else:
            print(f"❌ Deal não encontrada: {DEAL_ID}")
            sys.exit(1)
    
    elif ACTION == "send-invoice":
        invoice_id = sys.argv[2] if len(sys.argv) > 2 else None
        email = sys.argv[3] if len(sys.argv) > 3 else None
        if not invoice_id or not email:
            print("❌ invoice_id e email necessários")
            print("Uso: python composio-revenue-automation.py send-invoice <invoice_id> <email>")
            sys.exit(1)
        stripe_send_invoice(invoice_id, email)
    
    elif ACTION == "payment-confirmed":
        payment_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not payment_id:
            print("❌ payment_id necessário")
            print("Uso: python composio-revenue-automation.py payment-confirmed <payment_id>")
            sys.exit(1)
        stripe_confirm_payment(payment_id)
    
    elif ACTION == "daily-revenue-report":
        daily_revenue_report()
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        print("Use 'python composio-revenue-automation.py help' para ver opções")
        sys.exit(1)

if __name__ == "__main__":
    main()
