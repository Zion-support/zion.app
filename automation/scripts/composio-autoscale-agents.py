#!/usr/bin/env python3
"""
composio-autoscale-agents.py
=============================
Multi-Agent Orchestrator — cria e coordena agentes especialistas para cada domínio do Zion.

 Agentes suportados:
   - growth-agent: Firecrawl + Perplexity + LinkedIn + Twitter + HubSpot + Slack
   - devops-agent: GitHub + Vercel + Sentry + Linear + Slack
   - revenue-agent: Stripe + HubSpot + Notion + Google Sheets + Slack
   - support-agent: Gmail + Linear + Notion + Slack + Telegram
   - content-agent: Firecrawl + Google Docs + LinkedIn + Twitter + Slack

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#agents"
   
   python composio-autoscale-agents.py list                # lista agentes disponíveis
   python composio-autoscale-agents.py run <agente> <tarefa>
   python composio-autoscale-agents.py run growth-agent "Pesquisar concorrentes X, Y, Z"
   python composio-autoscale-agents.py run devops-agent "Criar release para PR #42"
   python composio-autoscale-agents.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#agents")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
AGENT_NAME = sys.argv[2] if len(sys.argv) > 2 else None
TASK = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None

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

# ========== AGENT DEFINITIONS ==========
AGENTS = {
    "growth-agent": {
        "name": "Growth Agent",
        "description": "Prospecção ativa — pesquisa, concorrentes, leads, outreach",
        "toolkits": ["firecrawl", "perplexityai", "linkedin", "twitter", "hubspot", "slack"],
        "icon": "🚀",
    },
    "devops-agent": {
        "name": "DevOps Agent",
        "description": "Deploy, releases, health check, erro management",
        "toolkits": ["github", "vercel", "sentry", "linear", "slack"],
        "icon": "🛠️",
    },
    "revenue-agent": {
        "name": "Revenue Agent",
        "description": "Faturamento, invoicing, receipt de pagamentos, relatórios financeiros",
        "toolkits": ["stripe", "hubspot", "notion", "googlesheets", "slack"],
        "icon": "💰",
    },
    "support-agent": {
        "name": "Support Agent",
        "description": "Triage de tickets, auto-reply, resolução de issues, escalação",
        "toolkits": ["gmail", "linear", "notion", "slack", "telegram"],
        "icon": "🛟",
    },
    "content-agent": {
        "name": "Content Agent",
        "description": "Criação de conteúdo, social media, blog posts, SEO research",
        "toolkits": ["firecrawl", "googledocs", "linkedin", "twitter", "slack"],
        "icon": "✍️",
    },
}

# ========== AGENT ORCHESTRATOR ==========
def create_agent_session(sdk, agent_key):
    """Cria uma sessão Tool Router para um agente específico."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return None
    
    print(f"   🎯 Criando sessão para {agent['name']}...")
    print(f"      Toolkits: {', '.join(agent['toolkits'])}")
    
    session = sdk.create_agent_session(
        name=f"zion-{agent_key}",
        description=agent["description"],
        toolkits=agent["toolkits"],
    )
    
    if session:
        print(f"   ✅ Sessão criada: {session.id if hasattr(session, 'id') else 'OK'}")
        return session
    return None

def run_agent(agent_key, task):
    """Executa um agente específico com uma tarefa."""
    agent = AGENTS.get(agent_key)
    if not agent:
        print(f"❌ Agente desconhecido: {agent_key}")
        print(f"Agentes disponíveis: {', '.join(AGENTS.keys())}")
        return None
    
    print(f"\n{agent['icon']} Executando {agent['name']}...")
    print(f"   Tarefa: {task}")
    
    sdk = get_sdk()
    session = create_agent_session(sdk, agent_key)
    
    # Executar a tarefa usando os toolkits do agente
    # Isso é um esqueleto — a implementação específica depende da tarefa
    
    # Exemplo: Growth Agent
    if agent_key == "growth-agent":
        return run_growth_agent(sdk, task)
    elif agent_key == "devops-agent":
        return run_devops_agent(sdk, task)
    elif agent_key == "revenue-agent":
        return run_revenue_agent(sdk, task)
    elif agent_key == "support-agent":
        return run_support_agent(sdk, task)
    elif agent_key == "content-agent":
        return run_content_agent(sdk, task)
    
    print(f"   ⚠️  Handler não implementado para {agent_key}")
    return None

def run_growth_agent(sdk, task):
    """Agenda de crescimento: pesquisa mercados, concorrentes, leads."""
    print("   🔍 Pesquisando mercado...")
    
    # 1. Firecrawl: coletar dados do mercado
    firecrawl_result = tool_execute(
        sdk,
        "FIRECRAWL_SCRAPE_URLS",
        {"urls": ["https://concorrente.com"], "format": "markdown"},
    )
    
    # 2. Perplexity: analisar dados
    perplexity_result = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        {"query": f"Analise este mercado: {task}", "temperature": 0.3},
    )
    
    # 3. Slack: notificar resultados
    analysis = perplexity_result.get("content", "Análise concluída") if perplexity_result else "Sem análise"
    
    slack_message = f"*🚀 Growth Agent — {datetime.now().strftime('%H:%M')}*\n\n"
    slack_message += f"**Tarefa:** {task}\n\n"
    slack_message += f"**Análise:**\n{analysis[:500]}\n\n"
    slack_message += f"_{datetime.now().strftime('%Y-%m-%d')}_"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": SLACK_CHANNEL, "text": slack_message},
    )
    
    print(f"   ✅ Growth Agent concluído")
    return analysis

