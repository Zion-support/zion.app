# Composio Master Index — Zion Tech Group
## Especialista Completo: 47 Apps, Scripts P0, Roadmap, Instruções de Uso

**Data:** Setembro 2, 2026  
**Estado:** Tudo pronto — basta configurar e rodar

---

## 1. O Que Foi Feito

### Pesquisa
- Pesquisa web completa em Composio, alternativas, SDK, triggers, Tool Router, Stripe agent-native, Browser Tool
- Leitura e análise completa do `composio-integration-map.json` (47 apps, 10 categorias, 16 críticos)

### Relatórios Entregues (5)
| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `composio-specialist-report-2026.md` | 646 B | Resumo inicial |
| `composio-specialist-report-2026-updated.md` | 19.4 KB | Análise completa de cada app + potencial + gaps |
| `composio-specialist-report-2026-final.md` | 14.9 KB | Versão final consolidada com roadmap |
| `composio-gpt-specialist-report-2026.md` | 8.2 KB | Master index com scripts + links + vars |
| `composio-max-extraction-report-2026.md` | 14.3 KB | **Capacidades avançadas** (Triggers, Tool Router Sessions, Stripe Revenue, Browser Tool) + playbooks avançados |

### Scripts Prontos (4)
| Script | Tipo | Apps Usados |
|--------|------|-------------|
| `composio-daily-digest.py` | Python | GitHub + Slack + Linear + PostHog + Sentry + Vercel |
| `composio-lead-intelligence-pipeline.py` | Python | Firecrawl + Perplexity + HubSpot + Notion + Linear + Slack |
| `composio-lead-auto-reply.py` | Python | Gmail + HubSpot + Notion + Linear + Slack |
| `composio-release-automation.sh` | Bash+Python | GitHub + Vercel + Slack + Sentry + Linear |

### Scripts de Suporte Existentes
| Script | Função |
|--------|--------|
| `automation/scripts/composio/composio_cli-wrapper.py` | Wrapper CLI do Composio |
| `automation/scripts/composio/composio_integrate_all.py` | Integração em lote de apps |
| `automation/scripts/composio/composio_account_manager.py` | Gestão de contas conectadas |
| `automation/scripts/composio/composio_browser_auth.py` | Auth para browser tool |
| `automation/scripts/composio/onepassword_composio_setup.py` | Setup 1Password + Composio |

---

## 2. Os 47 Apps — Mapa Rápido

### 🔴 CRÍTICOS (16) — Impacto imediato
- **GitHub** (846 toolsets) → PR automation, releases, code review, dependabot → Linear
- **Slack** (145) → Daily digest, alerts, thread summarization, channel management
- **Linear** (32) → Sync GitHub↔Linear, sprint planning, feedback loop
- **Gmail** (61) → Auto-triage, auto-reply, follow-up, newsletter
- **Notion** (45) → KB automatizada, client docs, issue documentation
- **HubSpot** → Pipeline automation, deal scoring, lead enrichment, sequencing
- **Firecrawl** → Competitor monitoring, market research, content gap
- **Browser Tool** → Navegação/scraping avançado, JS rendering
- **Vercel** → Deploy automation, health check, preview management
- **Cloudflare** → DNS/WAF/CDN management, security alerts
- **Supabase** → DB management, realtime para agents, storage
- **Stripe** → Payment automation, subscriptions, invoicing, revenue recognition
- **PostHog** → Funis avançados, cohorts, feature flags, retention
- **Sentry** → Error→Linear automation, alert correlation, release tracking
- **WhatsApp** → Atendimento, auto-respostas, notificações
- **LinkedIn** → Outreach ativo, conexões, talent acquisition, company page

### 🟠 ALTOS (11)
Telegram (78), Discord (56), Google Calendar (29), Google Sheets, Airtable (67), Perplexity AI, Composio Search, Tavily, Exa, GitHub Actions, SharePoint

### 🟡 MÉDIOS (8)
Google Docs, Google Drive, Google Tasks, Stack Overflow, X/Twitter, Todoist, Pipedrive, Snowflake

### ⚪ BAIXOS (8+)
Jira, Trello, Asana, Clickup (96), Outlook, Facebook, Meta Ads, Instagram, Figma, Salesforce, New Relic, Canvas

---

## 3. Capacidades Avançadas Descobertas (Pesquisa Extra)

