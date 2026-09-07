#!/usr/bin/env python3
"""
Zion Tech Group — Stripe Checkout CLI

Comando simples para gerar checkouts e links de pagamento para os serviços Zion.
Ideal para usar em scripts de outreach e landing pages.

Exemplo:
  python3 stripe_checkout.py checkout cli@ziontechgroup.com starter
  python3 stripe_checkout.py link growth
  python3 stripe_checkout.py setup
"""

import os
import sys
import json
import subprocess
import importlib
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

ZION_ROOT = Path("/Users/miami2/zion.app")
AUTOMATION_DIR = ZION_ROOT / "automation"
STRIPE_BILLING_PATH = AUTOMATION_DIR / "stripe_billing.py"
STATE_DIR = AUTOMATION_DIR / "stripe-state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ── Plan definitions ──────────────────────────────────────────────────────────

ZION_PLANS = {
    "starter": {
        "name": "Zion Tech Group — Starter Tier",
        "amount": 250000,  # $2,500.00 em centavos
        "currency": "usd",
        "interval": "month",
        "description": "AI & IT services starter package — $2,500/month",
        "success_url": "https://ziontechgroup.com/success?plan=starter",
        "cancel_url": "https://ziontechgroup.com/pricing",
    },
    "growth": {
        "name": "Zion Tech Group — Growth Tier",
        "amount": 800000,  # $8,000.00 em centavos
        "currency": "usd",
        "interval": "month",
        "description": "AI & IT services growth package — $8,000/month",
        "success_url": "https://ziontechgroup.com/success?plan=growth",
        "cancel_url": "https://ziontechgroup.com/pricing",
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_stripe():
    """Garante que stripe está importável; instala se necessário."""
    try:
        import stripe
        return stripe
    except ImportError:
        print("[INFO] Stripe library not found. Installing...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "stripe", "--quiet"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[ERROR] Failed to install stripe: {result.stderr}")
            sys.exit(1)
        import stripe
        return stripe


def load_api_key():
    """Carrega a Stripe API key de environment, arquivo, ou prompt."""
    key = os.environ.get("STRIPE_API_KEY", "").strip()
    if key:
        return key

    # Tenta ler de arquivo local (apenas desenvolvimento)
    key_file = STATE_DIR / ".stripe_key"
    if key_file.exists():
        key = key_file.read_text().strip()
        if key:
            return key

    # Prompt interativo
    print("🔑 Stripe API Key não configurada.")
    print("   - Obtém em: https://dashboard.stripe.com/apikeys")
    print("   - Use test key para desenvolvimento (sk_test_...)")
    print("   - Use live key apenas quando pronto para produção")
    print()
    key = input("Paste your Stripe API key: ").strip()
    if key:
        # Persiste para próximas execuções (apenas desenvolvimento)
        key_file.write_text(key + "\n")
        print(f"[OK] Key saved to {key_file}")
    return key


def get_stripe_billing():
    """Carrega o módulo stripe_billing e retorna uma instância configurada."""
    # Garante que o stripe_billing está no path
    sys.path.insert(0, str(AUTOMATION_DIR))
    import stripe_billing
    importlib.reload(stripe_billing)

    api_key = load_api_key()
    return stripe_billing.StripeBilling(api_key=api_key)


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_setup(billing):
    """Primeiro setup: cria products e prices no Stripe."""
    print("🚀 Configurando produtos Stripe para Zion Tech Group...")
    print()
    for key, plan in ZION_PLANS.items():
        print(f"  Criando product para: {plan['name']}")
        print(f"    Valor: ${plan['amount']/100:.2f}/{plan['interval']}")
        print(f"    Descrição: {plan['description']}")
        print()
        try:
            state = billing.get_or_create_product(key)
            print(f"  ✅ Product criado: {state['product_id']}")
            print(f"  ✅ Price criado: {state['price_id']}")
        except Exception as e:
            print(f"  ❌ Falha ao criar product: {e}")
        print()

    print("✅ Setup concluído.")
    print("   Products e prices criados no Stripe.")
    print("   Agora você pode usar comandos de checkout.")


def cmd_checkout(billing, email: str, plan_key: str, success_url: str = None, cancel_url: str = None):
    """Cria uma checkout session Stripe para um cliente."""
    if plan_key not in ZION_PLANS:
        print(f"❌ Plano desconhecido: {plan_key}")
        print(f"   Planos disponíveis: {list(ZION_PLANS.keys())}")
        sys.exit(1)

    plan = ZION_PLANS[plan_key]
    success_url = success_url or plan["success_url"]
    cancel_url = cancel_url or plan["cancel_url"]

    print(f"🔍 Criando checkout para: {email} — Plano: {plan_key}")
    print(f"   Valor: ${plan['amount']/100:.2f}/{plan['interval']}")
    print()

    try:
        session = billing.create_checkout_session(
            customer_email=email,
            plan_key=plan_key,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        checkout_url = session.get("url", "")
        print(f"✅ Checkout session criada: {session.get('id')}")
        print()
        print(f"🔗 URL de checkout: {checkout_url}")
        print()
        print("   Redirecione o cliente para esta URL para completar o pagamento.")
        print("   Após o pagamento, o cliente será redirecionado para:")
        print(f"   {success_url}")
        print()
    except Exception as e:
        print(f"❌ Falha ao criar checkout: {e}")
        sys.exit(1)


def cmd_checkout_link(billing, plan_key: str):
    """Cria um checkout link público para um plano."""
    if plan_key not in ZION_PLANS:
        print(f"❌ Plano desconhecido: {plan_key}")
        print(f"   Planos disponíveis: {list(ZION_PLANS.keys())}")
        sys.exit(1)

    plan = ZION_PLANS[plan_key]
    print(f"🔍 Criando checkout link público para: {plan_key}")
    print(f"   Valor: ${plan['amount']/100:.2f}/{plan['interval']}")
    print()

    try:
        link_url = billing.create_checkout_link(
            plan_key=plan_key,
            success_url=plan["success_url"],
            cancel_url=plan["cancel_url"],
        )
        print(f"✅ Checkout link criado")
        print()
        print(f"🔗 {link_url}")
        print()
        print("   Use este link em:")
        print(f"   - Páginas de serviço: /services/*")
        print(f"   - Blog posts que mencionam serviços")
        print(f"   - Emails de cold outreach")
        print(f"   - Página de pricing: /pricing")
        print()
    except Exception as e:
        print(f"❌ Falha ao criar checkout link: {e}")
        sys.exit(1)


def cmd_status(billing):
    """Verifica o status da conta Stripe."""
    print("🔍 Verificando status da conta Stripe...")
    print()
    try:
        health = billing.health_check()
        print(json.dumps(health, indent=2))
        print()
        if health.get("status") == "ok":
            print("✅ Conta Stripe ativa e operacional.")
            if health.get("charges_enabled"):
                print("   ✅ Cargas habilitadas — pode receber pagamentos.")
            else:
                print("   ⚠️  Cargas desabilitadas — verifique na dashboard.")
            if health.get("payouts_enabled"):
                print("   ✅ Payouts habilitados — pode sacar para conta bancária.")
            else:
                print("   ⚠️  Payouts desabilitados — configure sua conta bancária.")
        else:
            print("❌ Conta Stripe com problemas.")
            print(f"   Detalhe: {health.get('detail', 'unknown')}")
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        sys.exit(1)


def cmd_list_products(billing):
    """Lista products e prices configurados."""
    print("📦 Produtos Stripe configurados para Zion Tech Group:")
    print()
    products = billing.list_products()
    if not products:
        print("   Nenhum produto configurado ainda.")
        print("   Execute 'python3 stripe_checkout.py setup' para criar.")
    else:
        for p in products:
            print(f"   {p['plan_key']:10} — {p['product_name']}")
            print(f"             Valor: ${p['amount']/100:.2f}/{p['interval']}")
            print(f"             Product ID: {p['product_id']}")
            print(f"             Price ID:   {p['price_id']}")
            print()
    print(f"   Total: {len(products)} produtos configurados.")


def cmd_list_customers(billing):
    """Lista customers configurados localmente."""
    print("👥 Customers registrados localmente:")
    print()
    customers = billing.list_customers()
    if not customers:
        print("   Nenhum customer registrado.")
    else:
        for email, info in customers.items():
            print(f"   {email}")
            print(f"     Customer ID: {info.get('customer_id')}")
            print(f"     Criado em:   {info.get('created_at')}")
            print()
    print(f"   Total: {len(customers)} customers registrados.")


# ── Main ──────────────────────────────────────────────────────────────────────

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   Zion Tech Group — Stripe Checkout CLI                                  ║
║   Habilidades: criar checkouts, links de pagamento, gerenciar           ║
║   assinaturas SaaS para os planos Starter ($2,500/mês) e                ║
║   Growth ($8,000/mês).                                                  ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


def print_usage():
    print("Uso:")
    print()
    print("  # Setup inicial — criar products e prices no Stripe")
    print("  python3 stripe_checkout.py setup")
    print()
    print("  # Verificar status da conta Stripe")
    print("  python3 stripe_checkout.py status")
    print()
    print("  # Criar checkout session para um cliente específico")
    print("  python3 stripe_checkout.py checkout <email> <plan_key>")
    print("    plan_key: starter | growth")
    print("  Ex: python3 stripe_checkout.py checkout cli@empresa.com.br starter")
    print()
    print("  # Criar checkout link público para um plano")
    print("  python3 stripe_checkout.py link <plan_key>")
    print("    plan_key: starter | growth")
    print("  Ex: python3 stripe_checkout.py link growth")
    print()
    print("  # Listar produtos configurados")
    print("  python3 stripe_checkout.py products")
    print()
    print("  # Listar customers registrados")
    print("  python3 stripe_checkout.py customers")
    print()
    print("Configuração de API Key:")
    print("  1. Exporte a variável de ambiente: export STRIPE_API_KEY=sk_test_...")
    print("  2. Ou cole quando solicitado durante a execução.")
    print("  3. Chaves de teste (sk_test_...) são gratuitas e não cobram.")
    print()


def main():
    print_banner()

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        sys.exit(0)

    cmd = sys.argv[1]

    # Garante stripe disponível
    ensure_stripe()

    # Carrega billing
    try:
        billing = get_stripe_billing()
    except Exception as e:
        print(f"❌ Falha ao inicializar StripeBilling: {e}")
        sys.exit(1)

    # Dispatcher de comandos
    if cmd == "setup":
        cmd_setup(billing)
    elif cmd == "checkout":
        if len(sys.argv) < 3:
            print("❌ Uso: python3 stripe_checkout.py checkout <email> <plan_key> [success_url] [cancel_url]")
            sys.exit(1)
        email = sys.argv[2]
        plan_key = sys.argv[3]
        success_url = sys.argv[4] if len(sys.argv) > 4 else None
        cancel_url = sys.argv[5] if len(sys.argv) > 5 else None
        cmd_checkout(billing, email, plan_key, success_url, cancel_url)
    elif cmd == "link":
        if len(sys.argv) < 3:
            print("❌ Uso: python3 stripe_checkout.py link <plan_key>")
            sys.exit(1)
        plan_key = sys.argv[2]
        cmd_checkout_link(billing, plan_key)
    elif cmd == "status":
        cmd_status(billing)
    elif cmd == "products":
        cmd_list_products(billing)
    elif cmd == "customers":
        cmd_list_customers(billing)
    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
