#!/usr/bin/env python3
"""
composio_account_manager.py — Gerenciador de contas do Composio para Zion Tech Group.

Uso:
    export COMPOSIO_API_KEY="ak_..."
    python3 composio_account_manager.py [comando]

Comandos:
    list           — Listar todas as contas conectadas
    connect <app> — Conectar uma aplicacao (gmail, github, notion, etc.)
    refresh <id>   — Atualizar tokens de uma conta
    status         — Resumo rapido do estado atual
    setup-onepassword — Configurar OnePassword se possivel
"""

import os
import sys
from composio import Composio

API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
USER_ID = "kleber@ziontechgroup.com"

# Apps prioritarios para Zion
PRIORITY_APPS = [
    "gmail",           # Email outreach
    "github",          # Repo management
    "notion",          # Wiki / docs
    "slack",           # Communication
    "linear",          # Issue tracking
    "hubspot",         # CRM
    "calendly",        # Scheduling
    "stripe",          # Payments
    "supabase",        # Database
    "one_password",    # Credential management
]


def get_composio():
    if not API_KEY or not API_KEY.startswith("ak_"):
        print(f"ERRO: COMPOSIO_API_KEY invalida: {API_KEY[:20]}...")
        print("Esperado: ak_... (do dashboard.composio.dev)")
        sys.exit(1)
    return Composio(api_key=API_KEY)


def cmd_list(c):
    print("=" * 50)
    print("CONTAS CONECTADAS")
    print("=" * 50)
    try:
        resp = c.connected_accounts.list()
        items = resp.items if hasattr(resp, 'items') else []
        if not items:
            print("Nenhuma conta conectada.")
            return
        for a in items:
            toolkit = a.toolkit.slug if a.toolkit else "?"
            status = a.status
            aid = a.id
            user = getattr(a, 'user_id', '?')
            print(f"  [{toolkit:20s}] {status:12s} | {aid} | user={user}")
    except Exception as e:
        print(f"Erro: {e}")


def cmd_connect(c, app_slug):
    app_slug = app_slug.lower().strip()
    print(f"\nConectando: {app_slug}")
    
    # Verificar se ja existe auth config
    try:
        acs = c.auth_configs.list()
        items = acs.items if hasattr(acs, 'items') else []
    except Exception as e:
        print(f"Erro ao listar auth configs: {e}")
        return
    
    existing = [ac for ac in items if ac.toolkit and ac.toolkit.slug == app_slug]
    
    if not existing:
        print(f"  Criando auth config para {app_slug}...")
        try:
            ac = c.auth_configs.create(
                toolkit={"slug": app_slug},
                auth_config={
                    "name": f"zion-{app_slug}",
                    "type": "use_composio_managed_auth",
                    "authScheme": "OAUTH2",
                },
            )
            ac_id = ac.id
            print(f"  Auth config criado: {ac_id}")
        except Exception as e:
            print(f"  Erro ao criar: {e}")
            return
    else:
        ac_id = existing[0].id
        print(f"  Auth config existente: {ac_id}")
    
    # Criar connected account (oferece URL de OAuth)
    print(f"  Gerando link de conexao...")
    try:
        conn = c.connected_accounts.link(
            user_id=USER_ID,
            auth_config_id=ac_id,
        )
        redirect_url = getattr(conn, "redirect_url", None) or getattr(conn, "redirectUrl", None)
        
        if redirect_url:
            print(f"\n  🔗 ABRA ESTE URL NO NAVEGADOR:")
            print(f"\n      {redirect_url}\n")
            print(f"  Autorizando {app_slug} para {USER_ID}...")
            print(f"  Aguarde a pagina redirecionar para o dashboard.")
            print(f"\n  Alternativa: use 'composio connected-accounts link {app_slug}'")
        else:
            status = getattr(conn, 'status', 'unknown')
            print(f"  Status: {status}")
            if status == "ACTIVE":
                print(f"  Ja autorizado!")
    except Exception as e:
        print(f"  Erro: {e}")


def cmd_refresh(c, account_id):
    print(f"Atualizando tokens: {account_id}")
    try:
        result = c.connected_accounts.refresh(account_id)
        print(f"  Sucesso: {result}")
    except Exception as e:
        print(f"  Erro: {e}")