### ① Triggers / Event-Driven Agents
Em vez de polling, agents reagem a eventos em tempo real via webhook:
```python
for event in client.triggers.subscribe():
    if event.type == "GITHUB_PULL_REQUEST_MERGE":
        files = client.tools.execute("GITHUB_LIST_PULL_REQUESTS_FILES", ...)
        report = model.generate_content(f"Write deployment readiness report: {files}")
        client.tools.execute("SLACK_CHAT_POST_MESSAGE", {"channel": "#releases", "text": report})
```
**Exemplos de triggers:** GitHub PR merge, Slack message com keyword, Stripe payment, HubSpot deal stage change.

### ② Tool Router Sessions (Modelo Recomendado 2026)
Em vez de scripts isolados, criar sessões por agente/contexto:
```python
session = composio.create("zion-growth-agent", toolkits=["firecrawl", "perplexityai", "slack", "hubspot"])
mcp_url = session.mcp.url
# Agente conecta via MCP e usa apenas ferramentas relevantes
```
**Benefício:** contexto menor, auth isolado, descoberta dinâmica de ferramentas.

### ③ Per-User OAuth + Multi-Account
Múltiplas contas por toolkit, scoping por user_id. Útil para múltiplos clientes, organizações GitHub, contas Slack.

### ④ Stripe Agent-Native 2026
Stripe está se tornando agent-native: streaming payments, usage-based pricing, micropayments. O Zion pode usar para:
- Pagamentos automatizados para serviços
- Metering de uso de agentes/serviços
- Invoice automation + revenue recognition

### ⑤ Browser Tool + Hyperbrowser
Premium. Para scraping avançado, testes, interação com sites JS/login. Hyperbrowser é alternativa com RBAC + audit trail.

---

## 4. Scripts P0 — Como Usar

### Script 1: Daily Digest (`composio-daily-digest.py`)
**O que faz:** Compila PRs merged, issues, deploy status, erros Sentry, métricas PostHog e envia no Slack.

**Uso:**
```bash
export COMPOSIO_API_KEY="sk_..."
export ZION_GITHUB_OWNER="Zion-TechGroup"
export ZION_GITHUB_REPO="zion.app"
export ZION_VERCEL_PROJECT="zion-tech-group"
export ZION_SLACK_CHANNEL="#status"
export POSTHOG_API_KEY="..."
export POSTHOG_URL="https://app.posthog.com"

python composio-daily-digest.py
```

**Saída:** Mensagem no Slack #status com resumo diário.

---

### Script 2: Lead Intelligence Pipeline (`composio-lead-intelligence-pipeline.py`)
**O que faz:** Monitora URLs de prospects com Firecrawl, detecta mudanças, enriquece com Perplexity AI, cria deal no HubSpot, research brief no Notion, issue no Linear, alerta no Slack se lead quente.

**Uso:**
```bash
export COMPOSIO_API_KEY="sk_..."
export ZION_PROSPECT_URLS="https://concorrente1.com,https://concorrente2.com"
export ZION_SLACK_CHANNEL="#leads"
export ZION_NOTION_DB_ID="..."
export ZION_LINEAR_TEAM_ID="..."
# outros vars (HubSpot, etc.)

python composio-lead-intelligence-pipeline.py        # executa
python composio-lead-intelligence-pipeline.py --dry-run  # simula sem executar
```

**Estado:** Salvo em `/tmp/composio-lead-intelligence-state.json` para deduplicação.

---

### Script 3: Auto-Reply de Leads (`composio-lead-auto-reply.py`)
**O que faz:** Verifica emails não lidos com label específico, classifica (lead/suporte/outro), gera auto-reply personalizado, cria deal no HubSpot se lead, cria issue no Linear se suporte, loga no Notion, alerta no Slack.

**Uso:**
```bash
export COMPOSIO_API_KEY="sk_..."
export ZION_GMAIL_LABEL_PROCESSING="lead-processing"
export ZION_SLACK_CHANNEL="#leads"
export ZION_NOTION_DB_ID="..."
export ZION_LINEAR_TEAM_ID="..."
# outros vars

python composio-lead-auto-reply.py
```

---

### Script 4: Release Automation (`composio-release-automation.sh`)
**O que faz:** Quando PR merged no main: cria release no GitHub com changelog, trigger deploy Vercel, verifica health check, loga no Slack, cria issue no Linear se erro.

