#!/usr/bin/env python3
"""
composio_zion_setup.py - Complete Composio setup for Zion Tech Group.
Run: python3 composio_zion_setup.py
Requires: COMPOSIO_API_KEY env var set to a valid ak_... key
"""
import os, sys, json, subprocess
from datetime import datetime

API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
USER_ID = "kleber@ziontechgroup.com"
RESULTS_FILE = "/Users/miami2/zion.app/automation/composio_setup_results.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def save_result(key, value):
    results = {}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            results = json.load(f)
    results[key] = value
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

def main():
    if not API_KEY or not API_KEY.startswith("ak_"):
        log(f"ERROR: Invalid API key. Got: {API_KEY[:20]}...")
        log("Expected format: ak_... (from dashboard.composio.dev)")
        return 1
    
    log(f"API Key valid: {API_KEY[:8]}...")
    save_result("api_key_set", True)
    save_result("api_key_prefix", API_KEY[:8])
    save_result("setup_start", datetime.now().isoformat())
    
    try:
        from composio import Composio
        composio = Composio(api_key=API_KEY)
    except Exception as e:
        log(f"SDK init failed: {e}")
        return 1
    
    # 1. List connected accounts
    log("\n=== 1. CONNECTED ACCOUNTS ===")
    try:
        accounts = composio.connected_accounts.list()
        items = accounts.items if hasattr(accounts, 'items') else []
        log(f"Total: {len(items)} accounts")
        for a in items:
            toolkit = a.toolkit.slug if a.toolkit else "?"
            status = a.status
            aid = a.id
            log(f"  [{toolkit}] {status} | {aid}")
            save_result(f"account_{toolkit}", {"id": aid, "status": status})
    except Exception as e:
        log(f"  Error: {e}")
        save_result("accounts_error", str(e))
    
    # 2. List toolkits
    log("\n=== 2. AVAILABLE TOOLKITS ===")
    try:
        toolkits = composio.toolkits.list()
        items = toolkits.items if hasattr(toolkits, 'items') else []
        log(f"Total: {len(items)} toolkits")
        for t in items[:30]:
            name = t.name if hasattr(t, 'name') else '?'
            slug = t.slug if hasattr(t, 'slug') else '?'
            log(f"  {slug}: {name}")
        save_result("toolkit_count", len(items))
    except Exception as e:
        log(f"  Error: {e}")
    
    # 3. Check OnePassword specifically
    log("\n=== 3. ONEPASSWORD STATUS ===")
    try:
        op_accounts = [a for a in items if a.toolkit and a.toolkit.slug == 'one_password']
        if op_accounts:
            log(f"  OnePassword connected: {op_accounts[0].status}")
            save_result("onepassword_connected", True)
        else:
            log("  OnePassword NOT connected - needs setup")
            save_result("onepassword_connected", False)
    except Exception as e:
        log(f"  Error: {e}")
    
    # 4. Check Gmail
    log("\n=== 4. GMAIL STATUS ===")
    try:
        gm_accounts = [a for a in items if a.toolkit and a.toolkit.slug == 'gmail']
        if gm_accounts:
            log(f"  Gmail connected: {gm_accounts[0].status}")
            save_result("gmail_connected", True)
        else:
            log("  Gmail NOT connected - needs setup")
            save_result("gmail_connected", False)
    except Exception as e:
        log(f"  Error: {e}")
    
    # 5. Check GitHub
    log("\n=== 5. GITHUB STATUS ===")
    try:
        gh_accounts = [a for a in items if a.toolkit and a.toolkit.slug == 'github']
        if gh_accounts:
            log(f"  GitHub connected: {gh_accounts[0].status}")
            save_result("github_connected", True)
        else:
            log("  GitHub NOT connected - needs setup")
            save_result("github_connected", False)
    except Exception as e:
        log(f"  Error: {e}")
    
    save_result("setup_complete", datetime.now().isoformat())
    log(f"\nResults saved to: {RESULTS_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
