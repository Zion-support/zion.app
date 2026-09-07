#!/usr/bin/env python3
"""Prepare hot-followup CEO reply draft for ziontechgroup.com.

Scans inbox for hot-follow-up threads using gog gmail search and drafts
a contextually appropriate CEO reply in the same language as the thread,
including Calendly, ziontechgroup.com, new AI services, and free tools.
Does NOT send — only prepares hot-followup-ceo-reply-draft.txt.
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/Users/miami2/zion.app/automation")
DRAFT_PATH = WORKSPACE / "hot-followup-ceo-reply-draft.txt"
SENT_FILE = WORKSPACE / "hot-followup-sent.json"

# Load sent state
sent_state = {}
if SENT_FILE.exists():
    sent_state = json.loads(SENT_FILE.read_text())

def gog_search(query: str, max_results: int = 25) -> list[dict]:
    """Run gog gmail search and return parsed results."""
    try:
        result = subprocess.run(
            ["gog", "gmail", "search", query, "--max", str(max_results),
             "--plain", "--no-input"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"gog search failed: {result.stderr}", file=sys.stderr)
            return []
        return parse_tsv(result.stdout)
    except FileNotFoundError:
        print("gog binary not found on PATH", file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print("gog search timed out (likely auth issue)", file=sys.stderr)
        return []

def parse_tsv(output: str) -> list[dict]:
    """Parse gog gmail search TSV output into records."""
    records = []
    seen_ids = set()
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("ID") or line.startswith("Fetched"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            rec = {
                "id": parts[0].strip(),
                "thread_id": parts[1].strip() if len(parts) > 1 else "",
                "from": parts[2].strip() if len(parts) > 2 else "",
                "subject": parts[3].strip() if len(parts) > 3 else "",
                "date": parts[4].strip() if len(parts) > 4 else "",
                "snippet": parts[5].strip() if len(parts) > 5 else "",
            }
        except IndexError:
            continue
        if rec["id"] and rec["id"] not in seen_ids:
            seen_ids.add(rec["id"])
            records.append(rec)
    return records

# Step 1: probe hot-follow-up label
print("=== Probing hot-follow-up label ===")
threads = gog_search("label:!!!hot-follow-up", max_results=25)
print(f"Found {len(threads)} hot-follow-up threads")

if not threads:
    print("No hot-follow-up threads found. No draft needed.")
    DRAFT_PATH.write_text(
        "# Hot-followup CEO reply draft\n"
        "# Status: NO ACTIVE THREADS\n"
        f"# Scan time: 2026-09-05T15:35 UTC\n"
        "# No hot-follow-up threads detected in inbox.\n"
        "# No CEO draft prepared this cycle.\n"
    )
    print(f"Draft written to {DRAFT_PATH}")
    sys.exit(0)

# Step 2: find an unsent thread
unsent = [t for t in threads if t["thread_id"] not in sent_state]
if not unsent:
    print("All hot-follow-up threads already sent. No new draft needed.")
    sys.exit(0)

target = unsent[0]
print(f"Selected unsent thread: {target['id']} / {target['thread_id']}")
print(f"From: {target['from']}")
print(f"Subject: {target['subject']}")

# Step 3: detect language from subject
subject = target.get("subject", "")
def detect_lang(s: str) -> str:
    # Simple heuristic: check for Portuguese, Spanish, English markers
    pt_markers = ["re:", "parceria", "sobre", "contribuição", "operações", "eficiência",
                  "cotização", "proposta", "orçamento", "serviço", "suporte", "solicitação",
                  "agradeço", "obrigado", "desenvolvimento", "ti", "software", "solução"]
    es_markers = ["sobre", "parceria", "operaciones", "eficiencia", "cotizacion",
                  "propuesta", "presupuesto", "servicio", "soporte", "gracias",
                  "desarrollo", "software", "solucion"]
    s_lower = s.lower()
    pt_score = sum(1 for m in pt_markers if m in s_lower)
    es_score = sum(1 for m in es_markers if m in s_lower)
    if pt_score >= es_score and pt_score > 0:
        return "pt"
    if es_score > pt_score and es_score > 0:
        return "es"
    return "en"

lang = detect_lang(subject)
print(f"Detected language: {lang}")

# Step 4: build the reply body
def build_reply(thread_id: str, from_email: str, subject: str, lang: str) -> str:
    """Build CEO reply in the same language as the thread."""
    if lang == "pt":
        body = f"""Prezado(a),

