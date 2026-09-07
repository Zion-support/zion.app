#!/usr/bin/env python3
"""
composio-browser-agent.py
==========================
Browser Tool Agent — automação avançada de navegação e scraping para Zion.

 Fluxos:
   - Navegar e extrair dados de sites (concorrentes, marketplaces, etc.)
   - Scraper com JavaScript rendering (sites SPA, React, Vue, etc.)
   - Interagir com elementos (clicar, scroll, preencher formulários)
   - Capturar screenshots para evidence
   - Extrair dados estruturados (preços, produtos, artigos)
   - Retry automático com navegação inteligente

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#browser"
   
   python composio-browser-agent.py scrape "https://concorrente.com/produtos" --extract prices
   python composio-browser-agent.py navigate "https://site.com/login" --fill username=email password=senha
   python composio-browser-agent.py screenshot "https://site.com/page"
   python composio-browser-agent.py search "AI automation enterprise Brazil"
   python composio-browser-agent.py --dry-run
"""

import os
import sys
import json
import time
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#browser")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
TARGET = sys.argv[2] if len(sys.argv) > 2 else None

# Parser para flags
PARAMS = {}
i = 3
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg.startswith("--") and "=" in arg:
        key, val = arg[2:].split("=", 1)
        PARAMS[key] = val
    elif arg.startswith("--") and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
        PARAMS[arg[2:]] = sys.argv[i + 1]
        i += 1
    else:
        PARAMS[arg[2:]] = True
    i += 1

EXTRACT_TYPE = PARAMS.get("extract", None)
FILL_DATA = {}
for k, v in PARAMS.items():
    if k in ["username", "password", "email", "nome", "empresa", "telefone"]:
        FILL_DATA[k] = v
    elif k not in ["dry_run", "limit", "extract", "help"]:
        pass  # outros parâmetros

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
    return tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )

# ========== BROWSER FUNCTIONS ==========

def scrape_url(url, extract_type=None):
    """Scrape URL com Browser Tool e extrai dados."""
    print(f"   🌐 Scrapeando: {url}")
    
    sdk = get_sdk()
    
    # 1. Navigate para a URL
    print(f"   🔗 Navegando para {url}...")
    result = tool_execute(
        sdk,
        "BROWSER_NAVIGATE",
        arguments={"url": url},
        user_id="zion-bot",
    )
    
    if not result:
        print(f"   ⚠️  Falha ao navegar")
        return None
    
    # 2. Aguardar carregamento
    print(f"   ⏳ Aguardando carregamento...")
    time.sleep(3)
    
    # 3. Extrair conteúdo base
    print(f"   📄 Extraindo conteúdo...")
    content_result = tool_execute(
        sdk,
        "BROWSER_GET_PAGE_CONTENT",
        arguments={},
        user_id="zion-bot",
    )
    
    page_content = content_result.get("content", "") if content_result else ""
    
    # 4. Extração específica pelo tipo
    extracted = {}
    
    if extract_type == "prices":
        print(f"   💰 Extraindo preços...")
        extracted["prices"] = extract_prices(page_content)
    
    elif extract_type == "products":
        print(f"   📦 Extraindo produtos...")
        extracted["products"] = extract_products(page_content)
    
    elif extract_type == "articles":
        print(f"   📝 Extraindo artigos...")
        extracted["articles"] = extract_articles(page_content)
    
    elif extract_type == "links":
        print(f"   🔗 Extraindo links...")
        extracted["links"] = extract_links(page_content)
    
    elif extract_type == "all":
        print(f"   🔍 Extraindo tudo...")
        extracted["prices"] = extract_prices(page_content)
        extracted["products"] = extract_products(page_content)
        extracted["links"] = extract_links(page_content)
    
    # 5. Screenshot opcional
    screenshot_result = tool_execute(
        sdk,
        "BROWSER_SCREENSHOT",
        arguments={},
        user_id="zion-bot",
    )
    
    screenshot_url = screenshot_result.get("url", "") if screenshot_result else ""
    
    # 6. Slack notification
    summary = f"*🌐 Browser Agent — Scraping — {datetime.now().strftime('%H:%M')}*\n\n"
    summary += f"**URL:** {url}\n"
    summary += f"**Tipo:** {extract_type or 'conteúdo completo'}\n"
    
    if extracted:
        for key, value in extracted.items():
            if isinstance(value, list):
                summary += f"**{key.capitalize()}:** {len(value)} itens encontrados\n"
            else:
                summary += f"**{key.capitalize()}:** {str(value)[:100]}\n"
    
    if screenshot_url:
        summary += f"\n**Screenshot:** {screenshot_url}\n"
    
    slack_notify(summary)
    
    print(f"   ✅ Extração concluída")
    print(f"   📊 Resultados: {extracted}")
    
    return {
        "url": url,
        "content": page_content[:500] if page_content else "",
        "extracted": extracted,
        "screenshot": screenshot_url,
        "timestamp": datetime.now().isoformat(),
    }