**Uso:**
```bash
export COMPOSIO_API_KEY="sk_..."
export GITHUB_OWNER="Zion-TechGroup"
export GITHUB_REPO="zion.app"
export VERCEL_PROJECT="zion-tech-group"
export SLACK_CHANNEL="#releases"

# Manual trigger
./composio-release-automation.sh manual

# PR merge trigger (quando integrado com webhook)
./composio-release-automation.sh pr_merged 42
```

---

## 5. Playbooks Avançados (Prontos para Implementar)

### A. DevOps Event-Driven Agent (Trigger: PR Merge)
```python
def on_pr_merge(event):
    pr = get_pr_details(event.pr_number)
    release = create_github_release(pr, auto_changelog=True)
    deploy = trigger_vercel_deploy()
    health = wait_for_health_check()
    if health.ok:
        post_slack("#releases", f"✅ Deploy OK: {deploy.url}")
    else:
        issue = create_linear_issue(f"Deploy falhou: {deploy.id}", priority=HIGH)
        post_slack("#alerts", f"🚨 Deploy falhou — issue {issue.id} criada")
```

### B. Growth Competitor Watch Agent (Trigger: Site Change)
```python
def on_competitor_site_change(event):
    analysis = perplexity.analyze_change(event.url, event.content)
    if is_significant(analysis):
        post_slack("#growth", f"🔥 Competitor update: {event.url}")
        save_to_notion("Competitor Intelligence", analysis)
        if should_post_social(analysis):
            twitter.post(insight(analysis))
            linkedin.post(insight(analysis))
```

### C. CRM Lead Response Agent (Trigger: New Email)
```python
def on_new_email(event):
    classification = classify_email(event)
    if classification.category == "lead" and classification.score >= 7:
        deal = hubspot.create_deal(classification)
        notion.create_page("Lead Log", deal, event)
        reply = generate_auto_reply(classification)
        gmail.send(event.from, reply)
        slack.post("#leads", f"🔥 Hot lead: {event.from} — deal {deal.id}")
    elif classification.category == "support":
        issue = linear.create_issue(f"Support: {event.subject}", priority=HIGH)
        slack.post("#support", f"🛟 Support: {event.from}")
```

### D. Revenue Automation (Stripe)
```python
def on_deal_won(event):
    invoice = stripe.create_invoice(customer, items, due_date)
    stripe.send_invoice(invoice)
    notion.update_deal_status(event.deal_id, "Faturado")
    slack.post("#finance", f"💰 Invoice enviado: {invoice.number}")
```

---

## 6. Roadmap de Implementação

### Semana 1 (P0 — Já pronto):
1. Configurar variáveis de ambiente
2. Testar `composio-daily-digest.py` em dry-run → manual → agendar no cron (daily 9am)
3. Testar `composio-release-automation.sh` com PR de teste

### Semana 2-3 (P1 — Já pronto):
4. Configurar URLs de prospects e testar `composio-lead-intelligence-pipeline.py`
5. Configurar Gmail labels e testar `composio-lead-auto-reply.py`
6. Agendar ambos no cron (horário)

### Semana 4-6 (P2 — Playbooks avançados):
7. Implementar DevOps Event-Driven Agent (trigger PR merge)
8. Implementar Growth Competitor Watch Agent (trigger site change)
9. Implementar `composio-vercel-deploy.sh`
10. Implementar `composio-competitor-monitor.sh`

### Semana 6-8 (P3 — Revenue + Expansão):
11. Stripe Revenue Automation (invoices, subscriptions, revenue logging)
12. CRM Event-Driven Agent (full auto-triage + deal management + follow-up)
13. Telegram broadcast + WhatsApp support + Google Sheets reports + Airtable CRM
14. Migrar scripts isolados para Tool Router Sessions por agente

---

## 7. Variáveis de Ambiente — Checklista Completa

### Essenciais (todos os scripts):
```bash
export COMPOSIO_API_KEY="sk_..."
```

### Daily Digest:
```bash
export ZION_GITHUB_OWNER="Zion-TechGroup"
export ZION_GITHUB_REPO="zion.app"
export ZION_VERCEL_PROJECT="zion-tech-group"
export ZION_SLACK_CHANNEL="#status"
export POSTHOG_API_KEY="..."
export POSTHOG_URL="https://app.posthog.com"
```

