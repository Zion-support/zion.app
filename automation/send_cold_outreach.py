#!/usr/bin/env python3
"""Processa leads do zion_leads_free.json e envia cold outreach via gog gmail."""

import json, subprocess, sys, re
from datetime import datetime, timezone
from pathlib import Path

LEADS_PATH = Path("/Users/miami2/zion.app/automation/data/zion_leads_free.json")
LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log.jsonl")
ACCOUNT = "kleber@ziontechgroup.com"

GENERIC_EMAILS = {"info@", "contact@", "hello@", "admin@", "support@", "sales@", "CEO@", "ceo@", "founder@", "founders@", "hello@", "team@"}

EXCLUDE_DOMAINS = ["ziontechgroup.com"]

ALREADY_SENT = set()
if LOG_PATH.exists():
    for line in LOG_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                r = json.loads(line)
                ALREADY_SENT.add(r["to"].lower())
            except:
                pass

def extract_email(lead):
    """Extrai melhor e-mail disponível do lead."""
    candidates = []
    for key in ("contato_proventivo", "email", "contato", "contact"):
        val = lead.get(key, "")
        if val:
            candidates.append(val)
    # Also search site for common patterns
    site = lead.get("site", "") or lead.get("site", "")
    candidates.append(site)
    
    for cand in candidates:
        # Extract email patterns
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', str(cand))
        for e in emails:
            el = e.lower()
            # Skip ziontechgroup.com
            if any(d in el for d in EXCLUDE_DOMAINS):
                continue
            # Skip generic if we have better options later
            yield e, el
    
    # If site looks like a domain, try common prefixes
    site_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', str(site))
    if site_match:
        domain = site_match.group(1).lower()
        for prefix in ["contato", "info", "sales", "founder", "founders", "hello", "support", "admin", "diretoria"]:
            yield f"{prefix}@{domain}", f"{prefix}@{domain}"

def classify_service(lead):
    """Classifica qual serviço principal oferecer."""
    sr = (lead.get("servico_relevante") or "").lower()
    si = " ".join(lead.get("servicos_interesse") or []).lower()
    motivo = (lead.get("motivo") or "").lower()
    combined = f"{sr} {si} {motivo}"
    
    # Prioridade: Cybersecurity se mencionado
    cyber_keywords = ["cybersecurity", "cyber", "security", "segurança", "compliance", "threat", "soc"]
    if any(k in combined for k in cyber_keywords):
        return "Cybersecurity"
    
    # Depois Cloud Cost / Migration
    cloud_keywords = ["cloud", "aws", "azure", "gcp", "migração", "migration", "infraestrutura"]
    if any(k in combined for k in cloud_keywords):
        return "Cloud Cost"
    
    # AI Automation
    ai_keywords = ["ai", "automation", "automação", "chatbot", "ia", "llm", "rag", "agent"]
    if any(k in combined for k in ai_keywords):
        return "AI Automation"
    
    return "AI Automation"  # padrão

def build_email(lead, service):
    """Monta e-mail curto personalizado (<150 palavras)."""
    empresa = lead.get("empresa", "").strip()
    site = lead.get("site", "").strip()
    motivo = lead.get("motivo", "")[:200]
    
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
• Implementam Custos FinOps com dashboards e alertas
• Planejam migração de workloads com redução de 20-40% nos custos
• Negociam com provedores e implementam reserved instances

Se gestão de custos cloud é uma dor atual, podemos agendar uma conversa rápida.

Atenciosamente,
 Kleber | Zion Tech Group
 kleber@ziontechgroup.com"""
    else:  # AI Automation
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
    
    # Trim to <150 words
    words = body.split()
    if len(words) > 150:
        body = " ".join(words[:150]) + "..."
    
    return assunto, body

def send_email(to_email, subject, body):
    """Envia e-mail via gog gmail send. Retorna (status, error)."""
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
            try:
                data = json.loads(result.stdout)
                if data.get("id"):
                    return "sent", None
            except:
                pass
            if "sent" in result.stdout.lower() or result.stdout.strip():
                return "sent", None
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
    
    leads = data.get("leads", [])
    print(f"Total leads no arquivo: {len(leads)}")
    
    results = {
        "total": len(leads),
        "enviados": 0,
        "falhados": 0,
        "pulados": 0,
        "detalhes": []
    }
    
    # Process each lead
    for i, lead in enumerate(leads):
        empresa = lead.get("empresa", f"Lead #{i+1}")
        priority = lead.get("prioridade", "media")
        
        # Extract best email
        emails = list(extract_email(lead))
        # Filter: prefer non-generic
        non_generic = [(e, el) for e, el in emails if not any(g in el for g in GENERIC_EMAILS)]
        if non_generic:
            chosen = non_generic[0]
        elif emails:
            chosen = emails[0]
        else:
            chosen = None
        
        if not chosen:
            results["pulados"] += 1
            results["detalhes"].append({
                "empresa": empresa,
                "status": "pulado",
                "motivo": "sem email disponível"
            })
            print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (sem email)")
            continue
        
        email_raw, email_clean = chosen
        
        # Check duplicates
        if email_clean in ALREADY_SENT:
            results["pulados"] += 1
            results["detalhes"].append({
                "empresa": empresa,
                "status": "pulado",
                "motivo": f"email já enviado anteriormente ({email_clean})"
            })
            print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (duplicado: {email_clean})")
            continue
        
        # Filter generic emails
        is_generic = any(g in email_clean for g in GENERIC_EMAILS)
        if is_generic:
            # Only send generic if it's the only option and high priority
            if priority != "alta":
                results["pulados"] += 1
                results["detalhes"].append({
                    "empresa": empresa,
                    "status": "pulado",
                    "motivo": f"email genérico ({email_clean}) com prioridade {priority}"
                })
                print(f"[{i+1}/{len(leads)}] ⏭ {empresa} — pulado (genérico + prioridade {priority})")
                continue
        
        # Classify and build email
        service = classify_service(lead)
        subject, body = build_email(lead, service)
        
        print(f"[{i+1}/{len(leads)}] 📤 {empresa} → {email_clean} ({service})")
        print(f"      Subject: {subject}")
        
        # Send
        status, error = send_email(email_clean, subject, body)
        
        # Log
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
            ALREADY_SENT.add(email_clean)
            print(f"      ✅ Enviado")
        else:
            results["falhados"] += 1
            print(f"      ❌ Falhou: {error}")
        
        results["detalhes"].append(log_entry)
    
    # Summary
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
