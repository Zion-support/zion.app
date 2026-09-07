#!/usr/bin/env python3
"""
composio-daily-digest.py — Daily Zion Health Digest
====================================================
Compila e reporta no Slack o status diário do Zion Tech Group.

 Apps envolvidos: GitHub + Slack + Linear + PostHog + Sentry + Vercel
 Ferramentas Composio: GITHUB_LIST_PULL_REQUESTS, LINEAR_LIST_ISSUES,
    POSTHOG_FETCH_EVENTS, SENTRY_LIST_ISSUE, VERCEL_GET_DEPLOYMENTS,
    SLACK_SEND_MESSAGE

 Uso: python composio-daily-digest.py [--channel #status] [--date YYYYMMDD]
"""

import os
import sys
import json
from datetime import datetime, timedelta
from composio import Composio

# ========== CONFIG ==========
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#status")
REPORT_TIME = os.environ.get("ZION_DIGEST_TIME", "09:00")
ZION_GITHUB_OWNER = os.environ.get("ZION_GITHUB_OWNER", "Zion-TechGroup")
ZION_GITHUB_REPO = os.environ.get("ZION_GITHUB_REPO", "zion.app")
ZION_VERCEL_PROJECT = os.environ.get("ZION_VERCEL_PROJECT", "zion-tech-group")
POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")
POSTHOG_URL = os.environ.get("POSTHOG_URL", "https://app.posthog.com")

# ========== COMPOSI SETUP ==========
def get_sdk():
    api_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not api_key:
        print("ERRO: COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    return Composio(api_key=api_key)

# ========== FUNCTIONS ==========
def fetch_github_prs(sdk, days=1):
    """Busca PRs merged nos últimos N dias."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    resp = sdk.tools.execute(
        "GITHUB_LIST_PULL_REQUESTS",
        arguments={
            "owner": ZION_GITHUB_OWNER,
            "repo": ZION_GITHUB_REPO,
            "state": "closed",
            "since": start_date.isoformat(),
        },
        user_id="zion-bot",
    )
    
    prs = resp.get("items", []) if isinstance(resp, dict) else []
    merged = [p for p in prs if p.get("merged_at")]
    return merged

def fetch_linear_issues(sdk, days=1):
    """Busca issues criados/attribuídos nos últimos N dias."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    resp = sdk.tools.execute(
        "LINEAR_LIST_ISSUES",
        arguments={
            "filter": {
                "createdAt": {"gte": since},
            },
            "first": 20,
        },
        user_id="zion-bot",
    )
    
    issues = resp.get("issues", []) if isinstance(resp, dict) else []
    return issues[:10]  # top 10

def check_vercel_status(sdk):
    """Verifica status do último deploy no Vercel."""
    resp = sdk.tools.execute(
        "VERCEL_GET_DEPLOYMENTS",
        arguments={
            "projectId": ZION_VERCEL_PROJECT,
            "limit": 1,
        },
        user_id="zion-bot",
    )
    
    deploys = resp.get("deployments", []) if isinstance(resp, dict) else []
    if deploys:
        latest = deploys[0]
        return {
            "url": latest.get("url", "N/A"),
            "status": latest.get("status", "unknown"),
            "created_at": latest.get("createdAt", "N/A"),
        }
    return {"status": "sem deploys recentes"}

