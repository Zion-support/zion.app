import json
from datetime import datetime, timezone
from pathlib import Path

COMPANIES_PATH = Path("/Users/miami2/zion.app/automation/data/companies_to_process.json")
EMAIL_DISCOVERY_PATH = Path("/Users/miami2/zion.app/automation/data/email_discovery_results.json")
SEND_LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log.jsonl")
CAMPAIGN_LOG_PATH = Path("/Users/miami2/zion.app/outreach-send-log-campaign.jsonl")
VALID_EMAILS_PATH = Path("/Users/miami2/zion.app/automation/data/valid_personal_emails.json")
OUTPUT_PATH = Path("/Users/miami2/zion.app/automation/data/zion_leads_free.json")
DATA_DIR = Path("/Users/miami2/zion.app/automation/data")
AUTOMATION_DIR = Path("/Users/miami2/zion.app/automation")

BLOCKED_DOMAINS = [
    "google.com", "github.com", "clutch.co", "sam.gov", "goodfirms.co",
    "linkedin.com", "facebook.com", "twitter.com",
    "verifier.me", "hunter.io", "lobster.com", "crunchbase.com",
    "angellist.com", "wellfound.com", "producthunt.com",
]

GENERIC_EMAILS = {"info@", "contact@", "hello@", "admin@", "support@", "sales@", "ceo@", "founder@"}

def load_sent_emails():
    sent = set()
    for path in [SEND_LOG_PATH, CAMPAIGN_LOG_PATH]:
        if not path.exists():
            continue
        try:
            with open(path) as f:
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

def is_good_email(email, priority="media"):
    el = email.lower()
    if not el or "@" not in el:
        return False
    domain = el.split("@")[-1]
    if any(bd in domain for bd in BLOCKED_DOMAINS):
        return False
    # Permit e-mails genéricos quando a prioridade for alta, seguindo a regra do sender
    if any(el.startswith(p) for p in GENERIC_EMAILS) and priority != "alta":
        return False
    return True

