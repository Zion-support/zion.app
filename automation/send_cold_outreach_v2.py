#!/usr/bin/env python3
"""Processa leads do zion_leads_free.json e envia cold outreach via gog gmail — versão corrigida."""

import json, subprocess, sys, re
from datetime import datetime, timezone
from pathlib import Path

LEADS_PATH = Path("/Users/miami2/zion.app/automation/data/zion_leads_free.json")
LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log-campaign.jsonl")
ACCOUNT = "kleber@ziontechgroup.com"

# Domínios que são agregadores/plataformas — não usar como alvo de e-mail
BLOCKED_DOMAINS = [
    "google.com", "github.com", "clutch.co", "sam.gov", "goodfirms.co",
    "linkedin.com", "facebook.com", "twitter.com",
    "verifier.me", "hunter.io", "lobster.com", "crunchbase.com",
    "angellist.com", "wellfound.com", "producthunt.com",
]

GENERIC_EMAILS = {"info@", "contact@", "hello@", "admin@", "support@", "sales@", "ceo@", "founder@", "founders@"}

def is_already_sent(email, log_path):
    """Verifica se o email foi enviado com sucesso (somente status 'sent')."""
    if not log_path.exists():
        return False
    email_lower = email.lower()
    try:
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("status") == "sent" and r.get("to", "").lower() == email_lower:
                            return True
                    except (json.JSONDecodeError, KeyError):
                        pass
    except Exception:
        pass
    return False

def is_blocked_domain(email):
    domain = email.lower().split("@")[-1] if "@" in email else ""
    return any(bd in domain for bd in BLOCKED_DOMAINS)

def extract_email(lead):
    """Extrai melhor e-mail disponível do lead, evitando domínios de agregadores."""
    candidates = []
    
    # 1) Contato proventivo explícito
    cp = lead.get("contato_proventivo") or ""
    if cp:
        candidates.append(cp)
    
    # 2) Campo email explícito
    for key in ("email", "contato", "contact"):
        val = lead.get(key, "")
        if val:
            candidates.append(val)
    
    # 3) Extrair emails que já estão nos campos de texto
    for cand in candidates:
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', str(cand))
        for e in emails:
            el = e.lower()
            if "ziontechgroup" in el:
                continue
            yield e, el
    
    # 4) Se site é dominio real (não agregador), tentar prefixos comuns
    site = lead.get("site", "") or ""
    site_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', str(site))
    if site_match:
        domain = site_match.group(1).lower()
        if not is_blocked_domain(f"test@{domain}"):
            for prefix in ["contato", "contato", "info", "sales", "founder", "founders", "diretoria", "ti", "tech"]:
                email_cand = f"{prefix}@{domain}"
                if not is_blocked_domain(email_cand):
                    yield email_cand, email_cand.lower()

def classify_service(lead):
    sr = (lead.get("servico_relevante") or "").lower()
    si = " ".join(lead.get("servicos_interesse") or []).lower()
    motivo = (lead.get("motivo") or "").lower()
    combined = f"{sr} {si} {motivo}"
    
    cyber_keywords = ["cybersecurity", "cyber", "segurança", "security", "compliance", "threat", "soc"]
    if any(k in combined for k in cyber_keywords):
        return "Cybersecurity"
    
    cloud_keywords = ["cloud", "aws", "azure", "gcp", "migração", "migration", "infraestrutura"]
    if any(k in combined for k in cloud_keywords):
        return "Cloud Cost"
    
    ai_keywords = ["ai", "automation", "automação", "chatbot", "ia", "llm", "rag", "agent"]
    if any(k in combined for k in ai_keywords):
        return "AI Automation"
    
    return "AI Automation"

def build_email(lead, service):
    empresa = lead.get("empresa", "").strip()
    
    if service == "Cybersecurity":
        assunto = f"Proteção cibernética para {empresa}"
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
        assunto = f"Otimização de custos cloud para {empresa}"
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
        assunto = f"Automação com IA para {empresa}"
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
    
    return assunto, body

def send_email(to_email, subject, body):
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

def main():
    with open(LEADS_PATH) as f:
        data = json.load(f)
    
    # Accept either a list of leads or a dict with a "leads" key
    if isinstance(data, list):
        leads = data
    else:
        leads = data.get("leads", [])
    print(f"Total leads no arquivo: {len(leads)}")
    
    results = {"total": len(leads), "enviados": 0, "falhados": 0, "pulados": 0, "detalhes": []}
    
    for i, lead in enumerate(leads):
        empresa = lead.get("empresa", f"Lead #{i+1}")
        priority = lead.get("prioridade", "media")
        
        emails = list(extract_email(lead))
        # Filtra bloqueados e genéricos ruins
        valid_emails = [(e, el) for e, el in emails if not is_blocked_domain(el)]
        
        non_generic = [(e, el) for e, el in valid_emails if not any(g in el for g in GENERIC_EMAILS)]
        
        if non_generic:
            chosen = non_generic[0]
            chosen_is_generic = False
        elif valid_emails:
            chosen = valid_emails[0]
            chosen_is_generic = True
        else:
            chosen = None
        
        if not chosen:
            results["pulados"] += 1
            results["detalhes"].append({"empresa": empresa, "status": "pulado", "motivo": "sem email disponível"})
            print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (sem email)")
            continue
        
        email_raw, email_clean = chosen
        
        if is_already_sent(email_clean, LOG_PATH):
            results["pulados"] += 1
            results["detalhes"].append({"empresa": empresa, "status": "pulado", "motivo": f"email já enviado ({email_clean})"})
            print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (duplicado: {email_clean})")
            continue
        
        if chosen_is_generic and priority != "alta":
            results["pulados"] += 1
            results["detalhes"].append({"empresa": empresa, "status": "pulado", "motivo": f"email genérico com prioridade {priority}"})
            print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (genérico + prioridade {priority})")
            continue
        
        service = classify_service(lead)
        subject, body = build_email(lead, service)
        
        print(f"[{i+1}/{len(leads)}] 📤 {empresa} → {email_clean} ({service})")
        print(f"      Subject: {subject}")
        
        status, error = send_email(email_clean, subject, body)
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "to": email_clean,
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
            results["enviados"] += 1
            # Marca como enviado no log (já feito via LOG_PATH.write_text acima)
            pass
            print(f"      ✅ Enviado")
        else:
            results["falhados"] += 1
            print(f"      ❌ Falhou: {error}")
        
        results["detalhes"].append(log_entry)
    
    print("\n" + "="*60)
    print("RESUMO DO COLD OUTREACH")
    print("="*60)
    print(f"Total de leads processados : {results['total']}")
    print(f"Enviados com sucesso        : {results['enviados']}")
    print(f"Falhados                   : {results['falhados']}")
    print(f"Pulados (sem email/contato): {results['pulados']}")
    print(f"\nLog salvo em: {LOG_PATH}")
    
    if results["falhados"] > 0:
        print("\nDetalhes dos falhados:")
        for d in results["detalhes"]:
            if d["status"] == "failed":
                print(f"  • {d['empresa']} → {d['to']}: {d.get('error', 'erro desconhecido')}")
    
    if results["pulados"] > 0:
        print("\nDetalhes dos pulados:")
        for d in results["detalhes"]:
            if d["status"] == "pulado":
                print(f"  • {d['empresa']}: {d.get('motivo', '')}")
    
    return results

if __name__ == "__main__":
    main()