def fetch_sentry_errors(sdk, days=1):
    """Busca erros novos no Sentry."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    resp = sdk.tools.execute(
        "SENTRY_LIST_ISSUE",
        arguments={
            "since": since,
            "limit": 5,
        },
        user_id="zion-bot",
    )
    
    issues = resp.get("issues", []) if isinstance(resp, dict) else []
    return issues[:5]

def fetch_posthog_metrics(api_key, days=1):
    """Fetch basic metrics from PostHog."""
    if not api_key:
        return {"events": "N/A", "note": "PostHog API key não configurado"}
    
    # via Composio toolkit se disponível, senão via API direta
    try:
        sdk = get_sdk()
        resp = sdk.tools.execute(
            "POSTHOG_FETCH_EVENTS",
            arguments={
                "api_key": api_key,
                "url": POSTHOG_URL,
                "days": days,
            },
            user_id="zion-bot",
        )
        return resp
    except Exception as e:
        return {"events": "erro", "note": str(e)}

def build_digest(prs, linear_issues, vercel, sentry, posthog):
    """Monta a mensagem de digest do Slack."""
    lines = []
    lines.append(f"*🤖 Daily Zion Digest — {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")
    
    # PRs
    lines.append(f"*🔀 GitHub — PRs Merged (24h):* `{len(prs)}`")
    for pr in prs[:5]:
        lines.append(f"  • #{pr.get('number')} {pr.get('title','')[:60]}")
    if len(prs) > 5:
        lines.append(f"  …e mais {len(prs)-5} PRs")
    lines.append("")
    
    # Linear issues
    lines.append(f"*📋 Linear — Issues recentes:* `{len(linear_issues)}`")
    for issue in linear_issues[:5]:
        title = issue.get("title", "")[:55]
        state = issue.get("state", {}).get("name", "?}") if isinstance(issue.get("state"), dict) else str(issue.get("state", "?"))
        lines.append(f"  • [{state}] {title}")
    lines.append("")
    
    # Vercel
    if vercel.get("status"):
        icon = "✅" if vercel["status"] == "ready" else "⚠️" if vercel["status"] == "building" else "🔴"
        lines.append(f"*🚀 Vercel Deploy:* {icon} {vercel['status']}")
        if vercel.get("url"):
            lines.append(f"  `{vercel['url']}`")
        lines.append("")
    
    # Sentry
    if sentry:
        lines.append(f"*🚨 Sentry — Erros novos (24h):* `{len(sentry)}`")
        for err in sentry:
            title = err.get("title", "")[:55]
            lines.append(f"  • {title}")
    else:
        lines.append("*🚨 Sentry:* sem erros novos ✅")
    lines.append("")
    
    # PostHog
    if isinstance(posthog, dict):
        events = posthog.get("events", "N/A")
        note = posthog.get("note", "")
        lines.append(f"*📊 PostHog:* {events} eventos")
        if note:
            lines.append(f"  _{note}_")
    lines.append("")
    
    lines.append(f"_Gerado automaticamente pelo Daily Digest Bot • Zion Tech Group_")
    
    return "\n".join(lines)

def send_slack(sdk, message, channel=SLACK_CHANNEL):
    """Envia a mensagem no Slack."""
    resp = sdk.tools.execute(
        "SLACK_SEND_MESSAGE",
        arguments={
            "channel": channel,
            "text": message,
        },
        user_id="zion-bot",
    )
    return resp

# ========== MAIN ==========
def main():
    sdk = get_sdk()
    
    print("📡 Consultando GitHub...")
    prs = fetch_github_prs(sdk, days=1)
    print(f"   → {len(prs)} PRs merged")
    
    print("📡 Consultando Linear...")
    linear_issues = fetch_linear_issues(sdk, days=1)
    print(f"   → {len(linear_issues)} issues recentes")
    
    print("📡 Verificando Vercel...")
    vercel = check_vercel_status(sdk)
    print(f"   → status: {vercel.get('status')}")
    
    print("📡 Consultando Sentry...")
    sentry = fetch_sentry_errors(sdk, days=1)
    print(f"   → {len(sentry)} erros novos")
    
    print("📡 Consultando PostHog...")
    posthog = fetch_posthog_metrics(POSTHOG_API_KEY, days=1)
    
    digest = build_digest(prs, linear_issues, vercel, sentry, posthog)
    
    print("\n📤 Enviando para Slack...")
    send_slack(sdk, digest)
    print("   ✅ Digest enviado!")
    
    # Também salva localmente para auditoria
    with open("/tmp/composio-daily-digest.json", "w") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "prs_count": len(prs),
            "linear_issues_count": len(linear_issues),
            "vercel_status": vercel.get("status"),
            "sentry_errors_count": len(sentry),
        }, f, indent=2)

if __name__ == "__main__":
    main()
