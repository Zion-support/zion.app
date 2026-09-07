#!/usr/bin/env python3
"""
onepassword_composio_setup.py — Prepara a integracao OnePassword + Composio.

Fluxo:
    1. Verifica se tem conta 1Password acessivel
    2. Cria service account token se necessario (instrucoes)
    3. Configura no Composio via SDK ou instrucoes para dashboard
    4. Testa a conexao

Uso:
    export COMPOSIO_API_KEY="ak_..."
    export OP_SERVICE_ACCOUNT_TOKEN="..."
    export OP_CONNECT_HOST="vault.1password.com"  (opcional)
    python3 onepassword_composio_setup.py
"""

import os
import sys
from composio import Composio

API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
OP_TOKEN = os.environ.get("OP_SERVICE_ACCOUNT_TOKEN", "")
OP_HOST = os.environ.get("OP_CONNECT_HOST", "vault.1password.com")
USER_ID = "kleber@ziontechgroup.com"


def main():
    print("=" * 60)
    print("OnePassword + Composio — Setup para Zion Tech Group")
    print("=" * 60)

    # 1. Verificar Composio
    if not API_KEY or not API_KEY.startswith("ak_"):
        print("\nERROR: COMPOSIO_API_KEY invalida")
        print("  export COMPOSIO_API_KEY='ak_...'")
        print("\nObtenha a key em:")
        print("  https://dashboard.composio.dev/settings/api-keys")
        sys.exit(1)

    print(f"\n✓ Composio API Key: {API_KEY[:8]}...")

    # 2. Verificar 1Password
    print("\n--- 1Password Service Account ---")
    if OP_TOKEN:
        print(f"✓ OP_SERVICE_ACCOUNT_TOKEN: {OP_TOKEN[:8]}...")
    else:
        print("✗ OP_SERVICE_ACCOUNT_TOKEN nao definida")
        print("\nCrie uma service account no 1Password:")
        print("  1. Acesse: https://1password.com/downloads/connect")
        print("     OU use o app 1Password > Settings > Service Accounts")
        print("  2. Crie uma nova service account")
        print("  3. Copie o token (aparece apenas uma vez!)")
        print("  4. Export: export OP_SERVICE_ACCOUNT_TOKEN='...'")
        print()
        print("Ou configure no dashboard Composio:")
        print("  https://dashboard.composio.dev/integrations")
        print("  Busque por '1Password' e conecte")

    print(f"\n  OP_CONNECT_HOST: {OP_HOST}")

    # 3. Tentar conectar via SDK
    print("\n--- Tentando conectar via SDK ---")
    try:
        c = Composio(api_key=API_KEY)
        
        # Verificar se ja existe auth config para one_password
        acs = c.auth_configs.list()
        ac_items = acs.items if hasattr(acs, 'items') else []
        existing = [ac for ac in ac_items if ac.toolkit and ac.toolkit.slug == 'one_password']
        
        if existing:
            ac_id = existing[0].id
            print(f"  Auth config existente: {ac_id}")
        else:
            print("  Criando auth config para one_password...")
            ac = c.auth_configs.create(
                toolkit={"slug": "one_password"},
                auth_config={
                    "name": "zion-onepassword",
                    "type": "use_composio_managed_auth",
                    "authScheme": "OAUTH2",
                },
            )
            ac_id = ac.id
            print(f"  Auth config criado: {ac_id}")
        
        # Criar connected account
        print("  Criando connected account...")
        conn = c.connected_accounts.link(
            user_id=USER_ID,
            auth_config_id=ac_id,
        )
        redirect_url = getattr(conn, "redirect_url", None) or getattr(conn, "redirectUrl", None)
        
        if redirect_url:
            print(f"\n  🔗 URL de autorizacao:")
            print(f"     {redirect_url}")
            print(f"\n  Abra no navegador e autorize o 1Password")
        else:
            status = getattr(conn, 'status', 'unknown')
            print(f"  Status: {status}")
            if status == "ACTIVE":
                print("  ✓ OnePassword conectado com sucesso!")
        
    except Exception as e:
        print(f"  Erro: {e}")
        print("\n  Alternativa: configure manualmente no dashboard")
        print("  https://dashboard.composio.dev/integrations")

    # 4. Testar se possible com credenciais
    print("\n--- Testando acesso (se token disponivel) ---")
    if OP_TOKEN:
        try:
            import subprocess
            env = os.environ.copy()
            env['OP_SERVICE_ACCOUNT_TOKEN'] = OP_TOKEN
            env['OP_CONNECT_HOST'] = OP_HOST
            
            # Testar com op CLI se disponivel
            result = subprocess.run(
                ['op', 'account', 'list'],
                capture_output=True, text=True, timeout=10,
                env=env
            )
            if result.returncode == 0:
                print("  ✓ 1Password CLI funcional")
                print(f"  Contas: {result.stdout.strip()[:200]}")
            else:
                print(f"  ✗ 1Password CLI erro: {result.stderr[:200]}")
        except FileNotFoundError:
            print("  ⚠ 1Password CLI (op) nao instalado")
            print("  Instale: https://1password.com/downloads/command-line")
        except Exception as e:
            print(f"  ✗ Erro: {e}")
    else:
        print("  (sem token — configure OP_SERVICE_ACCOUNT_TOKEN)")


if __name__ == "__main__":
    main()
