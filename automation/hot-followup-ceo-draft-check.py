#!/usr/bin/env python3
"""
Hot-follow-up CEO reply draft generator.
Checks for hot-follow-up threads and drafts replies in the thread's language.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("/Users/miami2/zion.app/automation/data/lead-outreach")
DRAFT_FILE = Path("/Users/miami2/zion.app/automation/hot-followup-ceo-reply-draft.txt")
SENT_FILE = Path("/Users/miami2/zion.app/automation/data/lead-outreach/hot-followup-sent.json")

CALENDLY_URL = "https://calendly.com/kleber-ziontechgroup"
ZION_URL = "https://ziontechgroup.com"

# AI services and free tools to mention
AI_SERVICES = [
    "IA generativa e LLMs",
    "automação de e-mail com inteligência artificial",
    "agentes autônomos para suporte e vendas",
    "análise de sentimentos e classificação de intenção",
    "integração de IA em CRM e ferramentas de gestão",
]

FREE_TOOLS = [
    "ferramentas gratuitas de automação de e-mail",
    "modelos de prospeção e follow-up",
    "benchmark de resposta para campanhas B2B",
]


def probe_hot_followup_threads():
    """Search Gmail for hot-follow-up threads. Returns list of thread records."""
    try:
        result = subprocess.run(
            [
                "gog", "gmail", "search",
                "label:!!!hot-follow-up",
                "--max", "5",
                "--plain",
                "--no-input",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout.strip()
        if not stdout or "No results" in stdout:
            return []
        # Parse TSV: ID\tDATE\tFROM\tSUBJECT\tLABELS\tTHREAD
        threads = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 6:
                threads.append({
                    "id": parts[0],
                    "date": parts[1],
                    "from": parts[2],
                    "subject": parts[3],
                    "labels": parts[4],
                    "thread_id": parts[5],
                })
        return threads
    except Exception as e:
        print(f"[WARN] Hot-followup probe failed: {e}", file=sys.stderr)
        return []


def get_thread_language(thread_subject: str) -> str:
    """Detect language from subject heuristics. Returns 'pt-BR', 'en', 'es', or 'en' as default."""
    subject_lower = thread_subject.lower()
    if any(word in subject_lower for word in ["re:", "assunto:", "parceria", "operações", "eficiência", "para", "ti", "orçamento", "proposta", "suporte", "cotização"]):
        return "pt-BR"
    if any(word in subject_lower for word in ["hola", "gracias", "servicio", "propuesta", "operaciones"]):
        return "es"
    return "en"


def build_ceo_reply(thread_subject: str, language: str, thread_from: str) -> str:
    """Build a contextually appropriate CEO reply."""
    subject_prefix = f"Re: {thread_subject}" if thread_subject else "Following up — Zion Tech Group"

    if language == "pt-BR":
        greeting = f"Olá, obrigado pelo contato!"
        body = f"""\
{greeting}

Agradecemos a oportunidade de conversar. Na Zion Tech Group, ajudamos empresas a
transformar operações de TI com soluções práticas e inteligentes.

Estamos lançando novos serviços de IA que podem fazer diferença real no seu negócio:

{chr(10).join(f'- {s}' for s in AI_SERVICES)}

Também disponibilizamos algumas ferramentas gratuitas para quem quer começar a
explorar agora:

{chr(10).join(f'- {t}' for t in FREE_TOOLS)}

Se quisermarcar uma conversa rápida para vermos como tudo isso se encaixa no seu
contexto, é só escolher um horário na minha agenda:
{CALENDLY_URL}

Também dá para conferir nosso trabalho e cases no site:
{ZION_URL}

Fico à disposição.

Atenciosamente,
Kleber — CEO, Zion Tech Group
"""
    elif language == "es":
        greeting = "¡Hola, gracias por contactarnos!"
        body = f"""\
{greeting}

Agradecemos la oportunidad de conversar. En Zion Tech Group ayudamos a empresas a
transformar sus operaciones de TI con soluciones prácticas e inteligentes.