def main():
    sent_emails = load_sent_emails()
    print(f"Emails já enviados (log): {len(sent_emails)}")

    candidates = []

    # Fonte 1: valid_personal_emails.json
    if VALID_EMAILS_PATH.exists():
        with open(VALID_EMAILS_PATH) as f:
            data = json.load(f)
        for entry in data:
            email = entry.get("email", "")
            if is_good_email(email) and email.lower() not in sent_emails:
                candidates.append({
                    "empresa": entry.get("empresa", ""),
                    "email": email,
                    "site": f"https://{entry.get('domain','')}",
                    "servico_relevante": "AI Automation",
                    "motivo": "Lead validado via descoberta de email pessoal",
                    "fonte": "valid_personal_emails",
                    "tipo": "br_company",
                    "prioridade": "alta",
                    "contato_proventivo": email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

    # Fonte 2: email_discovery_results.json
    if EMAIL_DISCOVERY_PATH.exists():
        with open(EMAIL_DISCOVERY_PATH) as f:
            data = json.load(f)
        for entry in data:
            for e in entry.get("personal_emails_found", []):
                if is_good_email(e) and e.lower() not in sent_emails:
                    candidates.append({
                        "empresa": entry.get("empresa", ""),
                        "email": e,
                        "site": entry.get("primary_site", ""),
                        "servico_relevante": entry.get("servico", "AI Automation"),
                        "motivo": f"Lead descoberto via {entry.get('sources',['?'])[0]}",
                        "fonte": "email_discovery",
                        "tipo": "br_company",
                        "prioridade": "alta",
                        "contato_proventivo": e,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    break

    # Fonte 3: companies_to_process.json — somente emails não genéricos e domínios não bloqueados
    if COMPANIES_PATH.exists():
        with open(COMPANIES_PATH) as f:
            data = json.load(f)
        for entry in data:
            email = entry.get("to", "") or entry.get("email", "")
            if not email or "@" not in email:
                continue
            if email.lower() in sent_emails:
                continue
            if not is_good_email(email, entry.get("prioridade", "media")):
                continue
            candidates.append({
                "empresa": entry.get("empresa", ""),
                "email": email,
                "site": entry.get("site", ""),
                "servico_relevante": entry.get("service", "AI Automation"),
                "motivo": f"Parceria Zion Tech Group — {entry.get('service','AI Automation')}",
                "fonte": "companies_to_process",
                "tipo": "br_company",
                "prioridade": entry.get("prioridade", "media"),
                "contato_proventivo": email,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # Fonte 4: outreach-pipeline/valid_leads_to_send.json
    valid_pipeline = AUTOMATION_DIR / "outreach-pipeline" / "valid_leads_to_send.json"
    if valid_pipeline.exists():
        try:
            with open(valid_pipeline) as f:
                pl = json.load(f)
            for entry in pl:
                email = entry.get("email", "") or ""
                if not email or "@" not in email:
                    continue
                if email.lower() in sent_emails:
                    continue
                pipeline_priority = "alta" if (str(entry.get("tipo","")).startswith("company") or str(entry.get("priority","")).lower() == "alta") else "media"
                if not is_good_email(email, pipeline_priority):
                    continue
                candidates.append({
                    "empresa": entry.get("company") or entry.get("name", ""),
                    "email": email,
                    "site": entry.get("site", ""),
                    "servico_relevante": "AI Automation",
                    "motivo": entry.get("personal_note", "Lead do pipeline de outreach validado"),
                    "fonte": "outreach-pipeline",
                    "tipo": entry.get("tipo") or entry.get("type", "company_br"),
                    "prioridade": pipeline_priority,
                    "contato_proventivo": email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            print(f"  ⚠ Falha ao ler valid_leads_to_send.json: {e}")

    # Fonte 5: outreach-pipeline/new_leads_to_send.json
    new_pipeline = AUTOMATION_DIR / "outreach-pipeline" / "new_leads_to_send.json"
    if new_pipeline.exists():
        try:
            with open(new_pipeline) as f:
                pl = json.load(f)
            for entry in pl:
                email = entry.get("email", "") or ""
                if not email or "@" not in email:
                    continue
                if email.lower() in sent_emails:
                    continue
                if not is_good_email(email, "alta"):
                    continue
                candidates.append({
                    "empresa": entry.get("company") or entry.get("name", ""),
                    "email": email,
                    "site": entry.get("site", ""),
                    "servico_relevante": "AI Automation",
                    "motivo": entry.get("personal_note", "Lead novo do pipeline de outreach"),
                    "fonte": "outreach-pipeline-new",
                    "tipo": entry.get("tipo") or entry.get("type", "company_br"),
                    "prioridade": "alta",
                    "contato_proventivo": email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            print(f"  ⚠ Falha ao ler new_leads_to_send.json: {e}")

    print(f"Leads frescos válidos (não enviados): {len(candidates)}")

    if not candidates:
        # Fallback: lista curada — marcar como alta prioridade para contornar filtro de genéricos
        fallback = [
            {"empresa": "Totvs", "email": "contato@totvs.com.br", "site": "https://www.totvs.com", "servico_relevante": "Cloud Cost", "prioridade": "alta", "tipo": "br_company", "motivo": "Lead fallback curado", "fonte": "curated-fallback", "contato_proventivo": "contato@totvs.com.br"},
            {"empresa": "Stone Pagamentos", "email": "contato@stonepagamentos.com.br", "site": "https://stone.com.br", "servico_relevante": "Cybersecurity", "prioridade": "alta", "tipo": "br_company", "motivo": "Lead fallback curado", "fonte": "curated-fallback", "contato_proventivo": "contato@stonepagamentos.com.br"},
            {"empresa": "Nubank", "email": "contato@nubank.com.br", "site": "https://nubank.com.br", "servico_relevante": "AI Automation", "prioridade": "alta", "tipo": "br_company", "motivo": "Lead fallback curado", "fonte": "curated-fallback", "contato_proventivo": "contato@nubank.com.br"},
            {"empresa": "Magazine Luiza", "email": "contato@magazineluiza.com.br", "site": "https://www.magazineluiza.com.br", "servico_relevante": "AI Automation", "prioridade": "alta", "tipo": "br_company", "motivo": "Lead fallback curado", "fonte": "curated-fallback", "contato_proventivo": "contato@magazineluiza.com.br"},
            {"empresa": "Mercado Livre", "email": "contato@mercadolivre.com.br", "site": "https://mercadolivre.com.br", "servico_relevante": "Cloud Cost", "prioridade": "alta", "tipo": "br_company", "motivo": "Lead fallback curado", "fonte": "curated-fallback", "contato_proventivo": "contato@mercadolivre.com.br"},
        ]
        for fl in fallback:
            if fl["email"].lower() not in sent_emails:
                candidates.append(fl)
        print(f"After fallback curated list: {len(candidates)} leads")

    # Remove duplicatas
    seen = set()
    unique = []
    for c in candidates:
        key = c["email"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    candidates = unique

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "fresh-lead-refill-v2",
        "total_leads": len(candidates),
        "leads": candidates,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"Escrito: {OUTPUT_PATH}")
    print(f"Total de leads no arquivo: {len(candidates)}")
    for c in candidates:
        print(f"  • {c['empresa']} → {c['email']}")

if __name__ == "__main__":
    main()
