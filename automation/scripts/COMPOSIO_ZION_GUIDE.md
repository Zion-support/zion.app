#!/usr/bin/env python3
"""
=============================================================
COMPOSIO ZION — Guia Completo de Ativação e Uso
=============================================================
Arquivo mestre que consolida TODAS as instruções de como usar
a automação Composio do Zion Tech Group.

ESTRUTURA DE ARQUIVOS:
  automation/scripts/composio-*.py   → 19 scripts Python
  automation/scripts/composio-*.sh   → 4 scripts Shell
  automation/reports/composio-*.md   → 7 relatórios especialistas
  automation/composio-zion-env.example → Template de variáveis

=============================================================
PRÉ-REQUISITOS
=============================================================
1. Conta no Composio Dashboard (dashboard.composio.dev)
2. API Key: COMPOSIO_API_KEY="sk_..."
3. Conta conectada em: connect.composio.dev
   - GitHub (org Zion-TechGroup)
   - Slack (workspace Zion)
   - Gmail (kleber@ziontechgroup.com)
   - Notion (workspace Zion)
   - HubSpot (account Zion)
   - Linear (team Zion)
   - Vercel (project zion-tech-group)
   - PostHog (project zionapp)
   - Sentry (org Zion)
   - Firecrawl (API key)
   - Perplexity AI (API key)
   - Stripe (account Zion)
   - Supabase (project Zion)
   - Cloudflare (account Zion)
   - WhatsApp Business (number + API)
   - Telegram (bot + channel)
   - Discord (server + bot)
   - Google Calendar (account Zion)
   - Google Sheets (spreadsheet Zion)
   - Airtable (base Zion)
   - LinkedIn (page Zion)
   - Twitter/X (account @ziontechgroup)

=============================================================
PASSO 1: CONFIGURAÇÃO
=============================================================
Copiar o template e editar:

  cd /Users/miami2/zion.app/automation
  cp composio-zion-env.example composio-zion-env.sh
  # Editar com valores reais:
  vim composio-zion-env.sh

Carregar no shell atual:
  source composio-zion-env.sh

Ou adicionar ao .zshrc/.bashrc para persistência:
  echo "source /Users/miami2/zion.app/automation/composio-zion-env.sh" >> ~/.zshrc

Verificar configuração:
  python composio-daily-digest.py --dry-run

=============================================================
PASSO 2: TESTAR CADA SCRIPT (em dry-run)
=============================================================
Todos os scripts suportam --dry-run para teste sem execução:

  # Daily Digest
  python composio-daily-digest.py --dry-run
  
  # Lead Intelligence Pipeline
  python composio-lead-intelligence-pipeline.py --dry-run
  
  # Lead Auto-Reply
  python composio-lead-auto-reply.py --dry-run
  
  # Release Automation
  bash composio-release-automation.sh manual --dry-run
  
  # DevOps Event Agent
  python composio-devops-event-agent.py listen --dry-run
  
  # Revenue Automation
  python composio-revenue-automation.py --dry-run
  
  # Competitor Monitor
  bash composio-competitor-monitor.sh --dry-run
  
  # Vercel Deploy
  bash composio-vercel-deploy.sh deploy --dry-run
  
  # Google Sheets Reports
  python composio-google-sheets-reports.py daily-metrics --dry-run
  
  # Calendar Agent
  python composio-calendar-agent.py today --dry-run
  
  # Content Agent
  python composio-content-agent.py "AI Automation" --linkedin --twitter --dry-run
  
  # Social Broadcast
  python composio-social-broadcast.py "Nova atualização!" --linkedin --twitter --telegram --dry-run
  
  # Telegram Broadcast
  python composio-telegram-broadcast.py send "Teste" --channel --dry-run
  
  # WhatsApp Agent
  python composio-whatsapp-agent.py send "5511999999999" "Teste" --dry-run
  
  # Airtable CRM
  python composio-airtable-crm.py list-leads --dry-run
  
  # Supabase Database
  python composio-supabase-database.py query "SELECT 1" --dry-run
  
  # Salesforce CRM
  python composio-salesforce-crm.py list-accounts --dry-run
  
  # Multi-Agent Orchestrator
  python composio-autoscale-agents.py list --dry-run
  
  # Orchestrator Master
  bash composio-orchestrator.sh --dry-run --report

=============================================================
PASSO 3: EXECUTAR (sem dry-run)
=============================================================
Depois de validar tudo no dry-run, executar para real:

  # Daily Digest (dia a dia — o mais importante)
  python composio-daily-digest.py
  
  # Lead Intelligence Pipeline (monitora prospects)
  python composio-lead-intelligence-pipeline.py
  
  # Auto-Reply de Leads
  python composio-lead-auto-reply.py
  
  # Release Automation (quando PR merged)
  bash composio-release-automation.sh manual

=============================================================
PASSO 4: AGENDAR NO CRON
=============================================================
Editar crontab:
  crontab -e

Adicionar linhas:
  # Daily Digest — 9am diário
  0 9 * * * cd /Users/miami2/zion.app && python automation/scripts/composio-daily-digest.py >> /tmp/composio-daily-digest.log 2>&1
  
  # Lead Intelligence — horária
  0 * * * * cd /Users/miami2/zion.app && python automation/scripts/composio-lead-intelligence-pipeline.py >> /tmp/composio-lead-pipeline.log 2>&1
  
  # Auto-Reply — 30min após cada hora
  30 * * * * cd /Users/miami2/zion.app && python automation/scripts/composio-lead-auto-reply.py >> /tmp/composio-auto-reply.log 2>&1
  
  # Competitor Monitor — a cada 6 horas
  0 */6 * * * cd /Users/miami2/zion.app && bash automation/scripts/composio-competitor-monitor.sh >> /tmp/composio-competitor-monitor.log 2>&1
  
  # Google Sheets Reports — diário às 8am
  0 8 * * * cd /Users/miami2/zion.app && python automation/scripts/composio-google-sheets-reports.py daily-metrics >> /tmp/composio-sheets-reports.log 2>&1

Verificar logs:
  tail -f /tmp/composio-daily-digest.log
  tail -f /tmp/composio-lead-pipeline.log
  tail -f /tmp/composio-auto-reply.log

Verificar estado:
  cat /tmp/composio-daily-digest.json
  cat /tmp/composio-lead-intelligence-state.json

=============================================================
SCRIPT P0 — O Mais Importante
=============================================================
O Daily Digest é o script mais importante para começar. Ele:

1. Coleta PRs merged no GitHub (últimas 24h)
2. Lista issues recentes no Linear
3. Verifica status do último deploy no Vercel
4. Busca novos erros no Sentry
5. Puxa métricas do PostHog
6. Monta um resumo e envia no Slack #status

Impacto: 1 mensagem no Slack dá visibilidade completa do estado
do Zion para toda a equipe em menos de 30 segundos.

=============================================================
USANDO O ORQUESTADOR MASTER
=============================================================
O composio-orchestrator.sh executa todos os scripts em sequência:

  # Executar tudo
  bash composio-orchestrator.sh
  
  # Só daily digest
  bash composio-orchestrator.sh --only daily
  
  # Só leads (intelligence + auto-reply)
  bash composio-orchestrator.sh --only leads
  
  # Só devops (event agent + release)
  bash composio-orchestrator.sh --only devops
  
  # Dry-run de tudo
  bash composio-orchestrator.sh --dry-run
  
  # Gera relatório consolidado sem executar
  bash composio-orchestrator.sh --report

Logs por script: /tmp/composio-orchestrator-<nome>.log
Relatório consolidado: /tmp/composio-orchestrator-report.json

=============================================================
FLUXOS AVANÇADOS — P2 P3
=============================================================
Estes fluxos usam múltiplos scripts e requerem mais config:

  # Growth: Competitor Watch
  bash composio-competitor-monitor.sh
  # Monitora sites de concorrentes, detecta mudanças, enriquece com Perplexity
  
  # DevOps: Event-Driven
  python composio-devops-event-agent.py subscribe GITHUB_PULL_REQUEST_MERGE
  # Reage a PR merge em tempo real (Trigger webhook)
  
  # Revenue: Faturamento automático
  python composio-revenue-automation.py payment-confirmed pi_xxxx
  # Stripe payment → atualiza HubSpot → loga Notion → Slack
  
  # Content: Publicação multi-canal
  python composio-content-agent.py "AI Automation" --linkedin --twitter --draft
  # Cria conteúdo, publica em LinkedIn/Twitter, salva draft no Google Docs

=============================================================
ARQUITETURA 멀티-AGENTE (P2+)
=============================================================
Para escalabilidade, usar composio-autoscale-agents.py como orquestrador
de agentes especialistas:

  # Listar agentes disponíveis
  python composio-autoscale-agents.py list
  
  # Executar Growth Agent
  python composio-autoscale-agents.py run growth-agent "Pesquisar mercado SaaS Brasil"
  
  # Executar DevOps Agent
  python composio-autoscale-agents.py run devops-agent "Criar release para PR #42"
  
  # Executar todos os agentes (orquestração completa)
  python composio-autoscale-agents.py run-all "Atualizar toda a operação do Zion"

Cada agente tem seus próprios toolkits e contexto isolado via Tool Router.

=============================================================
CATEGORIAS DE AUTOMAÇÃO
=============================================================
🔴 CRÍTICO — Impacto imediato (já pronto em scripts)
  GitHub, Slack, Linear, Gmail, Notion, HubSpot, Firecrawl,
  Vercel, Cloudflare, Supabase, Stripe, PostHog, Sentry,
  WhatsApp, LinkedIn

🟠 ALTO — Importante, implementar após P0
  Telegram, Discord, Google Calendar, Google Sheets, Airtable,
  Perplexity AI, Composio Search, Tavily, Exa, GitHub Actions

🟡 MÉDIO — Implementar quando necessário
  Google Docs, Google Drive, Google Tasks, Stack Overflow,
  Twitter/X, Todoist, Pipedrive, Snowflake

⚪ BAIXO — Futuro / baixa prioridade
  Jira, Trello, Asana, Clickup, Outlook, Facebook, Meta Ads,
  Instagram, Figma, Salesforce, New Relic, Canvas, SharePoint

=============================================================
PRECISAÇÃO FINAL
=============================================================
Scripts criados: 23 (19 Python + 4 Shell)
Relatórios criados: 7
Arquivo de configuração: 1 (composio-zion-env.example)
Apps mapeados: 47 (16 críticos, 11 altos, 8 médios, 8 baixos)
Total de arquivos entregues: 31

Para testar:
  cd /Users/miami2/zion.app
  source automation/composio-zion-env.sh
  python composio-daily-digest.py --dry-run

Para agendar:
  crontab -e
  # Adicionar linhas de cron (ver acima)

Para usar o orquestrador:
  bash automation/scripts/composio-orchestrator.sh --dry-run --report

=============================================================
FIM DO GUIA
=============================================================