def extract_prices(html_content):
    """Extrai preços do HTML — heurística básica."""
    import re
    # Patterns comuns de preço
    patterns = [
        r'R\$\s*\d+[.,]\d{2}',
        r'\d+[.,]\d{2}\s*R\$',
        r'USD\s*\d+[.,]\d{2}',
        r'\$\s*\d+[.,]\d{2}',
    ]
    
    prices = set()
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        prices.update(matches)
    
    return sorted(list(prices))[:20]

def extract_products(html_content):
    """Extrai produtos — heurística básica."""
    import re
    # Tenta extrair títulos de produtos (h1-h3, class="product", etc.)
    title_patterns = [
        r'<h[123][^>]*>([^<]+)</h[123]>',
        r'class="[^"]*product[^"]*"[^>]*>([^<]+)</',
        r'<a[^>]*href="[^"]*"[^>]*>([^<]{5,100})</a>',
    ]
    
    products = set()
    for pattern in title_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for m in matches:
            clean = re.sub(r'<[^>]+>', '', m).strip()
            if len(clean) > 5 and len(clean) < 150:
                products.add(clean)
    
    return sorted(list(products))[:20]

def extract_articles(html_content):
    """Extrai títulos de artigos/blog posts."""
    import re
    patterns = [
        r'<h[12][^>]*>([^<]+)</h[12]>',
        r'<title>([^<]+)</title>',
        r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
    ]
    
    articles = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for m in matches:
            clean = re.sub(r'<[^>]+>', '', m).strip()
            if clean and len(clean) > 10:
                articles.append(clean)
    
    return articles[:10]

def extract_links(html_content):
    """Extrai links do HTML."""
    import re
    pattern = r'href="([^"]+)"'
    matches = re.findall(pattern, html_content)
    
    # Filtra para links relevantes
    relevant = []
    for m in matches:
        if m.startswith("http") and len(m) > 20:
            relevant.append(m)
    
    return relevant[:20]

def navigate_and_interact(url, fill_data=None):
    """Navega, preenche formulários e interage."""
    print(f"   🔗 Navegando para: {url}")
    
    sdk = get_sdk()
    
    # 1. Navigate
    result = tool_execute(
        sdk,
        "BROWSER_NAVIGATE",
        arguments={"url": url},
        user_id="zion-bot",
    )
    
    if not result:
        print(f"   ⚠️  Falha ao navegar")
        return None
    
    # 2. Se houver dados para preencher
    if fill_data:
        print(f"   ✏️ Preenchendo formulário...")
        for field, value in fill_data.items():
            fill_result = tool_execute(
                sdk,
                "BROWSER_FILL_INPUT",
                arguments={
                    "selector": f"input[name='{field}'], input[id='{field}'], input[placeholder*='{field}']",
                    "value": value,
                },
                user_id="zion-bot",
            )
            if fill_result:
                print(f"      ✓ {field}: {value}")
    
    # 3. Screenshot pós-interação
    screenshot_result = tool_execute(
        sdk,
        "BROWSER_SCREENSHOT",
        arguments={},
        user_id="zion-bot",
    )
    
    screenshot_url = screenshot_result.get("url", "") if screenshot_result else ""
    
    print(f"   ✅ Navegação e interação concluídas")
    if screenshot_url:
        print(f"   📸 Screenshot: {screenshot_url}")
    
    return {"url": url, "screenshot": screenshot_url, "filled": fill_data}