Estamos lanzando nuevos servicios de IA que pueden hacer una diferencia real en
tu negocio:

{chr(10).join(f'- {s}' for s in AI_SERVICES)}

También ponemos a disposición algunas herramientas gratuitas para quien quiere
comenzar a explorar ahora:

{chr(10).join(f'- {t}' for t in FREE_TOOLS)}

Si quieres agendar una conversación rápida para ver cómo todo esto encaja en tu
contexto, elija un horario en mi agenda:
{CALENDLY_URL}

También puede ver nuestro trabajo y casos de éxito en el sitio:
{ZION_URL}

Quedo a disposición.

Saludos cordiales,
Kleber — CEO, Zion Tech Group
"""
    else:  # English
        greeting = "Hi, thanks for reaching out!"
        body = f"""\
{greeting}

Thanks for the conversation. At Zion Tech Group, we help companies transform their
IT operations with practical, intelligent solutions.

We're rolling out new AI services that can make a real difference for your business:

{chr(10).join(f'- {s}' for s in AI_SERVICES)}

We also offer some free tools to help you get started exploring right away:

{chr(10).join(f'- {t}' for t in FREE_TOOLS)}

If you'd like to hop on a quick call to see how this all fits your context,
pick a time on my calendar:
{CALENDLY_URL}

You can also check out our work and case studies at:
{ZION_URL}

Happy to help.

Best,
Kleber — CEO, Zion Tech Group
"""

    return f"Subject: {subject_prefix}\n\n{body}"


def load_sent_set() -> dict:
    """Load the set of already-sent thread IDs."""
    if not SENT_FILE.exists():
        return {}
    try:
        return json.loads(SENT_FILE.read_text())
    except Exception:
        return {}


def save_sent_state(thread_id: str, record: dict):
    """Mark a thread as sent."""
    sent = load_sent_set()
    sent[thread_id] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "subject": record.get("subject", ""),
        "from": record.get("from", ""),
    }
    SENT_FILE.write_text(json.dumps(sent, indent=2, ensure_ascii=False))


def main():
    print("=" * 60)
    print("HOT-FOLLOW-UP CEO REPLY DRAFT CHECK")
    print("=" * 60)

    threads = probe_hot_followup_threads()
    print(f"\nHot-follow-up threads found: {len(threads)}")

    if not threads:
        print("\nNo hot-follow-up threads active.")
        print("No CEO draft required at this time.")
        # Remove stale draft if exists
        if DRAFT_FILE.exists():
            DRAFT_FILE.unlink()
            print(f"Removed stale draft: {DRAFT_FILE}")
        print("\n[SILENT]")
        return

    sent = load_sent_set()
    unsent_threads = [t for t in threads if t["thread_id"] not in sent]

    print(f"Already sent: {len(sent)}")
    print(f"Unsent candidates: {len(unsent_threads)}")

    if not unsent_threads:
        print("\nAll hot-follow-up threads already handled.")
        print("No new CEO draft required.")
        print("\n[SILENT]")
        return

    # Process the first unsent thread
    thread = unsent_threads[0]
    print(f"\nProcessing thread:")
    print(f"  ID: {thread['id']}")
    print(f"  Thread ID: {thread['thread_id']}")
    print(f"  From: {thread['from']}")
    print(f"  Subject: {thread['subject']}")

    language = get_thread_language(thread["subject"])
    print(f"  Detected language: {language}")

    draft = build_ceo_reply(thread["subject"], language, thread["from"])

    DRAFT_FILE.write_text(draft, encoding="utf-8")
    print(f"\nDraft written to: {DRAFT_FILE}")
    print(f"\n--- DRAFT CONTENT ---")
    print(draft)
    print(f"--- END DRAFT ---")

    # Mark as would-send (do NOT actually send unless configured)
    # save_sent_state(thread["thread_id"], thread)  # Commented: do not send unless configured
    print(f"\nDraft prepared but NOT sent (send not configured).")
    print(f"To send: review {DRAFT_FILE} and trigger live send manually.")
    print(f"\nStatus: DRAFT_READY")


if __name__ == "__main__":
    main()
