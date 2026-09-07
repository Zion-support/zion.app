#!/usr/bin/env python3
"""
composio-social-broadcast.py
=============================
Broadcast multi-canal para Zion Tech Group:
LinkedIn + Twitter + Telegram + Discord + Google Calendar

 Fluxos:
   - Criar e publicar post de conteúdo (LinkedIn + Twitter)
   - Broadcast no Telegram para canal do Zion
   - Mensagem no Discord para comunidade
   - Agendar evento no Google Calendar
   - Notificar Slack quando publicado

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#social"
   export ZION_TELEGRAM_BOT_TOKEN="..."  # se usar Telegram Bot
   export ZION_TELEGRAM_CHANNEL_ID="..."  # canal/chat ID
   
   python composio-social-broadcast.py post "Novo post sobre IA" --linkedin --twitter --telegram
   python composio-social-broadcast.py schedule "Reunião Semanal" --calendar
   python composio-social-broadcast.py --dry-run
"""

import os
import sys
import json
from datetime import datetime, timedelta
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#social")
TELEGRAM_BOT_TOKEN = os.environ.get("ZION_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("ZION_TELEGRAM_CHANNEL_ID", "")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
MESSAGE = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

# Platform flags
POST_TO_LINKEDIN = "--linkedin" in sys.argv
POST_TO_TWITTER = "--twitter" in sys.argv
POST_TO_TELEGRAM = "--telegram" in sys.argv
POST_TO_DISCORD = "--discord" in sys.argv
POST_TO_CALENDAR = "--calendar" in sys.argv

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

def publish_linkedin(content, title=None):
    """Publica conteúdo no LinkedIn."""
    print(f"   🔗 Publicando no LinkedIn...")
    
    result = tool_execute(
        get_sdk(),
        "LINKEDIN_CREATE_POST",
        arguments={
            "content": content,
            "title": title or f"Zion Tech Group — {datetime.now().strftime('%Y-%m-%d')}",
            "visibility": "public",
        },
        user_id="zion-bot",
    )
    
    if result:
        post_id = result.get("id", result.get("postId", ""))
        print(f"   ✅ Postado no LinkedIn: {post_id}")
        return post_id
    print(f"   ⚠️  Falha ao publicar no LinkedIn")
    return None

def publish_twitter(content):
    """Publica conteúdo no Twitter/X."""
    print(f"   🐦 Publicando no Twitter...")
    
    result = tool_execute(
        get_sdk(),
        "TWITTER_CREATE_TWEET",
        arguments={
            "text": content[:280],  # limite do Twitter
        },
        user_id="zion-bot",
    )
    
    if result:
        tweet_id = result.get("id", result.get("tweetId", ""))
        print(f"   ✅ Tweetado: {tweet_id}")
        return tweet_id
    print(f"   ⚠️  Falha ao tweetar")
    return None

def send_telegram(content):
    """Envia mensagem no Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"   ⚠️  Telegram bot token não configurado")
        return None
    
    print(f"   📱 Enviando no Telegram...")
    
    result = tool_execute(
        get_sdk(),
        "TELEGRAM_SEND_MESSAGE",
        arguments={
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": content,
        },
        user_id="zion-bot",
    )
    
    if result:
        message_id = result.get("message_id", "")
        print(f"   ✅ Enviado no Telegram: {message_id}")
        return message_id
    print(f"   ⚠️  Falha ao enviar no Telegram")
    return None

def send_discord(content):
    """Envia mensagem no Discord."""
    print(f"   💬 Enviando no Discord...")
    
    result = tool_execute(
        get_sdk(),
        "DISCORD_SEND_MESSAGE",
        arguments={
            "channel_id": os.environ.get("ZION_DISCORD_CHANNEL_ID", ""),
            "content": content,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Enviado no Discord")
        return True
    print(f"   ⚠️  Falha ao enviar no Discord")
    return None

def schedule_calendar_event(title, description=None, start_time=None):
    """Agenda evento no Google Calendar."""
    print(f"   📅 Agendando no Google Calendar...")
    
    start = start_time or datetime.now() + timedelta(days=1, hours=9)
    end = start + timedelta(hours=1)
    
    result = tool_execute(
        get_sdk(),
        "GOOGLECALENDAR_CREATE_EVENT",
        arguments={
            "summary": title,
            "description": description or f"Evento automático — {datetime.now().strftime('%Y-%m-%d')}",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "timezone": "America/Sao_Paulo",
        },
        user_id="zion-bot",
    )
    
    if result:
        event_id = result.get("id", result.get("eventId", ""))
        print(f"   ✅ Evento agendado: {event_id}")
        return event_id
    print(f"   ⚠️  Falha ao agendar")
    return None

def notify_slack(message):
    """Notifica no Slack."""
    print(f"   📤 Notificando Slack...")
    
    result = tool_execute(
        get_sdk(),
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": SLACK_CHANNEL,
            "text": message,
        },
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
    
    if not ACTION:
        print("""
📋 Social Broadcast — Uso:

  python composio-social-broadcast.py "Conteúdo do post" --linkedin --twitter --telegram
      Publica conteúdo em múltiplas plataformas

  python composio-social-broadcast.py "Conteúdo" --discord
      Envia mensagem no Discord

  python composio-social-broadcast.py "Nome do evento" --calendar
      Agenda evento no Google Calendar

  python composio-social-broadcast.py --dry-run
      Testa configuração sem publicar

Flags:
  --linkedin     Publicar no LinkedIn
  --twitter      Tweetar no X/Twitter
  --telegram     Enviar no Telegram
  --discord      Enviar no Discord
  --calendar     Agendar no Google Calendar

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#social'
  export ZION_TELEGRAM_BOT_TOKEN='...'
  export ZION_TELEGRAM_CHANNEL_ID='...'
  
  python composio-social-broadcast.py "Novo artigo: AI Automation para Enterprise" --linkedin --twitter --telegram
""")
        return
    
    if DRY_RUN:
        print("🔍 Modo dry-run — não publicando")
        print(f"   Mensagem: {MESSAGE}")
        platforms = []
        if POST_TO_LINKEDIN: platforms.append("LinkedIn")
        if POST_TO_TWITTER: platforms.append("Twitter")
        if POST_TO_TELEGRAM: platforms.append("Telegram")
        if POST_TO_DISCORD: platforms.append("Discord")
        if POST_TO_CALENDAR: platforms.append("Google Calendar")
        print(f"   Plataformas: {', '.join(platforms) or 'Nenhuma selecionada'}")
        return
    
    if not MESSAGE:
        print("❌ Mensagem necessária")
        print("Uso: python composio-social-broadcast.py <mensagem> [flags]")
        sys.exit(1)
    
    sdk = get_sdk()
    
    # Publicar nas plataformas selecionadas
    if POST_TO_LINKEDIN or not any([POST_TO_LINKEDIN, POST_TO_TWITTER, POST_TO_TELEGRAM, POST_TO_DISCORD]):
        # Se nenhuma flag específica, publicar em todas
        POST_TO_LINKEDIN = True
        POST_TO_TWITTER = True
        POST_TO_TELEGRAM = True
        POST_TO_DISCORD = True
    
    results = {}
    
    if POST_TO_LINKEDIN:
        results["linkedin"] = publish_linkedin(MESSAGE)
    
    if POST_TO_TWITTER:
        results["twitter"] = publish_twitter(MESSAGE)
    
    if POST_TO_TELEGRAM:
        results["telegram"] = send_telegram(MESSAGE)
    
    if POST_TO_DISCORD:
        results["discord"] = send_discord(MESSAGE)
    
    if POST_TO_CALENDAR:
        results["calendar"] = schedule_calendar_event(MESSAGE)
    
    # Slack notification
    published = [k for k, v in results.items() if v]
    if published:
        slack_msg = f"*✍️ Publicado — {datetime.now().strftime('%H:%M')}*\n\n"
        slack_msg += f"Múltiplas plataformas:\n"
        for platform in published:
            slack_msg += f"  ✅ {platform.capitalize()}\n"
        slack_msg += f"\n _{datetime.now().strftime('%Y-%m-%d')}_"
        notify_slack(slack_msg)
    
    print(f"\n✅ Broadcast concluído")
    print(f"   Publicado em: {', '.join(published) if published else 'Nenhuma plataforma'}")

if __name__ == "__main__":
    main()
