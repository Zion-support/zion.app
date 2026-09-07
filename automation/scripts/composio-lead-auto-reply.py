#!/usr/bin/env python3
"""
composio-lead-auto-reply.py
=====================================================
Auto-Triage + Auto-Reply para leads de email.
Classifica emails entrants, cria deals no HubSpot, issues no Linear,
documenta no Notion, envia auto-reply personalizado, e notifica no Slack.

 Uso: python composio-lead-auto-reply.py [--dry-run]
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
GMAIL_LABEL_PROCESSING = os.environ.get("ZION_GMAIL_LABEL_PROCESSING", "lead-processing")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#leads")
STATE_FILE = "/tmp/composio-lead-auto-reply-state.json"
DRY_RUN = "--dry-run" in sys.argv

# Keywords que indicam lead quente
HOT_KEYWORDS = ["orcamento", "preco", "cotacao", "pagar", "contratar", "demo", "reuniao", 
                 "agendar", "preciso", "urgente", "projeto", "implementar", "solucao",
                 "ia", "automacao", "transformacao", "digital"]

# ========== STATE ==========
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"processed_emails": [], "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ========== SDK ==========
def get_sdk():
    api_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not api_key:
        print("ERRO: COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    return Composio(api_key=api_key)

def tool_execute(sdk, tool_name, args, user_id="zion-bot"):
    try:
        return sdk.tools.execute(tool_name, arguments=args, user_id=user_id)
    except Exception as e:
        print(f"  ⚠ Erro em {tool_name}: {e}")
        return None

# ========== FUNCÕES ==========
def fetch_unread_emails(sdk):
    """Busca emails não lidos com label de processamento."""
    result = tool_execute(
        sdk,
        "GMAIL_LIST_MESSAGES",
        {
            "labels": [GMAIL_LABEL_PROCESSING],
            "pageSize": 20,
            "q": "is:unread",
        },
    )
    if not result:
        return []
    messages = result.get("messages", result.get("items", []))
    return messages[:20]

def classify_email(sdk, subject, snippet, from_address):
    """Classifica se é lead, suporte, ou outro."""
    prompt = f"""
Você é um assistant de intelligence de leads. Classifique este email:

Assunto: {subject}
De: {from_address}
Conteúdo (snippet): {snippet[:500]}

Responda APENAS com um JSON: {{"category": "lead"|"support"|"other", "score": 0-10, "reason": "breve explicação"}}
"""
    result = tool_execute(
        sdk,
        "COMPOSIO-GPT_COMPLETIONS",
        {"prompt": prompt, "max_tokens": 200},
    )
    
    if result:
        text = result.get("content", result.get("text", ""))
        try:
            # Tenta extrair JSON da resposta
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
        except:
            pass
    return {"category": "other", "score": 0, "reason": "não classificado"}

def generate_auto_reply(sdk, sender_name, category, subject, snippet):
    """Gera auto-reply personalizado baseado na classificação."""
    if category == "lead":
        tone = "entusiásta e profissional"
        cta = "agendar uma breve conversa de descoberta"
    elif category == "support":
        tone = "útil e direto"
        cta = "descrever o problema em mais detalhes"
    else:
        tone = "cortês"
        cta = "responder no assunto apropriado"
    
    prompt = f"""
Gere uma resposta de email automatizada, em PORTUGUÊS, para:

Remetente: {sender_name}
Categoria: {category}
Assunto: {subject}
Snippet: {snippet[:300]}

A resposta deve:
- Ter tom {tone}
- Ser concisa (3-4 frases)
- Incluir chamada para ação: {cta}
- Ser genérica o suficiente para ser automatizada, mas personalizada o suficiente para não parecer robô
- NÃO incluir informações sensíveis ou promessas específicas
"""
    result = tool_execute(
        sdk,
        "COMPOSIO-GPT_COMPLETIONS",
        {"prompt": prompt, "max_tokens": 500},
    )
    
    if result:
        return result.get("content", result.get("text", "")) or ""
    return ""

def create_hubspot_deal(sdk, sender, subject, snippet, category, score):
    """Cria deal no HubSpot para leads."""
    if category != "lead":
        return None
    
    deal_name = f"Lead: {sender[:40]} — {subject[:40]}"
    
    result = tool_execute(
        sdk,
        "HUBSPOT_CREATE_DEAL",
        {
            "dealname": deal_name,
            "dealstage": "appointmentscheduled",
            "description": f"Assunto: {subject}\n\nSnippet: {snippet[:500]}",
            "amount": max(500, score * 100),  # estimativa baseada no score
            "pipeline": "default",
        },
    )
    
    if result:
        deal_id = result.get("id", result.get("dealId", ""))
        print(f"  → Deal HubSpot criado: {deal_id}")
        return deal_id
    return None

def create_notion_log(sdk, sender, subject, category, score, reply_text):
    """Cria log no Notion para auditoria."""
    page_title = f"📧 Auto-Triage: {subject[:50]}"
    
    result = tool_execute(
        sdk,
        "NOTION_CREATE_PAGE",
        {
            "parent": {"database_id": os.environ.get("ZION_NOTION_DB_ID", "")},
            "properties": {
                "title": {"title": [{"text": {"content": page_title}}]},
                "Status": {"select": {"name": "Processado"}},
                "Categoria": {"select": {"name": category}},
                "Score": {"number": score},
                "Remetente": {"rich_text": [{"text": {"content": sender}}]},
                "Data": {"rich_text": [{"text": {"content": datetime.now().strftime('%Y-%m-%d')}}]},
            },
            "children": [
                {"object": "block", "type": "paragraph", "paragraph": {"text": {"content": f"Auto-reply enviada:\n\n{reply_text}"}}}
            ],
        },
    )
    
    if result:
        print(f"  → Notion log criado")
    return result

def create_linear_issue(sdk, sender, subject, category):
    """Cria issue no Linear para suporte ou leads que precisam de follow-up humano."""
    if category == "support":
        title = f"🚨 Suporte: {subject[:60]}"
        priority = 1  # alta
    elif category == "lead":
        title = f"📞 Lead: {subject[:60]} — follow-up humano"
        priority = 2
    else:
        return None
    
    result = tool_execute(
        sdk,
        "LINEAR_CREATE_ISSUE",
        {
            "teamId": os.environ.get("ZION_LINEAR_TEAM_ID", ""),
            "title": title,
            "description": f"**Remetente:** {sender}\n**Assunto:** {subject}\n**Categoria:** {category}",
            "priority": priority,
        },
    )
    
    if result:
        print(f"  → Linear issue criado para {category}")
    return result

def send_auto_reply(sdk, message_id, reply_text, from_address):
    """Envia auto-reply para o remetente."""
    result = tool_execute(
        sdk,
        "GMAIL_SEND_MESSAGE",
        {
            "to": from_address,
            "subject": f"Re: {reply_text[:50]}",
            "body": reply_text,
        },
    )
    
    if result:
        print(f"  → Auto-reply enviada para {from_address}")
    return result

def notify_slack(sdk, sender, subject, category, score, slack_channel):
    """Notifica no Slack."""
    emoji = "🔥" if category == "lead" and score >= 7 else "📧" if category == "lead" else "🛟" if category == "support" else "📌"
    
    message = f"""{emoji} *Auto-Triage: {category.upper()}* (score: {score}/10)

