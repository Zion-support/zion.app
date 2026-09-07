#!/usr/bin/env python3
"""
composio-cloudflare-agent.py
============================
Cloudflare Agent — gerencia DNS, WAF, CDN, e segurança do Zion.

 Fluxos:
   - Listar/registrar DNS records
   - Verificar status do WAF
   - Gerenciar CDN/cache
   - Monitorar performance
   - Crear alertas de segurança

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export CLOUDFLARE_API_TOKEN="..."
   export CLOUDFLARE_ACCOUNT_ID="..."
   
   python composio-cloudflare-agent.py dns list
   python composio-cloudflare-agent.py dns add example.com A 1.2.3.4
   python composio-cloudflare-agent.py waf status
   python composio-cloudflare-agent.py cache purge
   python composio-cloudflare-agent.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
DOMAIN = sys.argv[2] if len(sys.argv) > 2 else None
RECORD_TYPE = sys.argv[3] if len(sys.argv) > 3 else None
RECORD_VALUE = sys.argv[4] if len(sys.argv) > 4 else None

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

# ========== DNS FUNCTIONS ==========

def list_dns_records(domain):
    """Lista DNS records do domínio."""
    print(f"   🌐 Listando DNS records para {domain}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "CLOUDFLARE_LIST_DNS_RECORDS",
        arguments={
            "account_id": CLOUDFLARE_ACCOUNT_ID,
            "zone": domain,
        },
        user_id="zion-bot",
    )
    
    records = result.get("records", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(records)} records encontrados")
    
    for record in records:
        rtype = record.get("type", "?")
        name = record.get("name", "?")
        value = record.get("content", "?")
        proxied = record.get("proxied", False)
        print(f"     {rtype} {name} → {value} {'(proxied)' if proxied else ''}")
    
    return records

def add_dns_record(domain, record_type, value):
    """Adiciona DNS record."""
    print(f"   🌐 Adicionando {record_type} record para {domain} → {value}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "CLOUDFLARE_CREATE_DNS_RECORD",
        arguments={
            "account_id": CLOUDFLARE_ACCOUNT_ID,
            "zone": domain,
            "type": record_type,
            "content": value,
            "ttl": 1,
            "proxied": True,
        },
        user_id="zion-bot",
    )
    
    if result:
        record_id = result.get("id", "")
        print(f"   ✅ Record criado: {record_id}")
        return record_id
    print(f"   ⚠️  Falha ao criar record")
    return None

# ========== WAF FUNCTIONS ==========

def waf_status():
    """Verifica status do WAF."""
    print(f"   🛡️ Verificando status do WAF...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "CLOUDFLARE_GET_WAF_STATUS",
        arguments={
            "account_id": CLOUDFLARE_ACCOUNT_ID,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ WAF ativo: {result.get('status', 'N/A')}")
        print(f"      Mode: {result.get('mode', 'N/A')}")
        print(f"      Rules: {result.get('rules_count', 0)}")
        return result
    print(f"   ⚠️  Falha ao obter status")
    return None

# ========== CACHE FUNCTIONS ==========

def purge_cache(domain):
    """Limpa cache do CDN."""
    print(f"   🧹 Purgando cache para {domain}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "CLOUDFLARE_PURGE_CACHE",
        arguments={
            "account_id": CLOUDFLARE_ACCOUNT_ID,
            "zone": domain,
            "purge_everything": True,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Cache purgado")
        return True
    print(f"   ⚠️  Falha ao purgar cache")
    return None

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Cloudflare Agent — Uso:

  python composio-cloudflare-agent.py dns list example.com
      Lista DNS records do domínio

  python composio-cloudflare-agent.py dns add example.com A 1.2.3.4
      Adiciona DNS record

  python composio-cloudflare-agent.py waf status
      Verifica status do WAF

  python composio-cloudflare-agent.py cache purge example.com
      Limpa cache do CDN

  python composio-cloudflare-agent.py --dry-run
      Testa configuração sem executar

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export CLOUDFLARE_API_TOKEN='...'
  export CLOUDFLARE_ACCOUNT_ID='...'
  python composio-cloudflare-agent.py dns list ziontechgroup.com
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não executando")
        print(f"   Ação: {ACTION}")
        if DOMAIN:
            print(f"   Domínio: {DOMAIN}")
        return
    
    if ACTION == "dns":
        if "list" in sys.argv:
            if not DOMAIN:
                print("❌ Domínio necessário")
                print("Uso: python composio-cloudflare-agent.py dns list <domínio>")
                sys.exit(1)
            list_dns_records(DOMAIN)
        elif "add" in sys.argv or len(sys.argv) > 2:
            if not DOMAIN or not RECORD_TYPE or not RECORD_VALUE:
                print("❌ Domínio, tipo e valor necessários")
                print("Uso: python composio-cloudflare-agent.py dns add <domínio> <tipo> <valor>")
                sys.exit(1)
            add_dns_record(DOMAIN, RECORD_TYPE, RECORD_VALUE)
        else:
            print("❌ Subcomando desconhecido para dns")
            print("Uso: python composio-cloudflare-agent.py dns list|add <domínio> [tipo] [valor]")
            sys.exit(1)
    
    elif ACTION == "waf":
        if "status" in sys.argv:
            waf_status()
        else:
            print("❌ Subcomando desconhecido para waf")
            print("Uso: python composio-cloudflare-agent.py waf status")
            sys.exit(1)
    
    elif ACTION == "cache":
        if "purge" in sys.argv:
            if not DOMAIN:
                print("❌ Domínio necessário")
                print("Uso: python composio-cloudflare-agent.py cache purge <domínio>")
                sys.exit(1)
            purge_cache(DOMAIN)
        else:
            print("❌ Subcomando desconhecido para cache")
            print("Uso: python composio-cloudflare-agent.py cache purge <domínio>")
            sys.exit(1)
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
