#!/usr/bin/env python3
"""
Reseed: pega leads potenciais descobertos pelo Gmail scan e insere na fila de envio.

Fluxo:
1. Roda varredura Gmail (scan_inbox do run_outreach_scan)
2. Extrai leads potenciais (exclui duplicados, domínios bloqueados, já enviados)
3. Formata e insere no zion_leads_free.json
4. Reporta:_added, skipped, queue_size, errors
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/Users/miami2/zion.app/automation")
LEADS_PATH = WORKSPACE / "data" / "zion_leads_free.json"
SEND_LOG = Path("/Users/miami2/zion.app/outreach-send-log.jsonl")

# Domínios bloqueados (espelha send_cold_outreach_v2.py)
BLOCKED_DOMAINS = [
    "google.com", "github.com", "clutch.co", "sam.gov", "goodfirms.co",
    "linkedin.com", "facebook.com", "twitter.com",
    "verifier.me", "hunter.io", "lobster.com", "crunchbase.com",
    "angellist.com", "wellfound.com", "producthunt.com",
    # **NÃO bloquear** domínios comuns de empresas reais — apenas domínios
    # de provedores de e-mail/web que geram falsos positivos.
]

LEAD_HINTS = [
    'lead', 'opportunity', 'proposal', 'quote', 'project', 'collab',
    'partnership', 'solicitacao', 'orcamento', 'proposta', 'servico',
    'previsao', 'cliente', 'negocio', 'parceria',
    'do you offer', 'can you help', 'looking for', 'interested in',
    'pricing', 'available', 'capacity', 'quote request'
]

SKIP_DOMAINS = ['github.com', 'linkedin.com', 'bot', 'noreply', 'notification',
                'facebook', 'twitter', 'reddit', 'quora', 'medium.com',
                'newsletter', 'digest', 'alert', 'updated', 'merged',
                'closed', 'forked', 'automated', 'system']


def extract_email(from_field):
    m = re.search(r'<([^>]+)>', from_field)
    if m:
        return m.group(1)
    m2 = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', from_field)
    if m2:
        return m2.group(0)
    return None


def is_blocked_domain(email):
    if not email:
        return True
    domain = email.lower().split('@')[-1]
    return any(bd in domain for bd in BLOCKED_DOMAINS)


def is_skip_domain(email):
    if not email:
        return True
    email_lower = email.lower()
    for d in SKIP_DOMAINS:
        if d in email_lower:
            return True
    return False


def get_sent_emails():
    """Retorna set de emails já enviados (status=sent)."""
    sent = set()
    if not SEND_LOG.exists():
        return sent
    try:
        with open(SEND_LOG) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("status") == "sent":
                            sent.add(r.get("to", "").lower())
                    except (json.JSONDecodeError, KeyError):
                        pass
    except Exception:
        pass
    return sent


def load_existing_queue():
    """Carrega filas existentes de zion_leads_free.json."""
    if not LEADS_PATH.exists():
        return []
    try:
        with open(LEADS_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("leads", [])
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def run_gmail_scan():
    """Roda varredura Gmail e retorna lista de leads potenciais."""
    try:
        proc = subprocess.run(
            ['gog', 'gmail', 'search', 'in:anywhere', '--max', '500',
             '--plain', '--no-input'],
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            return None, f"gog erro: {proc.stderr.strip()}"
        lines = proc.stdout.strip().split('\n')
        if not lines or lines == ['']:
            return [], None
    except subprocess.TimeoutExpired:
        return None, "gog search timed out (120s)"
    except FileNotFoundError:
        return None, "gog CLI não encontrado"

    potential = []
    seen_ids = set()

    for line in lines:
        parts = line.split('\t')
        if len(parts) < 4:
            continue
        email_id, date, from_field, subject = parts[0], parts[1], parts[2], parts[3]

        if email_id in seen_ids:
            continue
        seen_ids.add(email_id)

        email = extract_email(from_field)
        if not email or is_skip_domain(email) or is_blocked_domain(email):
            continue

        text = f'{from_field} {subject}'.lower()
        if not any(hint in text for hint in LEAD_HINTS):
            continue

        potential.append({
            'id': email_id,
            'date': date,
            'from': from_field,
            'email': email,
            'subject': subject[:200],
        })

    return potential, None


def build_lead_from_scan_potential(client):
    """Converte um lead do scan Gmail para formato da fila de envio."""
    email = client['email']
    domain_match = re.search(r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email)
    domain = domain_match.group(1) if domain_match else ''

    # Determina serviço relevante pelo subject
    subject_lower = client['subject'].lower()
    if any(k in subject_lower for k in ['cyber', 'security', 'seguranca', 'protecao']):
        servico = "Cybersecurity"
    elif any(k in subject_lower for k in ['cloud', 'aws', 'azure', 'migration', 'migracao']):
        servico = "Cloud Migration & FinOps"
    elif any(k in subject_lower for k in ['ai', 'automation', 'chatbot', 'ia', 'llm', 'agent']):
        servico = "AI Automation"
    else:
        servico = "AI Automation"

    # Gera motivo
    motivo = f"Olá, analisei seu e-mail sobre: {client['subject'][:120]}"

    empresa = client['from'].split('<')[0].strip() if '<' in client['from'] else domain or 'Contato'

    return {
        "empresa": empresa[:100],
        "email": email,
        "site": f"https://{domain}" if domain else "",
        "servico_relevante": servico,
        "motivo": motivo,
        "fonte": "gmail-scan-reseed",
        "tipo": "email_inbound_lead",
        "prioridade": "alta",
        "contato_proventivo": email,
    }


def main():
    print("=" * 60)
    print("ZION OUTREACH RESEED")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    errors = []

    # 1. Varredura Gmail
    print("\n[1] Varredura Gmail (in:anywhere)...")
    clients, scan_err = run_gmail_scan()

    if scan_err:
        print(f"  ❌ ERRO: {scan_err}")
        errors.append(scan_err)
        # Mesmo com erro, reporta o estado atual
        existing = load_existing_queue()
        print(f"\n{'='*60}")
        print(f"RESUMO DO RESEED")
        print(f"{'='*60}")
        print(f"added: 0")
        print(f"skipped: 0 (erro de scan: {scan_err})")
        print(f"queue_size: {len(existing)}")
        print(f"errors: {errors}")
        return

    print(f"  📧 Total escaneados: ~500")
    print(f"  🔍 Leads potenciais encontrados: {len(clients)}")

    for c in clients:
        print(f"    - {c['email']} | {c['subject'][:70]}")

    # 2. Filtra já enviados
    sent_emails = get_sent_emails()
    print(f"\n[2] Filtragem...")
    print(f"  📋 Emails já enviados: {len(sent_emails)}")

    new_clients = []
    skipped = 0

    if clients:
        for c in clients:
            email_lower = c['email'].lower()
            if email_lower in sent_emails:
                skipped += 1
                print(f"  ⏭  Já enviado: {c['email']}")
                continue
            new_clients.append(c)

    print(f"  ✅ Novos (não enviados): {len(new_clients)}")

    # 3. Constrói leads para fila
    print(f"\n[3] Construindo leads para fila...")
    new_leads = []
    for c in new_clients:
        try:
            lead = build_lead_from_scan_potential(c)
            new_leads.append(lead)
            print(f"  ➕ {lead['empresa']} → {lead['email']} ({lead['servico_relevante']})")
        except Exception as e:
            errors.append(f"Erro ao construir lead para {c['email']}: {e}")
            print(f"  ❌ Erro: {c['email']} — {e}")

    # 4. Merge com fila existente
    print(f"\n[4] Merge com fila existente...")
    existing = load_existing_queue()
    print(f"  📂 Leads existentes na fila: {len(existing)}")

    # Deduplica por email
    existing_emails = {l.get('email', '').lower() for l in existing if l.get('email')}
    merged = list(existing)

    for lead in new_leads:
        email_lower = lead['email'].lower()
        if email_lower in existing_emails:
            print(f"  ⏭  Duplicado (já na fila): {lead['email']}")
            continue
        merged.append(lead)
        existing_emails.add(email_lower)

    # 5. Salva
    print(f"\n[5] Salvando fila atualizada...")
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "gmail-scan-reseed",
        "total_leads": len(merged),
        "leads": merged,
    }

    LEADS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_PATH, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  💾 Fila salva: {LEADS_PATH}")
    print(f"  📊 Total na fila: {len(merged)}")

    added = len(merged) - len(existing)
    print(f"\n{'='*60}")
    print(f"RESUMO DO RESEED")
    print(f"{'='*60}")
    print(f"added: {added}")
    print(f"skipped: {skipped} (already sent)")
    print(f"queue_size: {len(merged)}")
    if errors:
        print(f"errors: {errors}")
    else:
        print(f"errors: none")

    # Mostra novos leads
    if new_leads:
        print(f"\nNovos leads adicionados:")
        for l in new_leads:
            print(f"  • {l['empresa']} | {l['email']} | {l['servico_relevante']}")


if __name__ == '__main__':
    main()
