#!/usr/bin/env python3
"""
composio-lead-intelligence-pipeline.py
=====================================================
Pipeline de Intelligence de Leads: Firecrawl + Gmail + HubSpot + Notion + Linear + Slack

 Monitora sites de prospects chave, detecta mudanças relevantes,
 enriquece leads, cria deals no HubSpot, documenta no Notion,
 cria issues no Linear, e notifica no Slack.

 Uso: python composio-lead-intelligence-pipeline.py [--dry-run]
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from composio import Composio
from composio.core.types import ComposeToolName

# ========== CONFIG ==========
PROSPECT_URLS = os.environ.get("ZION_PROSPECT_URLS", "").split(",")
PROSPECT_URLS = [u.strip() for u in PROSPECT_URLS if u.strip()]
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#leads")
STATE_FILE = "/tmp/composio-lead-intelligence-state.json"
DRY_RUN = "--dry-run" in sys.argv

# ========== STATE MANAGEMENT ==========
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"processed": {}, "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]

# ========== COMPOSI SETUP ==========
def get_sdk():
    api_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not api_key:
        print("ERRO: COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    return Composio(api_key=api_key)

# ========== COMPOSIO TOOL WRAPPERS ==========
def tool_execute(sdk, tool_name, args, user_id="zion-bot"):
    """Wrapper seguro para tool_execute com tratamento de erro."""
    try:
        result = sdk.tools.execute(
            tool_name,
            arguments=args,
            user_id=user_id,
        )
        return result
    except Exception as e:
        print(f"  ⚠ Erro em {tool_name}: {e}")
        return None

# ========== MONITORING COM FIRECRAWL ==========
def monitor_prospect_urls(sdk, urls, state):
    """Scanea URLs monitoradas e detecta mudanças."""
    results = []
    for url in urls:
        url_id = url_hash(url)
        last_state = state.get("processed", {}).get(url_id, {})
        last_content_hash = last_state.get("content_hash")
        
        print(f"  Scaneando: {url}")
        
        # Firecrawl scrape
        scrape_result = tool_execute(
            sdk,
            "FIRECRAWL_SCRAPE_URLS",
            {"urls": [url], "format": "markdown", "extract": True},
        )
        
        if not scrape_result:
            continue
        
        content = scrape_result.get("data", "")
        current_hash = hashlib.md5(content.encode()).hexdigest()[:12] if content else None
        
        changed = current_hash != last_content_hash
        
        entry = {
            "url": url,
            "url_id": url_id,
            "changed": changed,
            "content_hash": current_hash,
            "scraped_at": datetime.now().isoformat(),
            "content_preview": content[:200] if content else "",
        }
        results.append(entry)
        
        # Update state
        if "processed" not in state:
            state["processed"] = {}
        state["processed"][url_id] = {
            "content_hash": current_hash,
            "last_scraped": entry["scraped_at"],
        }
        
        status = "🆕 NOVO" if not last_content_hash else ("🔄 MUDOU" if changed else "✅ IGUAL")
        print(f"    → {status} (hash: {current_hash})")
    
    return [r for r in results if r["changed"]]

# ========== ENRICHMENT COM PERPLEXITY AI ==========
def enrich_lead_with_perplexity(sdk, url, content_preview):
    """Usa Perplexity AI para analisar o conteúdo e extrair intelligence."""
    prompt = f"""
Analise este conteúdo de um site de empresa prospect e extraia:
1. Nome da empresa (se identificável)
2. O que mudou/provavelmente é novo no site
3. Potencial de interesse para serviços de IA/automação do Zion Tech Group
4. Indicadores de maturidade tecnológica (Cloud, AI, modern stack mencionados?)
5. Pontos de entrada para prospecção

Conteúdo analisado ({len(content_preview)} chars):
---
{content_preview}
---

Forneça uma análise concisa em bullets, foco em actionability.
"""
    
    result = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        {"query": prompt, "temperature": 0.3, "max_tokens": 1000},
    )
    
    if result and isinstance(result, dict):
        return result.get("content", result.get("text", str(result)))
    return str(result) if result else "Erro na enrichment."

# ========== CRM INTEGRATION (HUBSPOT) ==========
def create_or_update_hubspot_deal(sdk, company_name, intelligence, url):
    """Cria ou atualiza deal no HubSpot."""
    deal_name = f"{company_name[:50]} — Lead Intelligence"
    
    result = tool_execute(
        sdk,
        "HUBSPOT_CREATE_DEAL",
        {
            "dealname": deal_name,
            "dealstage": "appointmentscheduled",  # ou appropriate stage
            "description": intelligence[:2000],
            "amount": 0,  # a estimar
            "pipeline": "default",
        },
    )
    
    if result:
        deal_id = result.get("id", result.get("dealId", "desconhecido"))
        print(f"  → Deal criado no HubSpot: {deal_id}")
        return deal_id
    return None

# ========== DOCUMENTAÇÃO (NOTION) ==========
def create_notion_research_brief(sdk, company_name, intelligence, url, perplexity_analysis):
    """Cria página de research brief no Notion."""
    page_title = f"🔍 {company_name[:60]} — Research Brief"
    
    content = f"""
## Research Brief — {company_name}

**URL monitorada:** [{url}]({url})
**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Inteligência detectada:** Isso mudou no site

### Inteligência Extraída
{intelligence}

### Análise Perplexity AI
{perplexity_analysis}

