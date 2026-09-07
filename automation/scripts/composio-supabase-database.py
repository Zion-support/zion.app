#!/usr/bin/env python3
"""
composio-supabase-database.py
=============================
Supabase Database Agent — gerencia banco de dados, storage, e auth do Zion.

 Fluxos:
   - Executar queries SQL
   - Criar/ler/atualizar registros
   - Gerenciar Storage (uploads, downloads)
   - Gerenciar Auth (criar usuários, verificar)
   - Gerar relatórios analytics

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export SUPABASE_URL="https://xxx.supabase.co"
   export SUPABASE_ANON_KEY="..."
   
   python composio-supabase-database.py query "SELECT * FROM leads LIMIT 10"
   python composio-supabase-database.py insert leads "Empresa X" "email@x.com"
   python composio-supabase-database.py storage list
   python composio-supabase-database.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
TABLE = sys.argv[2] if len(sys.argv) > 2 else None
QUERY = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None

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

# ========== DATABASE FUNCTIONS ==========

def execute_query(sql):
    """Executa query SQL no Supabase."""
    print(f"   🔍 Executando query: {sql[:100]}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SUPABASE_EXECUTE_QUERY",
        arguments={
            "url": SUPABASE_URL,
            "anonym_key": SUPABASE_ANON_KEY,
            "query": sql,
        },
        user_id="zion-bot",
    )
    
    if result:
        data = result.get("data", result.get("rows", []))
        print(f"   ✅ {len(data)} registros retornados")
        for row in data[:5]:
            print(f"     {row}")
        return data
    print(f"   ⚠️  Falha ao executar query")
    return None

def insert_record(table, data):
    """Insere registro na tabela."""
    print(f"   📝 Inserindo registro em {table}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SUPABASE_INSERT_RECORD",
        arguments={
            "url": SUPABASE_URL,
            "anonym_key": SUPABASE_ANON_KEY,
            "table": table,
            "data": data,
        },
        user_id="zion-bot",
    )
    
    if result:
        record_id = result.get("id", result.get("recordId", ""))
        print(f"   ✅ Registro inserido: {record_id}")
        return record_id
    print(f"   ⚠️  Falha ao inserir")
    return None

def list_storage():
    """Lista arquivos no Storage."""
    print(f"   📦 Listando arquivos no Storage...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SUPABASE_STORAGE_LIST",
        arguments={
            "url": SUPABASE_URL,
            "anonym_key": SUPABASE_ANON_KEY,
        },
        user_id="zion-bot",
    )
    
    files = result.get("files", []) if isinstance(result, dict) else []
    print(f"   ✅ {len(files)} arquivos encontrados")
    for f in files[:10]:
        print(f"     {f}")
    return files

def create_user(email, password):
    """Cria usuário no Supabase Auth."""
    print(f"   🔐 Criando usuário: {email}...")
    
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SUPABASE_CREATE_USER",
        arguments={
            "url": SUPABASE_URL,
            "anonym_key": SUPABASE_ANON_KEY,
            "email": email,
            "password": password,
        },
        user_id="zion-bot",
    )
    
    if result:
        user_id = result.get("id", result.get("userId", ""))
        print(f"   ✅ Usuário criado: {user_id}")
        return user_id
    print(f"   ⚠️  Falha ao criar usuário")
    return None

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL não configurada")
        print("Exemplo: export SUPABASE_URL='https://xxx.supabase.co'")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Supabase Database Agent — Uso:

  python composio-supabase-database.py query "SELECT * FROM leads"
      Executa query SQL

  python composio-supabase-database.py insert leads "Empresa" "email@x.com"
      Insere registro na tabela

  python composio-supabase-database.py storage list
      Lista arquivos no Storage

  python composio-supabase-database.py auth create email password
      Cria usuário no Auth

  python composio-supabase-database.py --dry-run
      Testa configuração sem executar

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export SUPABASE_URL='https://zion.supabase.co'
  export SUPABASE_ANON_KEY='...'
  python composio-supabase-database.py query "SELECT count(*) FROM leads"
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não executando")
        if ACTION in ["query", "insert"]:
            print(f"   Tabela: {TABLE}")
            print(f"   Query/Dados: {QUERY}")
        return
    
    if ACTION == "query":
        if not QUERY:
            print("❌ Query necessária")
            print("Uso: python composio-supabase-database.py query \"SELECT ...\"")
            sys.exit(1)
        execute_query(QUERY)
    
    elif ACTION == "insert":
        if not TABLE:
            print("❌ Tabela necessária")
            print("Uso: python composio-supabase-database.py insert <table> <dados>")
            sys.exit(1)
        # Parse data from args
        data = {}
        parts = QUERY.split() if QUERY else []
        # Simple: first is company, second is email
        if len(parts) >= 2:
            data = {"Empresa": parts[0], "Email": parts[1], "Data": datetime.now().isoformat()}
        elif len(parts) == 1:
            data = {"Nome": parts[0], "Data": datetime.now().isoformat()}
        insert_record(TABLE, data)
    
    elif ACTION == "storage":
        if "list" in sys.argv:
            list_storage()
        else:
            print("❌ Subcomando desconhecido para storage")
            print("Uso: python composio-supabase-database.py storage list")
            sys.exit(1)
    
    elif ACTION == "auth":
        if "create" in sys.argv and len(sys.argv) > 3:
            email = sys.argv[2] if sys.argv.index("create") + 1 < len(sys.argv) else None
            password = sys.argv[3] if sys.argv.index("create") + 2 < len(sys.argv) else None
            if email and password:
                create_user(email, password)
            else:
                print("❌ Email e password necessários")
                sys.exit(1)
        else:
            print("❌ Subcomando desconhecido para auth")
            print("Uso: python composio-supabase-database.py auth create email password")
            sys.exit(1)
    
    else:
        print(f"❌ Ação desconhecida: {ACTION}")
        sys.exit(1)

if __name__ == "__main__":
    main()
