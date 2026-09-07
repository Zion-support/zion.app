#!/usr/bin/env python3
"""
composio-content-agent.py
==========================
Content Agent — cria, otimiza e publica conteúdo para Zion Tech Group.

 Fluxos:
   - Criar post de LinkedIn com SEO
   - Criar tweet/thread para Twitter
   - Criar newsletter via Gmail
   - Criar blog post draft via Google Docs
   - Pesquisar trending topics via Firecrawl/Perplexity
   - Publicar e notificar Slack

 Uso:
   export COMPOSIO_API_KEY="sk_..."
   export ZION_SLACK_CHANNEL="#content"
   
   python composio-content-agent.py create-post "AI Automation para Enterprise" --linkedin --twitter
   python composio-content-agent.py newletter "Semana de IA" --send
   python composio-content-agent.py blog "AI ROI Calculator" --draft
   python composio-content-agent.py --dry-run
"""

import os
import sys
import json
from datetime import datetime
from composio import Composio

# ========== CONFIG ==========
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
SLACK_CHANNEL = os.environ.get("ZION_SLACK_CHANNEL", "#content")
DRY_RUN = "--dry-run" in sys.argv

ACTION = sys.argv[1] if len(sys.argv) > 1 else "help"
TOPIC = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

# Platform flags
CREATE_LINKEDIN = "--linkedin" in sys.argv
CREATE_TWITTER = "--twitter" in sys.argv
CREATE_GMAIL = "--email" in sys.argv or "--newsletter" in sys.argv
CREATE_DOCS = "--draft" in sys.argv or "--blog" in sys.argv

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

def slack_notify(message):
    """Notifica no Slack."""
    print(f"   📤 Slack...")
    sdk = get_sdk()
    result = tool_execute(
        sdk,
        "SLACK_SEND_MESSAGE",
        arguments={"channel": SLACK_CHANNEL, "text": message},
        user_id="zion-bot",
    )
    if result:
        print(f"   ✅ Slack notificado")
    return result

# ========== CONTENT CREATION ==========

def create_linkedin_post(topic):
    """Cria post de LinkedIn com SEO, research, e publica."""
    print(f"   🔗 Criando post LinkedIn sobre: {topic}...")
    
    sdk = get_sdk()
    
    # 1. Research via Perplexity
    research = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        arguments={
            "query": f"Crie um post de LinkedIn profissional sobre: {topic}. Inclua estatísticas, bullet points, e CTA para Zion Tech Group. Máximo 3.000 caracteres.",
            "temperature": 0.5,
            "max_tokens": 2000,
        },
        user_id="zion-bot",
    )
    
    content = research.get("content", research.get("text", f"Post sobre {topic}")) if research else f"Post sobre {topic}"
    
    # 2. Publicar no LinkedIn
    result = tool_execute(
        sdk,
        "LINKEDIN_CREATE_POST",
        arguments={
            "content": content,
            "visibility": "public",
            "title": f"Zion Tech Group — {datetime.now().strftime('%Y-%m-%d')}",
        },
        user_id="zion-bot",
    )
    
    if result:
        post_id = result.get("id", result.get("postId", ""))
        print(f"   ✅ Post publicado no LinkedIn: {post_id}")
        slack_notify(f"*✍️ LinkedIn Post — {datetime.now().strftime('%H:%M')}*\n\n**Tópico:** {topic}\n\nPost publicado. Ver: linkedin.com/feed")
        return post_id
    return None

def create_twitter_post(topic):
    """Cria thread/tweet e publica no Twitter/X."""
    print(f"   🐦 Criando tweet sobre: {topic}...")
    
    sdk = get_sdk()
    
    # 1. Research
    research = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        arguments={
            "query": f"Crie um thread de 3 tweets sobre: {topic}. Engajante, com hashtags relevantes e CTA para ziontechgroup.com. Cada tweet máximo 280 caracteres.",
            "temperature": 0.5,
            "max_tokens": 1500,
        },
        user_id="zion-bot",
    )
    
    thread = research.get("content", "") if research else f"Thread sobre {topic}"
    tweets = thread.split("\n\n")[:3]  # até 3 tweets
    
    # 2. Publicar cada tweet
    published = []
    for i, tweet in enumerate(tweets):
        tweet = tweet.strip()[:280]
        if not tweet:
            continue
        result = tool_execute(
            sdk,
            "TWITTER_CREATE_TWEET",
            arguments={"text": tweet},
            user_id="zion-bot",
        )
        if result:
            tweet_id = result.get("id", "")
            published.append(tweet_id)
            print(f"   ✅ Tweet {i+1} publicado: {tweet_id}")
    
    if published:
        slack_notify(f"*🐦 Twitter Thread — {datetime.now().strftime('%H:%M')}*\n\n**Tópico:** {topic}\n\n{published[0]} tweets publicados")
    
    return published