def cmd_status(c):
    print("=" * 50)
    print("ESTADO DO COMPOSIO — Zion Tech Group")
    print("=" * 50)
    print(f"API Key: {API_KEY[:8]}..." if API_KEY else "API Key: NAO DEFINIDA")
    print(f"User ID: {USER_ID}")
    print()
    
    try:
        resp = c.connected_accounts.list()
        items = resp.items if hasattr(resp, 'items') else []
        
        connected = [a for a in items if a.status == "ACTIVE"]
        initializing = [a for a in items if a.status == "INITIALIZING"]
        expired = [a for a in items if a.status == "EXPIRED"]
        
        print(f"Contas ATIVAS:     {len(connected)}")
        print(f"Contas PENDING:    {len(initializing)}")
        print(f"Contas EXPIRADAS:  {len(expired)}")
        print(f"Total:             {len(items)}")
        print()
        
        if connected:
            print("=== ATIVAS ===")
            for a in connected:
                t = a.toolkit.slug if a.toolkit else "?"
                print(f"  ✓ {t}")
        
        if initializing:
            print("=== PENDENTES (precisa autorizar) ===")
            for a in initializing:
                t = a.toolkit.slug if a.toolkit else "?"
                print(f"  ○ {t} — usar: composio connected-accounts link {t}")
        
        if expired:
            print("=== EXPIRADAS ===")
            for a in expired:
                t = a.toolkit.slug if a.toolkit else "?"
                print(f"  ✗ {t} — reconectar")
    except Exception as e:
        print(f"Erro: {e}")


def cmd_setup_onepassword(c):
    print("=" * 50)
    print("ONEPASSWORD — Verificando integração")
    print("=" * 50)
    
    try:
        resp = c.connected_accounts.list()
        items = resp.items if hasattr(resp, 'items') else []
    except Exception as e:
        print(f"Erro: {e}")
        return
    
    op_accounts = [a for a in items if a.toolkit and a.toolkit.slug == 'one_password']
    
    if op_accounts:
        for a in op_accounts:
            print(f"OnePassword: {a.status} | {a.id}")
            if a.status == "ACTIVE":
                print("  ✓ Já conectado e ativo")
            elif a.status == "INITIALIZING":
                print("  ○ Pendente de autorização")
                # Tentar gerar novo link
                try:
                    conn = c.connected_accounts.link(
                        user_id=USER_ID,
                        auth_config_id=a.auth_config.id if hasattr(a, 'auth_config') else None,
                    )
                    url = getattr(conn, "redirect_url", None) or getattr(conn, "redirectUrl", None)
                    if url:
                        print(f"  Novo URL: {url}")
                except Exception as e2:
                    print(f"  Erro ao gerar link: {e2}")
    else:
        print("OnePassword não conectado.")
        print("Para conectar:")
        print("  1. Acesse: https://dashboard.composio.dev/integrations")
        print("  2. Busque por '1Password'")
        print("  3. Clique em Connect")
        print("  4. Configure com OP_SERVICE_ACCOUNT_TOKEN e OP_CONNECT_HOST")
        print()
        print("Ou via CLI:")
        print("  composio connected-accounts link one_password")


def main():
    if not API_KEY:
        print("ERRO: COMPOSIO_API_KEY nao definida")
        print("  export COMPOSIO_API_KEY='ak_...'")
        sys.exit(1)
    
    c = get_composio()
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "list":
        cmd_list(c)
    elif cmd == "connect" and len(sys.argv) > 2:
        cmd_connect(c, sys.argv[2])
    elif cmd == "refresh" and len(sys.argv) > 2:
        cmd_refresh(c, sys.argv[2])
    elif cmd == "status":
        cmd_status(c)
    elif cmd == "setup-onepassword":
        cmd_setup_onepassword(c)
    elif cmd == "help" or cmd == "--help":
        print(__doc__)
    else:
        print(f"Comando desconhecido: {cmd}")
        print("Use: python3 composio_account_manager.py help")
        sys.exit(1)


if __name__ == "__main__":
    main()
