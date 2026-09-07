"""
Zion Tech Group — Stripe Billing Integration Module

Gerencia assinaturas SaaS: cria customers, products, prices, checkout sessions,
subscriptions, e lida com webhooks de lifecycle.

Requirements:
  - stripe package (pip install stripe)
  - STRIPE_API_KEY environment variable (sk_live_... or sk_test_...)
  - STRIPE_WEBHOOK_SECRET for webhook signature verification

Usage:
  from stripe_billing import StripeBilling
  billing = StripeBilling()
  session = billing.create_checkout_session(customer_email, price_id, success_url, cancel_url)
"""

import os
import json
import stripe
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

# ── Configuration ────────────────────────────────────────────────────────────

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

# ── Constants ────────────────────────────────────────────────────────────────

# Plan definitions (Zion Tech Group services)
ZION_PLANS = {
    "starter": {
        "product_name": "Zion Tech Group — Starter Tier",
        "plan_name": "Starter",
        "amount": 250000,  # $2,500.00 in cents
        "currency": "usd",
        "interval": "month",
        "description": "AI & IT services starter package — $2,500/month",
        "metadata": {"tier": "starter", "company": "ziontechgroup"},
    },
    "growth": {
        "product_name": "Zion Tech Group — Growth Tier",
        "plan_name": "Growth",
        "amount": 800000,  # $8,000.00 in cents
        "currency": "usd",
        "interval": "month",
        "description": "AI & IT services growth package — $8,000/month",
        "metadata": {"tier": "growth", "company": "ziontechgroup"},
    },
}

# Where to store state between runs
STATE_DIR = Path(__file__).resolve().parent / "stripe-state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


# ── StripeBilling Class ──────────────────────────────────────────────────────

