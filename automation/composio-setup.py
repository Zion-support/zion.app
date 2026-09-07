#!/usr/bin/env python3
"""
composio-setup.py - One-time setup for Zion Tech Group Composio integration.
Run this after COMPOSIO_API_KEY is set in the environment.
"""
import os, sys, json
from composio import Composio

def main():
    api_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not api_key or not api_key.startswith("ak_"):
        print("ERROR: COMPOSIO_API_KEY not set or invalid format")
        print("Expected: ak_... (from dashboard.composio.dev)")
        return 1
    
    print(f"Using API key: {api_key[:8]}...")
    composio = Composio(api_key=api_key)
    
    # 1. List connected accounts
    print("\n=== CONNECTED ACCOUNTS ===")
    try:
        accounts = composio.connected_accounts.list()
        if hasattr(accounts, 'items'):
            for a in accounts.items:
                toolkit = a.toolkit.slug if a.toolkit else "unknown"
                status = a.status
                print(f"  [{toolkit}] {status} | {a.id}")
        else:
            print(f"  {accounts}")
    except Exception as e:
        print(f"  Error listing accounts: {e}")
    
    # 2. List available toolkits
    print("\n=== AVAILABLE TOOLKITS (first 20) ===")
    try:
        toolkits = composio.toolkits.list()
        if hasattr(toolkits, 'items'):
            for i, t in enumerate(toolkits.items[:20]):
                name = t.name if hasattr(t, 'name') else 'N/A'
                slug = t.slug if hasattr(t, 'slug') else 'N/A'
                print(f"  {i+1}. {slug}: {name}")
        else:
            print(f"  {toolkits}")
    except Exception as e:
        print(f"  Error listing toolkits: {e}")
    
    # 3. Create OnePassword auth config if needed
    print("\n=== ONEPASSWORD SETUP ===")
    try:
        existing = composio.auth_configs.list()
        if hasattr(existing, 'items'):
            op_configs = [a for a in existing.items if hasattr(a, 'toolkit') and a.toolkit and a.toolkit.slug == 'one_password']
            if op_configs:
                print(f"  OnePassword auth config exists: {op_configs[0].id}")
            else:
                print("  No OnePassword auth config found - needs manual setup")
        else:
            print(f"  {existing}")
    except Exception as e:
        print(f"  Error checking auth configs: {e}")
    
    # 4. Save results
    results = {"api_key_set": bool(api_key), "timestamp": __import__('datetime').datetime.now().isoformat()}
    with open("/Users/miami2/zion.app/automation/composio_setup_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to composio-setup-results.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
