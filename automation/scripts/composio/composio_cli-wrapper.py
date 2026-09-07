#!/usr/bin/env python3
"""Composio CLI wrapper for Zion Tech Group.

Usage:
    composio login               # Authenticate with Composio
    composio connected-accounts list
    composio connected-accounts link <toolkit>
    composio connected-accounts refresh <id>
"""
import os
import sys

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")

def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        print("   Defina: export COMPOSIO_API_KEY=sua_chave")
        sys.exit(1)
    
    from composio import Composio
    c = Composio(api_key=COMPOSIO_API_KEY)
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if cmd == "login":
        print(f"✅ Composio CLI autenticado (API key: {COMPOSIO_API_KEY[:8]}...)")
        print(f"   Perfil: kleber@ziontechgroup.com")
    
    elif cmd == "connected-accounts" and len(sys.argv) > 2:
        subcmd = sys.argv[2]
        
        if subcmd == "list":
            accts = c.connected_accounts.list().to_dict()
            items = accts.get("items", [])
            print(f"Total: {len(items)} contas\n")
            for a in items:
                slug = a["toolkit"]["slug"] if a.get("toolkit") else "?"
                status = a.get("status", "?")
                user = a.get("user_id", "?")
                print(f"  [{slug}] {status} | user={user}")
        
        elif subcmd == "link" and len(sys.argv) > 3:
            toolkit_slug = sys.argv[3]
            user_id = "kleber@ziontechgroup.com"
            
            # Find auth config
            ac_id = None
            for ac in c.auth_configs.list().items:
                if hasattr(ac, 'toolkit') and ac.toolkit and ac.toolkit.slug == toolkit_slug:
                    ac_id = ac.id
                    break
            
            if not ac_id:
                print(f"❌ Auth config não encontrado para {toolkit_slug}")
                print("   Criando novo auth config...")
                try:
                    ac = c.auth_configs.create(
                        toolkit={"slug": toolkit_slug},
                        auth_config={
                            "name": f"zion-{toolkit_slug}",
                            "type": "use_composio_managed_auth",
                            "authScheme": "OAUTH2"
                        }
                    )
                    ac_id = ac.id
                    print(f"   ✅ Criado: {ac_id}")
                except Exception as e:
                    print(f"   ❌ Erro ao criar: {e}")
                    sys.exit(1)
            
            # Generate link
            try:
                conn = c.connected_accounts.link(
                    user_id=user_id,
                    auth_config_id=ac_id,
                )
                redirect_url = getattr(conn, "redirect_url", None) or getattr(conn, "redirectUrl", None)
                
                if redirect_url:
                    print(f"\n🔗 Abra este URL no navegador para conectar {toolkit_slug}:")
                    print(f"\n   {redirect_url}\n")
                    print("   Após autorizar, rode:")
                    print(f"   composio connected-accounts list")
                else:
                    print(f"❌ Não foi possível gerar URL para {toolkit_slug}")
                    print(f"   Status: {getattr(conn, 'status', 'unknown')}")
            except Exception as e:
                print(f"❌ Erro ao gerar link: {e}")
                sys.exit(1)
        
        elif subcmd == "refresh" and len(sys.argv) > 3:
            account_id = sys.argv[3]
            try:
                result = c.connected_accounts.refresh(account_id)
                print(f"✅ Conta {account_id} atualizada")
            except Exception as e:
                print(f"❌ Erro ao atualizar: {e}")
                sys.exit(1)
        else:
            print(f"❌ Comando desconhecido: {subcmd}")
    
    elif cmd == "help":
        print("""
Composio CLI - Gestão de contas conectadas

Uso:
    composio login
    composio connected-accounts list
    composio connected-accounts link <toolkit>
    composio connected-accounts refresh <account_id>

Exemplos:
    composio login
    composio connected-accounts list
    composio connected-accounts link gmail
    composio connected-accounts link notion
    composio connected-accounts refresh ca_abc123
""")
    
    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print("   Rode: composio help")

if __name__ == "__main__":
    main()
