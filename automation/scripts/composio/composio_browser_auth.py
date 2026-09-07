#!/usr/bin/env python3
"""
composio_browser_auth.py — Drive Composio dashboard via browser to authenticate,
list accounts, and capture credentials.

Usage (from terminal, with valid COMPOSIO_API_KEY):
    python3 composio_browser_auth.py

This script uses the browser_exec tool via subprocess to:
  1. Navigate to app.composio.dev
  2. Attempt login (email + OAuth — may still need human for consent)
  3. Navigate to Settings > API Keys and extract the key
  4. Navigate to Integrations and list connected toolkits
  5. Capture OnePassword service account token if configured
"""

import subprocess
import sys
import json
import os

APP_DIR = "/Users/miami2/zion.app"
LOG_FILE = f"{APP_DIR}/automation/composio_browser_auth.log"


def browser(code: str, timeout: int = 30) -> dict:
    """Call browser_exec tool via Hermes CLI or direct subprocess."""
    # Try direct hermes CLI if available
    cmd = ["hermes", "browser", "exec", code]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except FileNotFoundError:
        # Fallback: use browser-use CLI directly
        cmd = ["browser-use", "run"]
        # This is a placeholder — actual integration depends on Hermes agent setup
        return {"error": "browser_exec not available as subprocess"}


def main():
    print("=" * 60)
    print("Composio Browser Auth — Zion Tech Group")
    print("=" * 60)

    # Step 1: Navigate to Composio
    print("\n[1/5] Navigating to app.composio.dev...")
    result = browser("new_tab('https://app.composio.dev'); wait_for_load(); page_info()")
    print(result)

    # Step 2: Check current state
    print("\n[2/5] Checking login state...")
    result = browser("js('document.title'); js('document.body.innerText.slice(0, 300)')")
    print(result)

    # Step 3: Attempt login with Google
    print("\n[3/5] Attempting Google OAuth login...")
    result = browser("""fill_input('input[name="email"]', 'kleber@ziontechgroup.com');
        js("document.querySelector('button[type=submit]')?.click()")""")
    print(result)

    # Step 4: Navigate to Settings
    print("\n[4/5] Navigating to Settings > API Keys...")
    result = browser("""goto_url('https://dashboard.composio.dev/settings/api-keys');
        wait_for_load();
        js('document.title');
        js('document.body.innerText.slice(0, 500)')""")
    print(result)

    # Step 5: Extract credentials
    print("\n[5/5] Extracting credentials...")
    result = browser("""js('''
        (() => {
            const keyEl = document.querySelector('[data-testid="api-key"], input[value*="ak_"]');
            const key = keyEl ? keyEl.value : null;
            const pageText = document.body.innerText;
            const hasKey = pageText.includes('ak_');
            return { hasKey, keyPreview: key ? key.slice(0, 10) + '...' : null, pageSnippet: pageText.slice(0, 300) };
        })()
    ''')""")
    print(result)


if __name__ == "__main__":
    main()
