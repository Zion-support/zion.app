#!/usr/bin/env python3
"""
composio-whatsapp-agent.py
===========================
WhatsApp Business Agent — atendimento, auto-respostas, e notificações do Zion.

 Fluxos:
   - Enviar mensagens para clientes (responder leads, notificar pedidos)
   - Ler mensagens recebidas
   - Auto-resposta para mensagens com keywords
   - Broadcast para lista de contatos
   - Sync com HubSpot (log de conversas)
   - Notificar Slack para mensagens importantes

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#whatsapp"
   
   python composio-whatsapp-agent.py send "5511999999999" "Olá! Como posso ajudar?"
   python composio-whatsapp-agent.py read --limit 10
   python composio-whatsapp-agent.py auto-reply --keyword "orcamento"
   python composio-whatsapp-agent.py broadcast "Nova oferta Zion!" --contacts "5511...,5521..."
   python composio-whatsapp-agent.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
ZION_SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#whatsapp")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
PHONE = sys.argv[2] if len(sys.argv) > 2 else None
MESSAGE = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None
KEYWORD = sys.argv[2] if len(sys.argv) > 2 and "--keyword" in sys.argv else None

# Parse args
if "--keyword" in sys.argv:
    kw_idx = sys.argv.index("--keyword")
    KEYWORD = sys.argv[kw_idx + 1] if kw_idx + 1 < len(sys.argv) else None
if "--limit" in sys.argv:
    limit_idx = sys.argv.index("--limit")
    READ_LIMIT = int(sys.argv[limit_idx + 1]) if limit_idx + 1 < len(sys.argv) else 10
else:
    READ_LIMIT = 10
if "--contacts" in sys.argv:
    contacts_idx = sys.argv.index("--contacts")
    CONTACTS = sys.argv[contacts_idx + 1] if contacts_idx + 1 < len(sys.argv) else ""
    CONTACTS = [c.strip() for c in CONTACTS.split(",") if c.strip()]
else:
    CONTACTS = []

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
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": ZION_SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )
    if result:
        print(f"   ✅ Slack notificado")
    return result

# ========== WHATSAPP FUNCTIONS ==========

def send_message(phone_number, message):
    """Envia mensagem por WhatsApp."""
    print(f"   📱 Enviando mensagem para {phone_number}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "WHATSAPP_SEND_MESSAGE",
        arguments={
            "phone_number": phone_number,
            "message": message,
        },
        user_id="zion-bot",
    )
    
    if result:
        msg_id = result.get("id", result.get("messageId", ""))
        print(f"   ✅ Mensagem enviada: {msg_id}")
        slack_notify(f"*📱 WhatsApp Enviado — {datetime.now().strftime('%H:%M')}*\n\n**Para:** {phone_number}\n**Mensagem:** {message[:200]}")
        return msg_id
    print(f"   ⚠️  Falha ao enviar mensagem")
    return None

def read_messages(limit=10):
    """Lê mensagens recebidas."""
    print(f"   📖 Lendo últimas {limit} mensagens...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "WHATSAPP_GET_MESSAGES",
        arguments={
            "limit": limit,
        },
        user_id="zion-bot",
    )
    
    messages = result.get("messages", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(messages)} mensagens lidas")
    
    for msg in messages[:5]:
        sender = msg.get("from", msg.get("sender", "N/A"))
        text = msg.get("text", msg.get("body", ""))
        timestamp = msg.get("timestamp", "")
        print(f"     [{timestamp}] {sender}: {text[:80]}")
    
    # Alertar no Slack se mensagens importantes
    important_keywords = ["orcamento", "preço", "serviço", "emergência", "urgente"]
    for msg in messages:
        text = msg.get("text", msg.get("body", "")).lower()
        if any(kw in text for kw in important_keywords):
            sender = msg.get("from", msg.get("sender", "N/A"))
            slack_notify(f"*🚨 WhatsApp Importante — {datetime.now().strftime('%H:%M')}*\n\n**De:** {sender}\n**Mensagem:** {msg.get('text', '')[:200]}")
    
    return messages

def auto_reply(keyword, response=None):
    """Auto-resposta para mensagens com keyword específica."""
    if not KEYWORD:
        print("❌ Keyword necessária")
        print("Uso: python composio-whatsapp-agent.py auto-reply --keyword 'orcamento'")
        sys.exit(1)
    
    if not response:
        response = f"""Olá! Obrigado pelo seu interesse em {KEYWORD}.
        
        Em breve um de nossos especialistas entrará em contato.
        Para atendimento imediato, acesse ziontechgroup.com ou ligue para (11) 99999-9999.
        
        Atenciosamente,
        Zion Tech Group"""
    
    print(f"   🤖 Configurando auto-resposta para keyword: {KEYWORD}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "WHATSAPP_SET_AUTO_REPLY",
        arguments={
            "keyword": KEYWORD,
            "response": response,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Auto-resposta configurada para '{KEYWORD}'")
        slack_notify(f"*🤖 Auto-Reply WhatsApp — {datetime.now().strftime('%H:%M')}*\n\nKeyword: {KEYWORD}\nResposta configurada")
        return True
    return None

def broadcast(message, contacts=None):
    """Broadcast para múltiplos contatos."""
    if not message:
        print("❌ Mensagem necessária")
        print("Uso: python composio-whatsapp-agent.py broadcast \"Mensagem\" --contacts \"5511...,5521...\"")
        sys.exit(1)
    
    if not contacts:
        print("❌ Contatos necessários")
        print("Use --contacts '5511999999999,5521888888888'")
        sys.exit(1)
    
    print(f"   📢 Broadcast para {len(contacts)} contatos...")
    
    sdk = get_sdk()
    sent = 0
    errors = 0
    
    for phone in contacts:
        result = tool_execute(
            sdk,
            "WHATSAPP_SEND_MESSAGE",
            arguments={
                "phone_number": phone,
                "message": message,
            },
            user_id="zion-bot",
        )
        
        if result:
            sent += 1
        else:
            errors += 1
    
    print(f"   ✅ {sent} mensagens enviadas, {errors} falhas")
    slack_notify(f"*📢 WhatsApp Broadcast — {datetime.now().strftime('%H:%M')}*\n\n**Enviado para:** {len(contacts)} contatos\n**Sucesso:** {sent}\n**Falhas:** {errors}")
    return sent

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 WhatsApp Agent — Uso:

  python composio-whatsapp-agent.py send "5511999999999" "Mensagem"
      Envia mensagem para número específico

  python composio-whatsapp-agent.py read --limit 10
      Lê mensagens recebidas

  python composio-whatsapp-agent.py auto-reply --keyword "orcamento"
      Configura auto-resposta para keyword

  python composio-whatsapp-agent.py broadcast "Mensagem" --contacts "5511...,5521..."
      Broadcast para múltiplos contatos

  python composio-whatsapp-agent.py --dry-run
      Testa configuração sem enviar mensagens

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#whatsapp'
  python composio-whatsapp-agent.py send "5511999999999" "Olá! Como posso ajudar?"
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não enviando mensagens")
        if ACTION == "send":
            print(f"   Para: {PHONE}")
            print(f"   Mensagem: {MESSAGE}")
        elif ACTION == "broadcast":
            print(f"   Para {len(CONTACTS)} contatos")
            print(f"   Mensagem: {MESSAGE}")
        return
    
    if ACTION == "send":
        if not PHONE or not MESSAGE:
            print("❌ Número e mensagem necessários")
            print("Uso: python composio-whatsapp-agent.py send <telefone> <mensagem>")
            sys.exit(1)
        send_message(PHONE, MESSAGE)
    
    elif ACTION == "read":
        read_messages(READ_LIMIT)
    
    elif ACTION == "auto-reply":
        auto_reply(KEYWORD)
    
    elif ACTION == "broadcast":
        broadcast(MESSAGE, CONTACTS)
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