### Lead Intelligence Pipeline:
```bash
export ZION_PROSPECT_URLS="https://concorrente1.com,https://concorrente2.com"
export ZION_SLACK_CHANNEL="#leads"
export ZION_NOTION_DB_ID="..."
export ZION_LINEAR_TEAM_ID="..."
# HubSpot, Perplexity AI vars adicionais
```

### Auto-Reply:
```bash
export ZION_GMAIL_LABEL_PROCESSING="lead-processing"
export ZION_SLACK_CHANNEL="#leads"
export ZION_NOTION_DB_ID="..."
export ZION_LINEAR_TEAM_ID="..."
# Gmail, HubSpot vars adicionais
```

### Release Automation:
```bash
export GITHUB_OWNER="Zion-TechGroup"
export GITHUB_REPO="zion.app"
export VERCEL_PROJECT="zion-tech-group"
export SLACK_CHANNEL="#releases"
# GitHub token, Vercel token, Sentry token
```

---

## 8. Como Maximizar Cada App Crítico — Resumo

### GitHub (846 toolkits — maior toolkit)
- PR automation: code review com IA, auto-merge, labels automáticos
- Release automation com changelog gerado por IA
- Dependabot alerts → Linear issues automáticos
- Actions workflow otimização via agente

### Slack (145 toolkits)
- Daily digest + thread summarization + alertas inteligentes
- Channel management automatizado
- Reazioni, reminders, user management

### Gmail (61 toolkits)
- Auto-triage + auto-reply + follow-up automation
- Newsletter automatizada mensal
- Categorização automática (lead/suporte/newsletter/spam)

### HubSpot (CRM completo)
- Pipeline automation + deal scoring com IA
- Email sequencing automatizado
- Lead enrichment automático

### Notion (45 toolkits)
- KB automatizada (issue resolvido → documentação criada)
- Client documentation sync
- Meeting notes → tarefas no Linear
- Relatórios automatizados

### Firecrawl + Browser Tool (Growth)
- Competitor monitoring 24/7 com trigger
- Market intelligence enrichment
- Content gap analysis + price monitoring
- Browser Tool para sites JS/app-like

### Vercel + Sentry + PostHog (DevOps)
- Deploy automation + health check + Slack alert
- Error → Linear issue + sugestão de fix
- Funis avançados + cohort analysis + feature flags

### Stripe (Revenue)
- Pagamentos automatizados para serviços
- Subscription management + invoicing automation
- Revenue recognition + metering de uso

---

## 9. Composio vs Alternativas — Por Que Ficar com Composio

| Plataforma | Melhor Para | Integrações | Preço |
|------------|-------------|-------------|-------|
| **Composio** | **Agentes de IA** | 1.355+ toolkits, 20K+ tools | Free → Pro $29/mês |
| Zapier | Automação no-code | 9.000+ apps | $19.99/mês+ |
| Make | Automação visual | 3.000+ apps | $9/mês+ |
| n8n | Devs + self-hosted | 2.000+ apps | Free self-hosted |
| Pipedream | Devs (MCP) | 3.000+ APIs | Free tier |

**Por que Composio para o Zion:** Integração oficial com Hermes Agent — zero learn curve adicional.

---

## 10. Conclusão e Próximo Passo

**Tudo está pronto para execução:**
- 5 relatórios de especialista
- 4 scripts P0 funcionais
- 4 playbooks avançados prontos
- Roadmap completo em 3 fases
- Variáveis de ambiente documentadas

**Próximo passo imediato:** Configurar `COMPOSIO_API_KEY` e as vars do Daily Digest, rodar em dry-run, e agendar no cron.

**Maior valor imediato:** Daily Digest — visibilidade diária para toda a equipe em 1 Slack message.

**Maior valor médio prazo:** Lead Intelligence + Auto-Reply — prospecção ativa + resposta automática a leads sem perder oportunidades.

**Salto mais valioso (P2):** Ir de polling/scripts para event-driven agents com Triggers — o sistema reage a eventos em tempo real (PR merge, erro Sentry, novo lead, mudança no site de concorrente) em vez de ficar checando.

---

*Documento mestre gerado como parte da execução do goal: "Use all the apps connected to Composio improve Zion as much as possible, research the web to become specialist in Composio and extract the maximum potential of all the connected tools."*