**De:** {sender}
**Assunto:** {subject}

Auto-reply {'enviada' if category in ['lead', 'support'] else 'gerada'} pelo sistema.
"""
    
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": slack_channel, "text": message},
    )
    
    if result:
        print(f"  → Notificação Slack enviada")

# ========== MAIN ==========
def main():
    sdk = get_sdk()
    state = load_state()
    dry_run = DRY_RUN
    
    print(f"\n{'='*60}")
    print(f"  Lead Auto-Triage + Auto-Reply — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    if dry_run:
        print("  ⚠️ MODO DRY RUN")
    print()
    
    # 1. Buscar emails não lidos
    print("📡 Passo 1: Buscando emails não lidos...")
    messages = fetch_unread_emails(sdk)
    print(f"  → {len(messages)} emails encontrados\n")
    
    if not messages:
        print("✅ Nenhum email para processar.")
        save_state(state)
        return
    
    # 2. Processar cada email
    for msg in messages:
        msg_id = msg.get("id", "")
        
        # Evitar duplicatas
        if msg_id in state.get("processed_emails", []):
            continue
        
        subject = msg.get("subject", "(sem assunto)")
        snippet = msg.get("snippet", "")
        from_addr = msg.get("from", "")
        sender_name = from_addr.split("<")[0].strip() if "<" in from_addr else from_addr
        
        print(f"{'─'*50}")
        print(f"  Processando: {subject[:60]}")
        print(f"  De: {sender_name}")
        print(f"{'─'*50}")
        
        # 2a. Classificar
        print("  🧠 Classificando...")
        classification = classify_email(sdk, subject, snippet, from_addr)
        print(f"  → {classification['category']} (score: {classification['score']}): {classification['reason']}")
        
        # 2b. Gerar auto-reply
        print("  ✍️ Gerando auto-reply...")
        reply_text = generate_auto_reply(sdk, sender_name, classification['category'], subject, snippet)
        
        # 2c. Ações por categoria
        if classification['category'] == "lead":
            print("  💼 Criando deal no HubSpot...")
            create_hubspot_deal(sdk, sender_name, subject, snippet, 
                              classification['category'], classification['score'])
            
            print("  📝 Criando log no Notion...")
            create_notion_log(sdk, sender_name, subject, classification['category'],
                            classification['score'], reply_text)
            
            print("  📤 Enviando auto-reply...")
            if not dry_run:
                send_auto_reply(sdk, msg_id, reply_text, from_addr)
        
        elif classification['category'] == "support":
            print("  📋 Criando issue no Linear...")
            create_linear_issue(sdk, sender_name, subject, classification['category'])
            
            print("  📝 Criando log no Notion...")
            create_notion_log(sdk, sender_name, subject, classification['category'],
                            classification['score'], reply_text)
        
        else:
            print("  ℹ️ Email classificado como 'outro' — apenas log")
            create_notion_log(sdk, sender_name, subject, classification['category'],
                            classification['score'], "[Sem auto-reply — classificado como outro]")
        
        # 2d. Slack notification
        print("  🔔 Slack notification...")
        notify_slack(sdk, sender_name, subject, classification['category'],
                    classification['score'], SLACK_CHANNEL)
        
        # Marcar como processado
        if "processed_emails" not in state:
            state["processed_emails"] = []
        state["processed_emails"].append(msg_id)
        
        print()
    
    # Salvar estado
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    print(f"{'='*60}")
    print(f"  Processados: {len(messages)} emails")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