class StripeBilling:
    """
    Gerencia o ciclo completo de assinaturas Stripe para Zion Tech Group.

    Responsabilidades:
    - Criar/lookup customers no Stripe
    - Criar products e prices para os planos Zion
    - Gerar Stripe Checkout Sessions para pagamento único ou assinatura
    - Processar webhooks de assinatura (created, updated, cancelled, payment_failed)
    - Persistir estado localmente para recuperação entre execuções
    """

    def __init__(self, api_key: str = None, webhook_secret: str = None):
        if api_key:
            stripe.api_key = api_key
        elif STRIPE_API_KEY:
            stripe.api_key = STRIPE_API_KEY
        else:
            raise RuntimeError(
                "Stripe API key not configured. "
                "Set STRIPE_API_KEY environment variable or pass api_key to constructor."
            )
        self.webhook_secret = webhook_secret or WEBHOOK_SECRET
        self.state_dir = STATE_DIR

    # ── Customers ────────────────────────────────────────────────────────────

    def get_or_create_customer(
        self,
        email: str,
        name: str = "",
        company: str = "",
        metadata: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        Retorna um customer Stripe existente por email, ou cria um novo.
        Persiste o ID localmente para referência futura.
        """
        metadata = metadata or {}
        if company:
            metadata["company"] = company
        if name:
            metadata["name"] = name

        # Tenta encontrar existente pelo email
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                customer = customers.data[0]
                self._save_customer_local(email, customer.id)
                return customer
        except stripe.error.StripeError as e:
            print(f"[WARN] Customer lookup failed: {e}")

        # Cria novo
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name or None,
                metadata=metadata,
            )
            self._save_customer_local(email, customer.id)
            print(f"[stripe] Created customer: {customer.id} ({email})")
            return customer
        except stripe.error.StripeError as e:
            print(f"[ERROR] Customer creation failed: {e}")
            raise

    def _save_customer_local(self, email: str, customer_id: str):
        """Persiste mapeamento email→customer_id localmente."""
        path = self.state_dir / "customers.json"
        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                data = {}
        data[email.lower()] = {
            "customer_id": customer_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(data, indent=2) + "\n")

    def get_customer_id(self, email: str) -> Optional[str]:
        """Retorna o customer_id armazenado localmente para um email."""
        path = self.state_dir / "customers.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return data.get(email.lower(), {}).get("customer_id")
        except (json.JSONDecodeError, OSError):
            return None

    # ── Products & Prices ────────────────────────────────────────────────────

    def get_or_create_product(self, plan_key: str) -> Dict[str, Any]:
        """
        Cria ou retorna o product Stripe para um plano Zion.
        Persiste product_id e price_id localmente.
        """
        plan = ZION_PLANS.get(plan_key)
        if not plan:
            raise ValueError(f"Unknown plan: {plan_key}. Available: {list(ZION_PLANS.keys())}")

        state_path = self.state_dir / f"product_{plan_key}.json"

        # Retorna estado persistido se existir
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text())
                # Verifica se ainda existe no Stripe
                try:
                    stripe.Product.retrieve(state["product_id"])
                    return state
                except stripe.error.InvalidRequestError:
                    pass  # Product deletado, recria
            except (json.JSONDecodeError, OSError, KeyError):
                pass

        # Cria product
        product = stripe.Product.create(
            name=plan["product_name"],
            description=plan["description"],
            metadata=plan["metadata"],
        )

        # Cria price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=plan["amount"],
            currency=plan["currency"],
            recurring={"interval": plan["interval"]},
            billing_scheme="per_unit",
        )

        state = {
            "plan_key": plan_key,
            "product_id": product.id,
            "price_id": price.id,
            "product_name": plan["product_name"],
            "amount": plan["amount"],
            "currency": plan["currency"],
            "interval": plan["interval"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        state_path.write_text(json.dumps(state, indent=2) + "\n")
        print(f"[stripe] Created product+price for {plan_key}: {product.id} / {price.id}")
        return state

    def get_price_id(self, plan_key: str) -> Optional[str]:
        """Retorna o price_id persistido para um plano."""
        state_path = self.state_dir / f"product_{plan_key}.json"
        if not state_path.exists():
            return None
        try:
            state = json.loads(state_path.read_text())
            return state.get("price_id")
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    # ── Checkout Sessions ────────────────────────────────────────────────────

    def create_checkout_session(
        self,
        customer_email: str,
        plan_key: str,
        success_url: str,
        cancel_url: str,
        customer_name: str = "",
        customer_company: str = "",
        metadata: Dict[str, str] = None,
        trial_days: int = 0,
        mode: str = "subscription",  # or "payment"
    ) -> Dict[str, Any]:
        """
        Cria uma Stripe Checkout Session.

        - mode='subscription': assinatura recorrente (ou trial)
        - mode='payment': pagamento único

        Retorna a session com o URL de checkout para redirecionar o cliente.
        """
        customer = self.get_or_create_customer(
            email=customer_email,
            name=customer_name,
            company=customer_company,
            metadata=metadata or {},
        )

        price_state = self.get_or_create_product(plan_key)
        price_id = price_state["price_id"]

        line_items = [{"price": price_id, "quantity": 1}]

        session_params = {
            "customer": customer.id,
            "customer_email": customer_email,
            "line_items": line_items,
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "company": "ziontechgroup",
                "plan": plan_key,
                "customer_email": customer_email,
                **(metadata or {}),
            },
            "payment_method_types": ["card"],
        }

        if mode == "subscription" and trial_days > 0:
            session_params["discounts"] = None  # Usar trial via price ou subscription_data
            # Alternativa: usar subscription_data com trial_period_days via Checkout com price que tenha trial
            # A maneira mais limpa: criar price com trial, mas aqui mantemos simples

        try:
            session = stripe.checkout.Session.create(**session_params)
            print(f"[stripe] Checkout session created: {session.id} → {session.url}")
            return session
        except stripe.error.StripeError as e:
            print(f"[ERROR] Checkout session creation failed: {e}")
            raise

    def create_checkout_link(
        self,
        plan_key: str,
        success_url: str = "https://ziontechgroup.com/success",
        cancel_url: str = "https://ziontechgroup.com/pricing",
        metadata: Dict[str, str] = None,
    ) -> str:
        """
        Cria um Checkout Link público (sem customer prévio) — ideal para páginas de serviço.

        O cliente insere email no checkout. Retorna URL direta para redirecionamento.
        """
        price_state = self.get_or_create_product(plan_key)

        link_params = {
            "line_items": [{"price": price_state["price_id"], "quantity": 1}],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "company": "ziontechgroup",
                "plan": plan_key,
                **(metadata or {}),
            },
        }

        link = stripe.checkout.Session.create(**link_params)
        return link.url

    # ── Subscriptions ────────────────────────────────────────────────────────

    def get_subscription_status(self, customer_id: str) -> List[Dict[str, Any]]:
        """Retorna todas as assinaturas ativas de um customer."""
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id, limit=10)
            return [
                {
                    "id": s.id,
                    "status": s.status,
                    "plan": s.items.data[0].price.id if s.items.data else None,
                    "current_period_end": s.current_period_end,
                    "customer_email": s.customer.email if hasattr(s.customer, 'email') else None,
                    "metadata": s.metadata,
                }
                for s in subscriptions.data
            ]
        except stripe.error.StripeError as e:
            print(f"[WARN] Subscription lookup failed: {e}")
            return []

    def cancel_subscription(self, subscription_id: str, reason: str = "") -> Dict[str, Any]:
        """Cancela uma assinatura (immediate)."""
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            canceled = stripe.Subscription.cancel(
                subscription_id,
                cancellation_method="immediate",
                proration="none",
            )
            self._log_subscription_event(subscription_id, "canceled", reason)
            print(f"[stripe] Subscription canceled: {subscription_id}")
            return canceled
        except stripe.error.StripeError as e:
            print(f"[ERROR] Subscription cancellation failed: {e}")
            raise

    # ── Webhooks ─────────────────────────────────────────────────────────────

    def construct_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verifica e constrói um evento Stripe a partir de payload e signature.
        Usado em handlers de webhook HTTP.
        """
        if not self.webhook_secret:
            raise RuntimeError("Stripe webhook secret not configured")
        return stripe.Webhook.construct_event(payload, signature, self.webhook_secret)

    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um evento Stripe e retorna a ação tomada.
        Usado como dispatcher central para webhooks.
        """
        event_type = event["type"]
        data = event["data"]["object"]
        result = {"event_type": event_type, "action": "ignored", "detail": ""}

        if event_type == "checkout.session.completed":
            result["action"] = "notify"
            result["detail"] = f"Checkout completed: {data.get('id')} — customer: {data.get('customer_email')}"
            self._log_checkout_completed(data)

        elif event_type == "customer.subscription.created":
            result["action"] = "provision"
            result["detail"] = f"Subscription created: {data.get('id')} — plan: {data.get('items', [{}])[0].get('price', {}).get('product')}"
            self._log_subscription_event(data.id, "created", "")

        elif event_type == "customer.subscription.updated":
            result["action"] = "sync"
            result["detail"] = f"Subscription updated: {data.get('id')} — status: {data.get('status')}"
            self._log_subscription_event(data.id, "updated", "")

        elif event_type == "customer.subscription.deleted":
            result["action"] = "revoke_access"
            result["detail"] = f"Subscription canceled: {data.get('id')}"
            self._log_subscription_event(data.id, "deleted", "")

        elif event_type == "invoice.payment_failed":
            result["action"] = "dunning"
            result["detail"] = f"Payment failed for invoice: {data.get('id')}"
            self._log_invoice_event(data.id, "payment_failed", "")

        elif event_type == "invoice.paid":
            result["action"] = "record"
            result["detail"] = f"Invoice paid: {data.get('id')} — amount: ${data.get('amount_paid')/100:.2f}"

        else:
            result["detail"] = f"Event type {event_type} not handled"

        return result

    # ── Local Logging ────────────────────────────────────────────────────────

    def _log_checkout_completed(self, session_data: Dict[str, Any]):
        log_path = self.state_dir / "checkout-completed.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_data.get("id"),
            "customer_email": session_data.get("customer_email"),
            "amount_total": session_data.get("amount_total"),
            "payment_status": session_data.get("payment_status"),
            "metadata": session_data.get("metadata"),
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _log_subscription_event(self, subscription_id: str, event_type: str, reason: str):
        log_path = self.state_dir / "subscription-events.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subscription_id": subscription_id,
            "event": event_type,
            "reason": reason,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _log_invoice_event(self, invoice_id: str, event_type: str, reason: str):
        log_path = self.state_dir / "invoice-events.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "invoice_id": invoice_id,
            "event": event_type,
            "reason": reason,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── Utility ──────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Verifica se a conexão com Stripe está saudável."""
        try:
            account = stripe.Account.retrieve()
            return {
                "status": "ok",
                "account_id": account.id,
                "business_name": account.business_profile.get("name") if account.business_profile else None,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
            }
        except stripe.error.StripeError as e:
            return {"status": "error", "detail": str(e)}

    def list_products(self) -> List[Dict[str, Any]]:
        """Lista products e prices configurados localmente."""
        products = []
        for state_file in self.state_dir.glob("product_*.json"):
            try:
                state = json.loads(state_file.read_text())
                products.append(state)
            except (json.JSONDecodeError, OSError):
                pass
        return products

    def list_customers(self) -> Dict[str, str]:
        """Retorna mapeamento email→customer_id."""
        path = self.state_dir / "customers.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}


# ── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    def print_usage():
        print("""
Zion Stripe Billing CLI — uso:

  # Health check da conta Stripe
  python3 stripe_billing.py health

  # Criar ou listar produtos/plans
  python3 stripe_billing.py products

  # Criar checkout session para um cliente
  python3 stripe_billing.py checkout <email> <plan_key> [success_url] [cancel_url]
    plan_key: starter | growth

  # Criar checkout link público (para páginas de serviço)
  python3 stripe_billing.py checkout-link <plan_key>

  # Status da conta Stripe
  python3 stripe_billing.py status
        """)

    billing = StripeBilling()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    args = sys.argv[2:]

    if cmd == "health":
        result = billing.health_check()
        print(json.dumps(result, indent=2))

    elif cmd == "products":
        products = billing.list_products()
        if not products:
            for key in ZION_PLANS:
                state = billing.get_or_create_product(key)
                products.append(state)
        for p in products:
            print(f"  {p['plan_key']}: {p['product_name']} — ${p['amount']/100:.2f}/{p['interval']} — price_id: {p['price_id']}")

    elif cmd == "checkout":
        if len(args) < 2:
            print_usage()
            sys.exit(1)
        email = args[0]
        plan_key = args[1]
        success_url = args[2] if len(args) > 2 else "https://ziontechgroup.com/success"
        cancel_url = args[3] if len(args) > 3 else "https://ziontechgroup.com/pricing"
        session = billing.create_checkout_session(
            email=email,
            plan_key=plan_key,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        print(json.dumps(session, indent=2, ensure_ascii=False))
        print(f"\n🔗 Checkout URL: {session.get('url')}")

    elif cmd == "checkout-link":
        if len(args) < 1:
            print_usage()
            sys.exit(1)
        plan_key = args[0]
        url = billing.create_checkout_link(
            plan_key=plan_key,
            success_url="https://ziontechgroup.com/success",
            cancel_url="https://ziontechgroup.com/pricing",
        )
        print(f"🔗 Checkout Link: {url}")

    elif cmd == "status":
        result = billing.health_check()
        print(json.dumps(result, indent=2))

    else:
        print_usage()
