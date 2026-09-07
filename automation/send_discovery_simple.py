#!/usr/bin/env python3
"""Envia os 17 leads discovery diretamente — versão autocontida"""
import json, subprocess, sys, os
from datetime import datetime, timezone
from pathlib import Path

LEADS_PATH = Path("/Users/miami2/zion.app/automation/data/zion_leads_free.json")
LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log.jsonl")
ACCOUNT = "kleber@ziontechgroup.com"

BLOCKED = ["google.com", "github.com", "clutch.co", "sam.gov", "goodfirms.co",
           "linkedin.com", "facebook.com", "twitter.com", "x.com",
           "verifier.me", "hunter.io", "lobster.com", "crunchbase.com",
           "angellist.com", "wellfound.com", "producthunt.com"]

ALREADY_SENT = set()
if LOG_PATH.exists():
    for line in LOG_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                r = json.loads(line)
                ALREADY_SENT.add(r["to"].lower())
            except: pass

with open(LEADS_PATH) as f:
    leads = json.load(f)

def _build_email(empresa, service):
    if service == "Cybersecurity":
        subject = f"Proteção cibernética para {empresa}"
        body = f"""Olá, analisei o perfil da {empresa} e identifiquei uma oportunidade relevante em Cybersecurity.

{empresa} opera com dados e sistemas que merecem proteção de nível enterprise. A Zion Tech Group ajuda organizações como a sua a:
• Implementar monitoramento de ameaças 24/7 e resposta a incidentes
• Cumprir frameworks como ISO 27001, NIST e LGPD
• Proteger dados sensíveis com arquiteturas zero-trust
• Reduzir riscos com auditorias e treinamentos

Se segurança cibernética está na sua radar, posso agendar uma conversa rápida para entender suas prioridades atuais.

Atenciosamente,
 Kleber | Zion Tech Group
 kleber@ziontechgroup.com"""
    elif service == "Cloud Cost":
        subject = f"Otimização de custos cloud para {empresa}"
        body = f"""Olá, analisei o perfil da {empresa} e identifiquei uma oportunidade relevante em Cloud Cost Optimization.

Muitas empresas estão pagando mais por infraestrutura cloud do que o necessário. A Zion Tech Group ajuda organizações como a {empresa} a:
• Auditam e otimizam instâncias, armazenamento e data transfer
• Implementam FinOps com dashboards e alertas de custo
• Planejam migração de workloads com redução de 20-40% nos custos
• Negociam com provedores e implementam reserved instances

Se gestão de custos cloud é uma dor atual, podemos agendar uma conversa rápida.

Atenciosamente,
 Kleber | Zion Tech Group
 kleber@ziontechgroup.com"""
    else:
        subject = f"Automação com IA para {empresa}"
        body = f"""Olá, analisei o perfil da {empresa} e identifiquei uma oportunidade relevante em AI Automation.

A {empresa} tem processos que podem ser potencializados com automação inteligente. A Zion Tech Group ajuda organizações como a sua a:
• Criar chatbots e assistentes de IA para atendimento e operações
• Automatizar pipelines de dados e análises com IA generativa
• Implementar RAG e agentes para recuperação e processamento de conhecimento
• Integrar IA em fluxos existentes sem refatoração completa

Se automação com IA é uma prioridade, posso agendar uma conversa rápida para explorar juntos.

Atenciosamente,
 Kleber | Zion Tech Group
 kleber@ziontechgroup.com"""
    words = body.split()
    if len(words) > 150:
        body = " ".join(words[:150]) + "..."
    return subject, body

def _send_email(to_email, subject, body):
    cmd = [
        "gog", "gmail", "send",
        "--to", to_email,
        "--subject", subject,
        "--body", body,
        "--account", ACCOUNT,
        "--no-input",
        "--json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return "sent", None
        else:
            err = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            return "failed", err
    except subprocess.TimeoutExpired:
        return "failed", "timeout"
    except Exception as e:
        return "failed", str(e)

print(f"Total leads: {len(leads)}")
print(f"Já enviados: {len(ALREADY_SENT)}")
print()

enviados = 0
falhados = 0
pulados = 0

for i, lead in enumerate(leads):
    empresa = lead.get("empresa", f"Lead #{i+1}")
    email = lead.get("contato_proventivo", lead.get("email", ""))
    if not email:
        pulados += 1
        print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — sem email")
        continue
    el = email.lower()
    if el in ALREADY_SENT:
        pulados += 1
        print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — duplicado ({el})")
        continue
    dominio = el.split("@")[-1] if "@" in el else ""
    if any(bd in dominio for bd in BLOCKED):
        pulados += 1
        print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — domínio bloqueado ({dominio})")
        continue
    service = lead.get("servico_relevante", "AI Automation")
    subject, body = _build_email(empresa, service)
    print(f"[{i+1}/{len(leads)}] 📤 {empresa} → {el} ({service})")
    status, error = _send_email(el, subject, body)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "to": el,
        "empresa": empresa,
        "subject": subject,
        "service": service,
        "status": status,
        "error": error
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    if status == "sent":
        enviados += 1
        ALREADY_SENT.add(el)
        print(f"      ✅ Enviado")
    else:
        falhados += 1
        print(f"      ❌ Falhou: {error}")

print()
print("=" * 60)
print("RESUMO DO COLD OUTREACH (DISCOVERY LEADS)")
print("=" * 60)
print(f"Total de leads processados : {len(leads)}")
print(f"Enviados com sucesso       : {enviados}")
print(f"Falhados                  : {falhados}")
print(f"Pulados                   : {pulados}")
print(f"Log salvo em: {LOG_PATH}")
