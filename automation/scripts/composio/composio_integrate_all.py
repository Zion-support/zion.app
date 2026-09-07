#!/usr/bin/env python3
"""
composio_integrate_all.py — Conecta todas as aplicacoes prioritarias do Zion Tech Group
no Composio de uma vez so.

Uso:
    export COMPOSIO_API_KEY="ak_..."
    python3 composio_integrate_all.py

Fluxo:
    1. Lista contas existentes
    2. Para cada app prioritario nao conectado:
       - Cria auth config se necessario
       - Gera URL de OAuth
       - Informa ao usuario para autorizar
    3. Após autorizacoes, lista contas ativas
"""

import os
import sys
import time
from composio import Composio

API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
USER_ID = "kleber@ziontechgroup.com"

# Apps em ordem de prioridade para Zion
APPS = [
    ("gmail",       "Email outreach e triage"),
    ("github",      "Repositorios e issues"),
    ("notion",      "Wiki e documentacao"),
    ("linear",      "Issue tracking"),
    ("slack",       "Comunicacao"),
    ("hubspot",     "CRM"),
    ("google_calendar", "Agendamento"),
    ("google_drive", "Arquivos"),
    ("stripe",      "Pagamentos"),
    ("calendly",    "Agendamento de reuniões"),
    ("linkedin",    "Rede social profissional"),
    ("supabase",    "Banco de dados"),
    ("discord",     "Comunidade"),
    ("airtable",    "Planilhas avancadas"),
    ("notion",      "Database"),
]

# Apps que usam API key em vez de OAuth
API_KEY_APPS = {
    "resend": "API key do Resend (email infra)",
    "brevo":  "API key do Brevo (email marketing)",
    "serpapi":"API key do SerpApi (busca Google)",
    "tavily": "API key do Tavily (busca AI)",
    "firecrawl": "API key do Firecrawl (web scraping)",
    "one_password": "OP_SERVICE_ACCOUNT_TOKEN + OP_CONNECT_HOST",
}


def log(msg):
    print(f"\033[94m[{time.strftime('%H:%M:%S')}]\033[0m {msg}")


def main():
    if not API_KEY or not API_KEY.startswith("ak_"):
        print("ERRO: COMPOSIO_API_KEY invalida ou nao definida")
        print("  export COMPOSIO_API_KEY='ak_...'")
        sys.exit(1)

    log(f"Iniciando integracao Composio para Zion Tech Group")
    log(f"API Key: {API_KEY[:8]}...")
    log(f"User ID: {USER_ID}")
    log(f"Aplicacoes alvo: {len(APPS)} OAuth + {len(API_KEY_APPS)} API key")
    log("-" * 50)

    c = Composio(api_key=API_KEY)

    # 1. Estado atual
    log("\n[1/4] Verificando estado atual...")
    try:
        resp = c.connected_accounts.list()
        existing = resp.items if hasattr(resp, 'items') else []
    except Exception as e:
        log(f"Erro ao listar: {e}")
        existing = []

    connected_slugs = set()
    for a in existing:
        if a.toolkit and a.toolkit.slug:
            slug = a.toolkit.slug
            status = a.status
            connected_slugs.add(slug)
            icon = "✓" if status == "ACTIVE" else ("○" if status == "INITIALIZING" else "✗")
            log(f"  {icon} {slug:25s} {status}")

    # 2. Apps OAuth que precisam de conexao
    log(f"\n[2/4] Conectando aplicacoes OAuth ({len(APPS)} apps)...")
    log("-" * 50)

    urls_to_authorize = []

    for slug, description in APPS:
        if slug in connected_slugs:
            # Verificar status
            account = next((a for a in existing if a.toolkit and a.toolkit.slug == slug), None)
            if account and account.status == "ACTIVE":
                log(f"  ✓ {slug:25s} — ja ativo")
            else:
                log(f"  ○ {slug:25s} — status: {account.status if account else 'N/A'} — reconectar")
                slug_to_connect = slug
                _connect_app(c, slug, description, urls_to_authorize)
        else:
            log(f"  ○ {slug:25s} — nao conectado")
            _connect_app(c, slug, description, urls_to_authorize)

    # 3. Apps API key
    log(f"\n[3/4] Aplicacoes API key ({len(API_KEY_APPS)} apps)...")
    log("-" * 50)
    for slug, info in API_KEY_APPS.items():
        log(f"  ℹ {slug:25s} — {info}")
        log(f"     Configure manualmente no dashboard ou passe variavel de ambiente")

    # 4. Resumo
    log(f"\n[4/4] Resumo e proximos passos...")
    log("-" * 50)
    
    pending = [u for u in urls_to_authorize if u]
    if pending:
        log(f"\n  {len(pending)} URL(s) de autorizacao gerada(s)")
        log("\n  PROXIMOS PASSOS:")
        log("  1. Abra cada URL no navegador e autorize")
        log("  2. Após autorizar, rode:")
        log("     python3 composio_integrate_all.py  (para verificar)")
        log("  3. Ou use CLI:")
        log("     composio connected-accounts list")
    else:
        log("\n  Todas as contas OAuth ja estao ativas ou sem acesso a API key valida")
    
    log(f"\n  Apps API key ainda precisam de configuração manual:")
    for slug, _ in API_KEY_APPS.items():
        log(f"    - {slug}")
    
    log("\n  OnePassword:")
    log("    - Precisa de OP_SERVICE_ACCOUNT_TOKEN + OP_CONNECT_HOST")
    log("    - Crie no: https://1password.com/downloads/connect")
    log("    - Configure no dashboard Composio > Integrations > 1Password")


def _connect_app(c, slug, description, urls_list):
    """Cria auth config e gera URL de OAuth para um app."""
    try:
        # Verificar auth config existente
        acs = c.auth_configs.list()
        ac_items = acs.items if hasattr(acs, 'items') else []
        existing_ac = [ac for ac in ac_items if ac.toolkit and ac.toolkit.slug == slug]
        
        if existing_ac:
            ac_id = existing_ac[0].id
        else:
            # Criar auth config
            ac = c.auth_configs.create(
                toolkit={"slug": slug},
                auth_config={
                    "name": f"zion-{slug}",
                    "type": "use_composio_managed_auth",
                    "authScheme": "OAUTH2",
                },
            )
            ac_id = ac.id
            log(f"    Auth config criado: {ac_id}")
        
        # Criar connected account
        conn = c.connected_accounts.link(
            user_id=USER_ID,
            auth_config_id=ac_id,
        )
        redirect_url = getattr(conn, "redirect_url", None) or getattr(conn, "redirectUrl", None)
        
        if redirect_url:
            urls_list.append((slug, redirect_url))
            log(f"    {slug}: URL gerada (autorize no navegador)")
        else:
            status = getattr(conn, 'status', 'unknown')
            log(f"    {slug}: status={status}")
            
    except Exception as e:
        log(f"    {slug}: ERRO — {e}")


if __name__ == "__main__":
    main()
