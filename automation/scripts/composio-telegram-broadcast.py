#!/usr/bin/env python3
"""
composio-telegram-broadcast.py
=================================
Broadcast + Management para Telegram do Zion Tech Group.

 Fluxos:
   - Enviar broadcast para canal/chats
   - Ler mensagens recentes
   - Gerenciar grupos
   - Forward messages entre canais
   - Automatizar resposta a menções

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#telegram"
   export ZION_TELEGRAM_CHANNEL_ID="-100..."  # canal
   export ZION_TELEGRAM_BOT_TOKEN="..."      # bot token

   python composio-telegram-broadcast.py send "Nova atualização" --channel
   python composio-telegram-broadcast.py read --limit 10
   python composio-telegram-broadcast.py forward <msg_id> --to #outro-canal
   python composio-telegram-broadcast.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#telegram")
CHANNEL_ID = os.environ.get("ZION_TELEGRAM_CHANNEL_ID", "")
BOT_TOKEN = os.environ.get("ZION_TELEGRAM_BOT_TOKEN", "")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
MESSAGE = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

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

def send_message(content, chat_id=None):
    """Envia mensagem para canal/grupo especificado."""
    chat = chat_id or CHANNEL_ID
    if not chat:
        print("❌ CHANNEL_ID não configurado")
        print("Exemplo: export ZION_TELEGRAM_CHANNEL_ID='-100...'")
        sys.exit(1)
    
    print(f"   📱 Enviando mensagem para canal {chat}...")
    
    result = tool_execute(
        get_sdk(),
        "TELEGRAM_SEND_MESSAGE",
        arguments={
            "chat_id": chat,
            "text": content,
        },
        user_id="zion-bot",
    )
    
    if result:
        msg_id = result.get("message_id", result.get("id", ""))
        print(f"   ✅ Mensagem enviada: {msg_id}")
        return msg_id
    print(f"   ⚠️  Falha ao enviar")
    return None

def read_messages(limit=10, chat_id=None):
    """Lê mensagens recentes."""
    chat = chat_id or CHANNEL_ID
    print(f"   📖 Lendo últimas {limit} mensagens de {chat}...")
    
    result = tool_execute(
        get_sdk(),
        "TELEGRAM_GET_MESSAGES",
        arguments={
            "chat_id": chat,
            "limit": limit,
        },
        user_id="zion-bot",
    )
    
    if result:
        messages = result.get("messages", [])
        print(f"   ✅ {len(messages)} mensagens lidas")
        for msg in messages[:3]:
            print(f"     [{msg.get('date', '')}] {msg.get('text', '')[:80]}")
        return messages
    return None

def forward_message(msg_id, to_chat_id=None):
    """Forward messages entre canais."""
    to_chat = to_chat_id or CHANNEL_ID
    print(f"   🔄 Forwarding message {msg_id} para {to_chat}...")
    
    result = tool_execute(
        get_sdk(),
        "TELEGRAM_FORWARD_MESSAGE",
        arguments={
            "chat_id": to_chat,
            "message_id": msg_id,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Forwarded")
        return True
    return None

def notify_slack(content):
    """Notifica no Slack."""
    print(f"   📤 Slack...")
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": content},
        user_id="zion-bot",
    )
    if result:
        print(f"   ✅ Slack notificado")
    return result

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Telegram Broadcast — Uso:

  python composio-telegram-broadcast.py send "Mensagem" --channel
      Envia broadcast para canal

  python composio-telegram-broadcast.py read --limit 10
      Lê mensagens recentes

  python composio-telegram-broadcast.py forward <msg_id> --to #canal
      Forward message

  python composio-telegram-broadcast.py --dry-run
      Testa configuração

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_TELEGRAM_CHANNEL_ID='-100...'
  export ZION_TELEGRAM_BOT_TOKEN='...'
  python composio-telegram-broadcast.py send "Release Zion v2.0" --channel
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não executando")
        if ACTION == "send":
            print(f"   Mensagem: {MESSAGE}")
            print(f"   Canal: {CHANNEL_ID}")
        return
    
    if ACTION == "send":
        if not MESSAGE:
            print("❌ Mensagem necessária")
            sys.exit(1)
        send_message(MESSAGE)
        notify_slack(f"*📱 Telegram Broadcast — {datetime.now().strftime('%H:%M')}*\n\n{MESSAGE[:200]}")
    
    elif ACTION == "read":
        limit = 10
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 10
        read_messages(limit)
    
    elif ACTION == "forward":
        msg_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not msg_id:
            print("❌ message_id necessário")
            sys.exit(1)
        forward_message(msg_id)
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