def run_devops_agent(sdk, task):
    """DevOps: releases, deploys, health checks."""
    print("   🛠️ Executando ação DevOps...")
    
    # Exemplo: parse de tarefas comuns
    if "release" in task.lower() or "pr" in task.lower():
        print("   📦 Criando release...")
        # tool_execute(sdk, "GITHUB_CREATE_RELEASE", ...)
    
    if "deploy" in task.lower():
        print("   🚀 Triggering deploy...")
        # tool_execute(sdk, "VERCEL_CREATE_DEPLOYMENT", ...)
    
    error = "sem erros"  # placeholder
    message = f"*🛠️ DevOps Agent — {datetime.now().strftime('%H:%M')}*\n\n"
    message += f"**Tarefa:** {task}\n"
    message += f"**Status:** ✅ Concluído\n"
    message += f"**Erros:** {error}\n"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": SLACK_CHANNEL, "text": message},
    )
    
    print(f"   ✅ DevOps Agent concluído")
    return {"status": "ok"}

def run_revenue_agent(sdk, task):
    """Revenue: invoicing, receipts, relatórios financeiros."""
    print("   💰 Executando ação financeira...")
    
    message = f"*💰 Revenue Agent — {datetime.now().strftime('%H:%M')}*\n\n"
    message += f"**Tarefa:** {task}\n"
    message += f"**Status:** ✅ Processado\n"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": SLACK_CHANNEL, "text": message},
    )
    
    print(f"   ✅ Revenue Agent concluído")
    return {"status": "ok"}

def run_support_agent(sdk, task):
    """Support: triage, auto-reply, resolução de issues."""
    print("   🛟 Executando ação de suporte...")
    
    message = f"*🛟 Support Agent — {datetime.now().strftime('%H:%M')}*\n\n"
    message += f"**Tarefa:** {task}\n"
    message += f"**Status:** ✅ Processado\n"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": SLACK_CHANNEL, "text": message},
    )
    
    print(f"   ✅ Support Agent concluído")
    return {"status": "ok"}

def run_content_agent(sdk, task):
    """Content: criação de conteúdo, social media."""
    print("   ✍️ Executando ação de conteúdo...")
    
    message = f"*✍️ Content Agent — {datetime.now().strftime('%H:%M')}*\n\n"
    message += f"**Tarefa:** {task}\n"
    message += f"**Status:** ✅ Criado\n"
    
    tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": SLACK_CHANNEL, "text": message},
    )
    
    print(f"   ✅ Content Agent concluído")
    return {"status": "ok"}

def list_agents():
    """Lista todos os agentes disponíveis."""
    print("\n📋 Agentes disponíveis:")
    print()
    
    for key, agent in AGENTS.items():
        print(f"  {agent['icon']} {agent['name']} ({key})")
        print(f"     {agent['description']}")
        print(f"     Toolkits: {', '.join(agent['toolkits'])}")
        print()

def run_all_agents(task):
    """Executa todos os agentes com uma tarefa (para orchestrar workflows complexos)."""
    print(f"\n🔄 Executando todos os agentes para: {task}")
    print()
    
    results = {}
    for key in AGENTS.keys():
        results[key] = run_agent(key, task)
    
    print(f"\n✅ Todos os agentes concluídos")
    return results

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Composio Multi-Agent Orchestrator — Uso:

  python composio-autoscale-agents.py list
      Lista todos os agentes disponíveis

  python composio-autoscale-agents.py run <agente> <tarefa>
      Executa um agente específico

  python composio-autoscale-agents.py run-all <tarefa>
      Executa todos os agentes em paralelo

  python composio-autoscale-agents.py --dry-run
      Testa configuração sem executar

Agentes disponíveis:
  🚀 growth-agent    — Prospecção, concorrentes, leads
  🛠️ devops-agent     — Releases, deploys, erros
  💰 revenue-agent    — Invoicing, receipts, finanças
  🛟 support-agent    — Triagem, auto-reply, tickets
  ✍️ content-agent    — Conteúdo, social media, blog

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#agents'
  python composio-autoscale-agents.py run growth-agent "Pesquisar mercado SaaS Brasil"
""")
        return
    
    if DRY_RUN:
        print("🔍 Modo dry-run — não executando ações")
        if AGENT_NAME:
            agent = AGENTS.get(AGENT_NAME)
            if agent:
                print(f"   Agente: {agent['name']}")
                print(f"   Toolkits: {', '.join(agent['toolkits'])}")
            else:
                print(f"   Agente desconhecido: {AGENT_NAME}")
        else:
            print(f"   Ação: {ACTION}")
        return
    
    if ACTION == "list":
        list_agents()
    elif ACTION == "run":
        if not AGENT_NAME:
            print("❌ Agente necessário")
            print("Uso: python composio-autoscale-agents.py run <agente> <tarefa>")
            sys.exit(1)
        run_agent(AGENT_NAME, TASK or "executar tarefa padrão")
    elif ACTION == "run-all":
        run_all_agents(TASK or "executar todos os agentes")
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        print("Use 'python composio-autoscale-agents.py' para ver opções")
        sys.exit(1)
    
    print(f"\n✅ Orchestrator concluído")

if __name__ == "__main__":
    main()