def create_newsletter(topic):
    """Cria newsletter via Gmail e envia."""
    print(f"   📧 Criando newsletter sobre: {topic}...")
    
    sdk = get_sdk()
    
    # 1. Create content via Perplexity
    content = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        arguments={
            "query": f"Escreva uma newsletter de 500 palavras sobre: {topic}. Título chamativo, introdução, 3 seções principais, e CTA para Zion Tech Group. Tom profissional.",
            "temperature": 0.5,
            "max_tokens": 2500,
        },
        user_id="zion-bot",
    )
    
    body = content.get("content", content.get("text", f"Newsletter sobre {topic}")) if content else f"Newsletter sobre {topic}"
    
    # 2. Send via Gmail
    recipient = os.environ.get("ZION_NEWSLETTER_LIST", "leads@ziontechgroup.com")
    result = tool_execute(
        sdk,
        "GMAIL_SEND_EMAIL",
        arguments={
            "to": recipient,
            "subject": f"Zion Tech Group — {topic} — {datetime.now().strftime('%d/%m/%Y')}",
            "body": body,
        },
        user_id="zion-bot",
    )
    
    if result:
        print(f"   ✅ Newsletter enviada para {recipient}")
        slack_notify(f"*📧 Newsletter Enviada — {datetime.now().strftime('%H:%M')}*\n\n**Tópico:** {topic}\n**Destinatários:** {recipient}")
        return True
    return None

def create_blog_draft(topic):
    """Cria draft de blog post no Google Docs."""
    print(f"   📝 Criando draft de blog sobre: {topic}...")
    
    sdk = get_sdk()
    
    # 1. Research full content
    content = tool_execute(
        sdk,
        "PERPLEXITYAI_CHAT",
        arguments={
            "query": f"Escreva um artigo de blog completo (1.500 palavras) sobre: {topic}. Título SEO, meta description, introdução, 4 seções com subtítulos, conclusão, e CTA para ziontechgroup.com.",
            "temperature": 0.4,
            "max_tokens": 3500,
        },
        user_id="zion-bot",
    )
    
    full_content = content.get("content", content.get("text", f"Artigo sobre {topic}")) if content else f"Artigo sobre {topic}"
    
    # 2. Create Google Doc
    result = tool_execute(
        sdk,
        "GOOGLEDOCS_CREATE_DOCUMENT",
        arguments={
            "title": f"Blog Post — {topic} — {datetime.now().strftime('%Y-%m-%d')}",
            "content": full_content,
        },
        user_id="zion-bot",
    )
    
    if result:
        doc_id = result.get("id", result.get("documentId", ""))
        print(f"   ✅ Draft criado no Google Docs: {doc_id}")
        slack_notify(f"*📝 Blog Draft — {datetime.now().strftime('%H:%M')}*\n\n**Tópico:** {topic}\n\nGoogle Doc criado. Editar e publicar: docs.google.com")
        return doc_id
    return None

# ========== MAIN ==========
def main():
    if not COMPOSIO_API_KEY:
        print("❌ COMPOSIO_API_KEY não configurada")
        sys.exit(1)
    
    if ACTION == "help" or ACTION is None:
        print("""
📋 Content Agent — Uso:

  python composio-content-agent.py "TÓPICO" --linkedin
      Cria e publica post de LinkedIn

  python composio-content-agent.py "TÓPICO" --twitter
      Cria e publica thread no Twitter

  python composio-content-agent.py "TÓPICO" --newsletter
      Cria e envia newsletter via Gmail

  python composio-content-agent.py "TÓPICO" --draft
      Cria draft de blog no Google Docs

  python composio-content-agent.py "TÓPICO" --linkedin --twitter --newsletter
      Publica em múltiplas plataformas

  python composio-content-agent.py --dry-run
      Testa configuração sem publicar

Exemplo:
  export COMPOSIO_API_KEY='sk_...'
  export ZION_SLACK_CHANNEL='#content'
  python composio-content-agent.py "AI Automation para Enterprise" --linkedin --twitter --draft
""")
        return
    
    if DRY_RUN:
        print("🔍 Dry-run — não criando conteúdo")
        print(f"   Tópico: {TOPIC}")
        platforms = []
        if CREATE_LINKEDIN: platforms.append("LinkedIn")
        if CREATE_TWITTER: platforms.append("Twitter")
        if CREATE_GMAIL: platforms.append("Gmail/Newsletter")
        if CREATE_DOCS: platforms.append("Google Docs")
        print(f"   Plataformas: {', '.join(platforms) or ' Todas'}")
        return
    
    if not TOPIC:
        print("❌ Tópico necessário")
        print("Uso: python composio-content-agent.py <tópico> [flags]")
        sys.exit(1)
    
    results = {}
    
    if CREATE_LINKEDIN or not any([CREATE_LINKEDIN, CREATE_TWITTER, CREATE_GMAIL, CREATE_DOCS]):
        results["linkedin"] = create_linkedin_post(TOPIC)
    
    if CREATE_TWITTER:
        results["twitter"] = create_twitter_post(TOPIC)
    
    if CREATE_GMAIL:
        results["newsletter"] = create_newsletter(TOPIC)
    
    if CREATE_DOCS:
        results["blog_draft"] = create_blog_draft(TOPIC)
    
    published = [k for k, v in results.items() if v]
    if published:
        print(f"\n✅ Content Agent concluído")
        print(f"   Criado em: {', '.join(published)}")
    else:
        print(f"\n⚠️  Nenhum conteúdo criado")

if __name__ == "__main__":
    main()