### Próximos Passos
- [ ] Validar informações com pesquisa adicional
- [ ] Priorizar se é lead quente
- [ ] Preparar abordagem personalizada
"""
    
    result = tool_execute(
        sdk,
        "NOTION_CREATE_PAGE",
        {
            "parent": {"database_id": os.environ.get("ZION_NOTION_DB_ID", "")},
            "properties": {
                "title": {"title": [{"text": {"content": page_title}}]},
                "Status": {"select": {"name": "Nova Pesquisa"}},
                "URL": {"url": url},
                "Data": {"rich_text": [{"text": {"content": datetime.now().strftime('%Y-%m-%d')}}]},
            },
            "children": [
                {"object": "block", "type": "paragraph", "paragraph": {"text": {"content": content}}}
            ],
        },
    )
    
    if result:
        page_id = result.get("id", result.get("pageId", "desconhecido"))
        print(f"  → Notion page criada: {page_id}")
        return page_id
    return None

# ========== ISSUES (LINEAR) ==========
def create_linear_issue(sdk, company_name, action_item, url):
    """Cria issue no Linear para ação necessária."""
    title = f"Prospecção: {company_name[:50]} — {action_item[:60]}"
    
    result = tool_execute(
        sdk,
        "LINEAR_CREATE_ISSUE",
        {
            "teamId": os.environ.get("ZION_LINEAR_TEAM_ID", ""),
            "title": title,
            "description": f"**URL:** {url}\n\n**Ação necessária:** {action_item}",
            "priority": 2,  # medium
        },
    )
    
    if result:
        issue_id = result.get("id", result.get("issueId", "desconhecido"))
        print(f"  → Linear issue criado: {issue_id}")
        return issue_id
    return None

# ========== SLACK NOTIFICATION ==========
def notify_slack_hot_lead(sdk, company_name, intelligence_preview, url, slack_channel):
    """Notifica no Slack se lead parece quente."""
    message = f"""*🔥 Lead Inteligente Detectado — {company_name}*

**Site:** {url}
**Resumo:** {intelligence_preview[:300]}

Uma mudança foi detectada no site de um prospect. Research brief criada no Notion.
"""
    
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        {"channel": slack_channel, "text": message},
    )
    
    if result:
        print(f"  → Notificação Slack enviada para {slack_channel}")
    return result

# ========== MAIN PIPELINE ==========
def main():
    sdk = get_sdk()
    state = load_state()
    dry_run = DRY_RUN
    
    print(f"\n{'='*60}")
    print(f"  Lead Intelligence Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    if dry_run:
        print("  ⚠️ MODO DRY RUN — nenhuma ação será executada")
    print()
    
    # 1. Monitorar URLs
    print("📡 Passo 1: Monitorando URLs de prospects...")
    if not PROSPECT_URLS:
        print("  ERRO: ZION_PROSPECT_URLS não configurado")
        print("  Exemplo: export ZION_PROSPECT_URLS='https://concorrente1.com,https://concorrente2.com'")
        sys.exit(1)
    
    changed_urls = monitor_prospect_urls(sdk, PROSPECT_URLS, state)
    print(f"\n  → {len(changed_urls)} URL(s) com mudanças detectadas\n")
    
    if not changed_urls:
        print("✅ Nenhuma mudança detectada. Pipeline concluído.")
        save_state(state)
        return
    
    # 2. Para cada URL alterada, executar enrichment + CRM + docs
    for entry in changed_urls:
        url = entry["url"]
        content = entry.get("content_preview", "")
        
        # Uso um ID simples baseado na URL
        company_name = url.split("/")[2].replace("www.", "") if "://" in url else url
        
        print(f"\n{'─'*50}")
        print(f"  Processando: {company_name}")
        print(f"{'─'*50}")
        
        # 2a. Enriquecer com Perplexity
        print("🧠 Passo 2: Enrichment com Perplexity AI...")
        perplexity_analysis = enrich_lead_with_perplexity(sdk, url, content)
        print(f"  Análise: {perplexity_analysis[:150]}...")
        
        # 2b. Criar deal no HubSpot
        print("💼 Passo 3: Criando deal no HubSpot...")
        deal_id = create_or_update_hubspot_deal(sdk, company_name, perplexity_analysis, url)
        
        # 2c. Criar research brief no Notion
        print("📝 Passo 4: Criando research brief no Notion...")
        page_id = create_notion_research_brief(
            sdk, company_name, perplexity_analysis, url, perplexity_analysis
        )
        
        # 2d. Criar issue no Linear para follow-up
        print("📋 Passo 5: Criando issue no Linear...")
        action = "Validar lead e preparar abordagem" if "hotmail" not in url else "Verificar disponibilidade para reunião"
        issue_id = create_linear_issue(sdk, company_name, action, url)
        
        # 2e. Notificar Slack (se quente)
        print("🔔 Passo 6: Verificando se é lead quente para Slack...")
        # Heuristica simples: se mencionar "AI", "cloud", "startup", "funding" etc.
        hot_keywords = ["ai", "artificial intelligence", "cloud", "startup", "funding", "series", "vc", "acquisition", "launch"]
        is_hot = any(kw in perplexity_analysis.lower() for kw in hot_keywords)
        
        if is_hot:
            print("  🔥 Lead quente detectado — notificando Slack...")
            notify_slack_hot_lead(sdk, company_name, perplexity_analysis, url, SLACK_CHANNEL)
        else:
            print("  → Lead não classificado como quente neste momento")
        
        if dry_run:
            print("  [DRY RUN] Ações não executadas")
        
        print()
    
    # Salvar estado
    save_state(state)
    
    print(f"{'='*60}")
    print(f"  Pipeline concluído: {len(changed_urls)} leads processados")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