Agradeço pelo contato e pelo interesse em colaboração. A Zion Tech Group está sempre aberta a novos projetos e parcerias que possam gerar valor mútuo.

Como empresa, oferecemos serviços completos de transformação digital, inteligência artificial, automação de processos e implementação de soluções cloud — com foco em resultados mensuráveis para nossos clientes.

Além dos serviços proprietários, disponibilizamos ferramentas gratuitas que podem ajudar sua equipe a explorar novas capacidades sem custo inicial:
- Zion Tech Group Free Tools (ziontechgroup.com/tools) — Conjunto de utilitários open para análise, automação leve e prototipagem rápida
- AI Playground — Ambiente gratuito para testar modelos de linguagem e visão em cenários reais

Gostaria de agendar uma conversa rápida para entender suas necessidades e mostrar o que pode ser feito? Você pode 예약ar diretamente pela minha agenda:
https://calendly.com/kleber-ziontechgroup

Mais informações sobre a empresa e nossas capacidades:
https://ziontechgroup.com

Fico no aguardo.

Atenciosamente,
Kleber | CEO, Zion Tech Group
"""
    elif lang == "es":
        body = f"""Estimado(a),

Gracias por su mensaje y por su interés en una colaboración. Zion Tech Group está siempre abierta a nuevos proyectos y alianzas que puedan generar valor mutuo.

Como empresa, ofrecemos servicios completos de transformación digital, inteligencia artificial, automatización de procesos e implementación de soluciones cloud, con énfasis en resultados medibles para nuestros clientes.

Además de nuestros servicios principales, ponen a disposición herramientas gratuitas que pueden ayudar a su equipo a explorar nuevas capacidades sin costo inicial:
- Herramientas gratuitas de Zion Tech Group (ziontechgroup.com/tools) — Utilitarios de código abierto para análisis, automatización ligera y prototipado rápido
- AI Playground — Entorno gratuito para probar modelos de lenguaje y visión en escenarios reales

Me gustaría agendar una conversación rápida para entender sus necesidades y mostrar lo que podemos hacer. Puede reservar directamente en mi calendario:
https://calendly.com/kleber-ziontechgroup

Más información sobre la empresa y nuestras capacidades:
https://ziontechgroup.com

Quedo a la espera.

Saludos cordiales,
Kleber | CEO, Zion Tech Group
"""
    else:
        body = f"""Hello,

Thank you for reaching out and for your interest in collaborating. Zion Tech Group is always open to new projects and partnerships that can create mutual value.

As a company, we offer comprehensive digital transformation, artificial intelligence, process automation, and cloud solution implementation services — with a focus on measurable results for our clients.

In addition to our core services, we provide free tools that can help your team explore new capabilities at no initial cost:
- Zion Tech Group Free Tools (ziontechgroup.com/tools) — Open utilities for analysis, light automation, and rapid prototyping
- AI Playground — Free environment to test language and vision models on real-world scenarios

I would love to schedule a quick conversation to understand your needs and show what can be done. You can book directly on my calendar:
https://calendly.com/kleber-ziontechgroup

More about the company and our capabilities:
https://ziontechgroup.com

Looking forward to connecting.

Best regards,
Kleber | CEO, Zion Tech Group
"""
    return body

reply_body = build_reply(target["thread_id"], target["from"], subject, lang)

# Step 5: write the draft file
draft_content = f"""# Hot-followup CEO Reply Draft
# Generated: 2026-09-05T15:35 UTC
# Language: {lang}
# Thread ID: {target['thread_id']}
# From: {target['from']}
# Subject: {subject}
# Status: DRAFT READY — NOT SENT

---
Reply body ({lang== 'pt' and 'Portuguese' or lang == 'es' and 'Spanish' or 'English'}):

{reply_body}
---

# Send instructions:
# - To send: use gog mail send with the above body, subject = "Re: {subject}"
# - Thread ID: {target['thread_id']}
# - DO NOT send unless explicitly configured to send.
# - This draft is prepared for review; send only after manual confirmation.
"""

DRAFT_PATH.write_text(draft_content)
print(f"\nDraft written to: {DRAFT_PATH}")
print(f"Thread: {target['thread_id']}")
print(f"Language: {lang}")
print(f"Status: DRAFT READY — NOT SENT")
