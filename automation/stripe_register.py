#!/usr/bin/env python3
"""Helper: open Stripe dashboard and fill registration form."""
import subprocess
import sys

code = """
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    
    # Go to Stripe register
    page.goto("https://dashboard.stripe.com/register", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    
    print("=== PAGE INFO ===")
    print("TITLE:", page.title())
    print("URL:", page.url)
    
    # Get all form fields
    inputs = page.query_selector_all("input, select, textarea")
    print(f"\\nFORM FIELDS ({len(inputs)}):")
    for i, inp in enumerate(inputs):
        name = inp.get_attribute("name") or ""
        ph = inp.get_attribute("placeholder") or ""
        typ = inp.get_attribute("type") or ""
        inp_id = inp.get_attribute("id") or ""
        print(f"  [{i}] id={inp_id} name={name} type={typ} placeholder={ph}")
    
    # Buttons
    btns = page.query_selector_all("button, input[type=submit]")
    print(f"\\nBUTTONS ({len(btns)}):")
    for i, b in enumerate(btns):
        txt = b.inner_text().strip()[:50]
        print(f"  [{i}] {txt}")
    
    browser.close()
"""

print("Executando Playwright para Stripe...")
try:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=45,
        cwd="/Users/miami2/zion.app/automation"
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    print("EXIT:", result.returncode)
except subprocess.TimeoutExpired:
    print("TIMEOUT")
except Exception as e:
    print(f"ERROR: {e}")