def take_screenshot(url):
    """Tira screenshot de URL."""
    print(f"   📸 Screenshot de: {url}")
    
    sdk = get_sdk()
    
    # Navigate
    sdk.tools.execute("BROWSER_NAVIGATE", arguments={"url": url}, user_id="zion-bot")
    time.sleep(2)
    
    result = tool_execute(
        sdk,
        "BROWSER_SCREENSHOT",
        arguments={},
        user_id="zion-bot",
    )
    
    screenshot_url = result.get("url", "") if result else ""
    
    if screenshot_url:
        print(f"   ✅ Screenshot tirado: {screenshot_url}")
        slack_notify(f"*📸 Screenshot — {datetime.now().strftime('%H:%M')}*\n\n**URL:** {url}\n**Imagem:** {screenshot_url}")
    
    return screenshot_url

def search_web(query, limit=10):
    """Search na web via Browser Tool."""
    print(f"   🔍 Buscando: '{query}'")
    
    sdk = get_sdk()
    
    result = tool_execute(
        sdk,
        "BROWSER_SEARCH",
        arguments={
            "query": query,
            "limit": limit,
        },
        user_id="zion-bot",
    )
    
    results = result.get("results", []) if isinstance(result, dict) else []
    
    print(f"   ✅ {len(results)} resultados encontrados")
    
    for r in results[:5]:
        print(f"     {r.get('title', 'N/A')}")
        print(f"       {r.get('url', 'N/A')}")
        print(f"       {r.get('snippet', '')[:100]}")
    
    return results

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Browser Agent — Uso:

  python composio-browser-agent.py scrape <url> --extract prices
      Scrape URL e extrai preços

  python composio-browser-agent.py scrape <url> --extract products
      Scrape URL e extrai produtos

  python composio-browser-agent.py scrape <url> --extract articles
      Scrape URL e extrai artigos

  python composio-browser-agent.py scrape <url> --extract all
      Scrape URL e extrai tudo (preços + produtos + links)

  python composio-browser-agent.py navigate <url> --username user --password pass
      Navega, preenche formulário e interage

  python composio-browser-agent.py screenshot <url>
      Tira screenshot da URL

  python composio-browser-agent.py search "consulta"
      Busca na web via Browser Tool

  python composio-browser-agent.py --dry-run
      Testa configuração sem executar

Exemplos:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#browser'
  
  # Extrair preços de concorrente
  python composio-browser-agent.py scrape "https://concorrente.com/produtos" --extract prices
  
  # Login automatizado
  python composio-browser-agent.py navigate "https://app.concorrente.com/login" \
    --username "analista@zion.com" --password "senha123"
  
  # Screenshot de página
  python composio-browser-agent.py screenshot "https://concorrente.com/landing"
  
  # Pesquisa de mercado
  python composio-browser-agent.py search "melhores ferramentas AI automation Brasil 2026"
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não executando")
        print(f"   Ação: {ACTION}")
        if TARGET:
            print(f"   Alvo: {TARGET}")
        if EXTRACT_TYPE:
            print(f"   Extração: {EXTRACT_TYPE}")
        if FILL_DATA:
            print(f"   Dados para preencher: {list(FILL_DATA.keys())}")
        return
    
    if ACTION == "scrape":
        if not TARGET:
            print("❌ URL necessária")
            print("Uso: python composio-browser-agent.py scrape <url> --extract <tipo>")
            sys.exit(1)
        scrape_url(TARGET, EXTRACT_TYPE)
    
    elif ACTION == "navigate":
        if not TARGET:
            print("❌ URL necessária")
            print("Uso: python composio-browser-agent.py navigate <url> [--username u] [--password p]")
            sys.exit(1)
        navigate_and_interact(TARGET, FILL_DATA if FILL_DATA else None)
    
    elif ACTION == "screenshot":
        if not TARGET:
            print("❌ URL necessária")
            print("Uso: python composio-browser-agent.py screenshot <url>")
            sys.exit(1)
        take_screenshot(TARGET)
    
    elif ACTION == "search":
        if not TARGET:
            print("❌ Query necessária")
            print("Uso: python composio-browser-agent.py search <query>")
            sys.exit(1)
        search_web(TARGET)
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
