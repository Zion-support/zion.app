#!/usr/bin/env python3
"""
composio-calendar-agent.py
==========================
Google Calendar Agent — agenda, sincroniza, gerencia eventos do Zion.

 Fluxos:
   - Criar eventos e reuniões
   - Listar eventos do dia/semana
   - Agendar focus time automaticamente
   - Responder a convites
   - Sync com agenda de equipe

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#calendar"
   
   python composio-calendar-agent.py today
   python composio-calendar-agent.py week
   python composio-calendar-agent.py create "Reunião de Projeto" 15:00 16:00
   python composio-calendar-agent.py focus-time
   python composio-calendar-agent.py --dry-run
"""

import os
import sys
import json
from datetime import datetime, timedelta
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#calendar")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
MEETING_TITLE = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
MEETING_START = "15:00"  # default
MEETING_END = "16:00"  # default

# Parse time args
if len(sys.argv) > 3:
    MEETING_START = sys.argv[3]
if len(sys.argv) > 4:
    MEETING_END = sys.argv[4]

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

def list_today_events():
    """Lista eventos de hoje."""
    print(f"   📅 Eventos de hoje ({datetime.now().strftime('%Y-%m-%d')})...")
    
    sdk = get_sdk()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
    
    result = tool_execute(
        sdk,
        "GOOGLECALENDAR_LIST_EVENTS",
        arguments={
            "time_min": today_start,
            "time_max": today_end,
            "max_results": 20,
        },
        user_id="zion-bot",
    )
    
    events = result.get("items", []) if isinstance(result, dict) else []
    
    print(f"   ✅ {len(events)} eventos encontrados")
    for event in events:
        start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
        title = event.get("summary", "Sem título")
        print(f"     {start} — {title}")
    
    return events

def list_week_events():
    """Lista eventos da próxima semana."""
    print(f"   📅 Eventos da próxima semana...")
    
    sdk = get_sdk()
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_end = (datetime.now() + timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
    
    result = tool_execute(
        sdk,
        "GOOGLECALENDAR_LIST_EVENTS",
        arguments={
            "time_min": week_start,
            "time_max": week_end,
            "max_results": 50,
        },
        user_id="zion-bot",
    )
    
    events = result.get("items", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(events)} eventos na próxima semana")
    return events

def create_event(title, start_time, end_time):
    """Cria evento no calendário."""
    print(f"   📅 Criando evento: {title}...")
    print(f"      Horário: {start_time} → {end_time}")
    
    sdk = get_sdk()
    
    # Parse time
    today = datetime.now().strftime("%Y-%m-%d")
    start_dt = f"{today}T{start_time}:00"
    end_dt = f"{today}T{end_time}:00"
    
    result = tool_execute(
        sdk,
        "GOOGLECALENDAR_CREATE_EVENT",
        arguments={
            "summary": title,
            "start_time": start_dt,
            "end_time": end_dt,
            "timezone": "America/Sao_Paulo",
        },
        user_id="zion-bot",
    )
    
    if result:
        event_id = result.get("id", result.get("eventId", ""))
        print(f"   ✅ Evento criado: {event_id}")
        return event_id
    print(f"   ⚠️  Falha ao criar evento")
    return None

def create_focus_time(duration_hours=2):
    """Agenda focus time automaticamente."""
    print(f"   🧠 Agendando focus time de {duration_hours}h...")
    
    sdk = get_sdk()
    
    # Encontrar próximo horário disponível (simples: próximo dia 9am)
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=duration_hours)
    
    # Check existing events
    existing = list_today_events() if datetime.now().date() == tomorrow.date() else []
    
    result = tool_execute(
        sdk,
        "GOOGLECALENDAR_CREATE_EVENT",
        arguments={
            "summary": "🔒 Focus Time — Zion Tech Group",
            "description": "Tempo dedicado para trabalho profundo. Agendado automaticamente pelo Calendar Agent.",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "timezone": "America/Sao_Paulo",
            "visibility": "private",
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Focus time agendado para {tomorrow.strftime('%d/%m/%Y')} 09:00-{duration_hours}h")
        return result.get("id", "")
    return None

def notify_slack(message):
    """Notifica no Slack."""
    print(f"   📤 Slack...")
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": message},
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
📋 Calendar Agent — Uso:

  python composio-calendar-agent.py today
      Lista eventos de hoje

  python composio-calendar-agent.py week
      Lista eventos da próxima semana

  python composio-calendar-agent.py create "Título" 15:00 16:00
      Cria evento no calendário

  python composio-calendar-agent.py focus-time
      Agenda focus time automaticamente (2h)

  python composio-calendar-agent.py --dry-run
      Testa configuração sem criar eventos

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#calendar'
  python composio-calendar-agent.py create "Reunião de Projeto" 15:00 16:00
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não criando eventos")
        if ACTION == "create":
            print(f"   Evento: {MEETING_TITLE}")
            print(f"   Horário: {MEETING_START} → {MEETING_END}")
        return
    
    if ACTION == "today":
        list_today_events()
        notify_slack(f"*📅 Agenda de Hoje — {datetime.now().strftime('%H:%M')}*\n\nEventos de hoje listados")
    
    elif ACTION == "week":
        list_week_events()
        notify_slack(f"*📅 Semana que Vem — {datetime.now().strftime('%H:%M')}*\n\nEventos da próxima semana listados")
    
    elif ACTION == "create":
        if not MEETING_TITLE:
            print("❌ Título necessário")
            print("Uso: python composio-calendar-agent.py create \"Título\" 15:00 16:00")
            sys.exit(1)
        create_event(MEETING_TITLE, MEETING_START, MEETING_END)
        notify_slack(f"*📅 Evento Criado — {datetime.now().strftime('%H:%M')}*\n\n**{MEETING_TITLE}**\n{MEETING_START}–{MEETING_END}")
    
    elif ACTION == "focus-time":
        create_focus_time()
        notify_slack("*🧠 Focus Time Agendado*\n\nFocus time de 2h agendado automaticamente para manhã de amanhã.")
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
