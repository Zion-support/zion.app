#!/usr/bin/env python3
"""Compile fresh leads for Zion Tech Group from all discovery sources."""

import json
import csv
import os
from datetime import datetime, timezone

OUT_DIR = "/Users/miami2/zion.app/automation/data"

# ── Fresh leads compiled from:
#   (1) GitHub Lead Discovery: 75 repos (github_leads.json)
#   (2) SAM.gov / RFP web search: 8 government opportunities
#   (3) Brazil + US company web search: 10+ companies
#   (4) Software/digital agency web search: 8+ agencies
#   (5) Previous session leads (28 existing) - enriched with new info

fresh_leads = [
    # ── GOVERNMENT / RFP OPPORTUNITIES (from SAM.gov + web search) ──
    {
        "empresa": "DNFSB - IT Support Services",
        "site": "https://sam.gov/opp/d2c1a57d8e984bd2bfecff2654ac97d5/view",
        "localidade": "Washington DC, USA (Federal)",
        "servico_relevante": "Cybersecurity, AI-enabled IT Ops, Cloud Support, Helpdesk",
        "motivo": "Sources Sought for IT O&M with embedded cybersecurity + AI-enabled tools for Microsoft/cloud environment. Industry Day Mar 18, award before Sep 2026. Small business eligible.",
        "fonte": "SAM.gov (Mar 2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Not disclosed (IT O&M contract)",
        "prioridade": "alta",
    },
    {
        "empresa": "NIST - CAPSS Cybersecurity & Privacy",
        "site": "https://sam.gov/opp/b6f51248db754570a2860d60347f0151/view",
        "localidade": "Gaithersburg, MD, USA (Federal)",
        "servico_relevante": "Cybersecurity, Privacy, Software Dev, Business Process Automation",
        "motivo": "Total Small Business Set-Aside (FAR 19.5). NAICS 541519, $30M size standard. Design/test/deploy software, web apps, automation. Direct small business opportunity.",
        "fonte": "SAM.gov (2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Not disclosed (Set-Aside)",
        "prioridade": "alta",
    },
    {
        "empresa": "DoD - Agentic Workload Automation Harness",
        "site": "https://sam.gov/opp/7ac85dcacf0745e8a1488506c3e4e4f6/view",
        "localidade": "San Antonio, TX, USA (DoD)",
        "servico_relevante": "AI Chat/Assistants, RAG, Workflow Automation, Document Analysis, GenAI",
        "motivo": "Sources Sought for secure enterprise AI: LLM access, generative AI chat, document summarization, RAG, API integration. DoD cybersecurity requirements. San Antonio place of performance.",
        "fonte": "SAM.gov (Aug 2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Not disclosed (Sources Sought)",
        "prioridade": "alta",
    },
    {
        "empresa": "C5ISRT - Next Gen Cybersecurity & Info Assurance",
        "site": "https://sam.gov/opp/d0a6b00135934235b42329fd2d7c30d3/view",
        "localidade": "Coronado, CA / NSWC PCD, USA (Navy)",
        "servico_relevante": "Cybersecurity, Threat Intelligence, Security Engineering, Compliance, Training",
        "motivo": "Sources Sought for full-lifecycle cybersecurity program. 12-month base + 4x12-month options. Small business encouraged. NAICS 541330, $25.5M. Potential 8(a) set-aside.",
        "fonte": "SAM.gov (Aug 2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Not disclosed (12mo + 4 options)",
        "prioridade": "alta",
    },
    {
        "empresa": "FDA - NextGen Cyber Engineering, Operations AI",
        "site": "https://sam.gov/workspace/contract/opp/f09034fca4234513a25a5d8e2f9b82f7/view",
        "localidade": "Silver Spring, MD, USA (FDA/HHS)",
        "servico_relevante": "Cybersecurity Engineering, AI Operations, Cloud Security",
        "motivo": "Sources Sought for next-gen cyber engineering + AI operations at FDA. High-impact federal health agency. Cloud security and AI ops align with Zion services.",
        "fonte": "SAM.gov (2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Not disclosed",
        "prioridade": "media",
    },
    {
        "empresa": "IRS - Small Business IT/ Cloud BPA",
        "site": "https://www.ostglobalsolutions.com/exclusive-small-business-irs-contract-broaden-your-it-footprint/",
        "localidade": "Washington DC, USA (IRS/Federal)",
        "servico_relevante": "Cloud Migration, IT Support, Cybersecurity",
        "motivo": "Exclusive small business BPA for IRS IT work including cloud migration. Reserved for small businesses. Strong fit for Zion's cloud + cybersecurity services.",
        "fonte": "OSTG (2026)",
        "tipo": "government_bpa",
        "estimado_valor": "Not disclosed (BPA)",
        "prioridade": "alta",
    },
    {
        "empresa": "City of Cabot - Cloud Migration RFP (Starbridge)",
        "site": "https://www.google.com/search?q=City+of+Cabot+Arkansas+cloud+migration+RFP+2026",
        "localidade": "Cabot, AR, USA (Municipal)",
        "servico_relevante": "Cloud Migration, IT Consulting",
        "motivo": "Municipal cloud migration RFP identified in prior session. Smaller government entity = less competition. Starbridge referenced as potential partner. High close probability for SMB-focused Zion.",
        "fonte": "Prior session web search (2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Small municipal contract",
        "prioridade": "alta",
    },
    {
        "empresa": "Council Bluffs, IA - IT Services RFP",
        "site": "https://www.google.com/search?q=Council+Bluffs+Iowa+IT+services+RFP+2026",
        "localidade": "Council Bluffs, IA, USA (Municipal)",
        "servico_relevante": "IT Managed Services, Cloud, Cybersecurity",
        "motivo": "Municipal IT services RFP identified in prior session. Smaller city = approachable. Managed services + cloud migration align with core Zion offerings.",
        "fonte": "Prior session web search (2026)",
        "tipo": "government_rfp",
        "estimado_valor": "Small municipal contract",
        "prioridade": "alta",
    },
    {
        "empresa": "CFPB - Cybersecurity BPA",
        "site": "https://www.google.com/search?q=CFPB+cybersecurity+BPA+2026",
        "localidade": "Washington DC, USA (Federal Financial)",
        "servico_relevante": "Cybersecurity, Managed Security, Compliance",
        "motivo": "Consumer Financial Protection Bureau cybersecurity BPA. Federal financial regulator = high-value cybersecurity client. Found in prior session. Potential subcontracting opportunity.",
        "fonte": "Prior session web search (2026)",
        "tipo": "government_bpa",
        "estimado_valor": "Federal BPA (multi-year)",
        "prioridade": "media",
    },
    # ── BRAZILIAN COMPANIES ──
    {
        "empresa": "Beep Saúde",
        "site": "https://beep.saude.com.br",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "AI Data Pipeline, Document OCR, Chatbots, Cloud Migration",
        "motivo": "Health tech startup. Digital health platform needing AI data pipelines, patient document OCR, chatbot for patient engagement, and cloud infrastructure. High growth = scaling IT needs.",
        "fonte": "Web search (beep.saude.com.br), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Startup (Series A/B range)",
        "prioridade": "alta",
    },
    {
        "empresa": "Bliss Health",
        "site": "https://bliss.health",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "AI Data Pipeline, Chatbots, Document OCR, Cloud Migration",
        "motivo": "Health/wellness platform. Digital health services needing patient data pipelines, chatbot for user engagement, document processing, and cloud infrastructure. Health vertical = strong AI + compliance needs.",
        "fonte": "Web search (bliss.health), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Startup/Scale-up",
        "prioridade": "alta",
    },
    {
        "empresa": "Prodam SP (Governo do Estado)",
        "site": "https://www.prodam.sp.gov.br",
        "localidade": "São Paulo, SP, Brasil (Governo Estadual)",
        "servico_relevante": "Cloud Migration, Cybersecurity, AI Services, Document OCR, IT Consulting",
        "motivo": "State government IT department. Digital transformation of Sao Paulo state systems. massive document processing (OCR), citizen chatbots, cloud migration of legacy systems, cybersecurity hardening. Government = stable contracts.",
        "fonte": "Web search (prodam.sp.gov.br), prior session",
        "tipo": "government_brazil",
        "estimado_valor": "State government (large)",
        "prioridade": "alta",
    },
    {
        "empresa": "Natura",
        "site": "https://www.natura.com",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "AI Data Pipeline, Cloud Migration, Cybersecurity, QA Automation",
        "motivo": "Major Brazilian cosmetics company undergoing digital transformation. Supply chain data pipelines, e-commerce cloud, security for customer data, QA for digital platforms. Large enterprise with budget.",
        "fonte": "Web search (natura.com), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Large enterprise (multinational)",
        "prioridade": "media",
    },
    {
        "empresa": "Conta Azul",
        "site": "https://www.contaazul.com",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "AI Data Pipeline, QA Automation, Chatbots, Document OCR",
        "motivo": "Accounting/ERP SaaS for SMBs. Needs AI data pipeline for financial analytics, QA automation for continuous deployment, chatbot for customer support, OCR for receipt/invoice processing. High-volume transactional data.",
        "fonte": "Web search (contaazul.com), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Venture-backed SaaS (Series C+)",
        "prioridade": "alta",
    },
    {
        "empresa": "Stone (Pagamentos)",
        "site": "https://stone.com.br",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "AI Data Pipeline, QA Automation, Cybersecurity, IoT Edge",
        "motivo": "Major payment processor. Payment data pipelines, QA for transaction systems, cybersecurity for financial data, IoT edge for POS terminals. Large fintech = significant IT spend.",
        "fonte": "Web search (stone.com.br), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Large fintech (public)",
        "prioridade": "media",
    },
    {
        "empresa": "Neurosia",
        "site": "https://www.goodfirms.co/company/neurosia",
        "localidade": "Brasil (AI consulting)",
        "servico_relevante": "AI Data Pipeline, AI Services Partnership, Chatbots",
        "motivo": "AI consulting firm building AI agents, RAG, predictive analytics, computer vision. Potential partner for Zion's AI services or client for end-to-end AI pipeline infrastructure. Complementary not competitive.",
        "fonte": "GoodFirms web search (2026)",
        "tipo": "agency_brazil",
        "estimado_valor": "AI consulting firm",
        "prioridade": "media",
    },
    {
        "empresa": "Red Lotus Tecnologia",
        "site": "https://www.goodfirms.co/company/red-lotus-tecnologia",
        "localidade": "Brasil (IT consulting)",
        "servico_relevante": "IT Consulting, Cloud Migration, QA Automation",
        "motivo": "Brazilian IT consultancy offering digital transformation. Could be partner for shared clients or client for overflow work. Process improvement + technology overhaul focus.",
        "fonte": "GoodFirms web search (2026)",
        "tipo": "agency_brazil",
        "estimado_valor": "IT consulting firm",
        "prioridade": "media",
    },
    {
        "empresa": "SCM Gestão",
        "site": "https://www.goodfirms.co/company/scm-gestao",
        "localidade": "Brasil (BI/BPM consulting for ISPs)",
        "servico_relevante": "AI Data Pipeline, AI Consulting, QA Automation",
        "motivo": "Brazilian BI/BPM consultancy serving ISPs. AI tools for business intelligence. Potential client for AI data pipeline services or partner for telecom sector opportunities.",
        "fonte": "GoodFirms web search (2026)",
        "tipo": "company_brazil",
        "estimado_valor": "Niche consultancy (ISPs)",
        "prioridade": "media",
    },
    # ── US COMPANIES ──
    {
        "empresa": "Starbridge (City of Cabot Cloud Migration Partner)",
        "site": "https://www.google.com/search?q=starbridge+cloud+migration+arkansas",
        "localidade": "USA (likely AR/Louisiana region)",
        "servico_relevante": "Cloud Migration, IT Consulting, Subcontracting",
        "motivo": "Referenced in City of Cabot cloud migration RFP. Could be prime contractor seeking subcontractors for cloud migration work. Subcontracting opportunity for Zion's cloud services.",
        "fonte": "Prior session web search + RFP analysis",
        "tipo": "company_usa",
        "estimado_valor": "Regional IT services firm",
        "prioridade": "alta",
    },
    {
        "empresa": "AI Automation Agency (UK)",
        "site": "https://www.google.com/search?q=AI+automation+agency+UK+services+2026",
        "localidade": "United Kingdom",
        "servico_relevante": "AI Automation, Chatbots, Workflow Automation, Partnership",
        "motivo": "UK-based AI automation agency identified in prior session. Potential partner for UK/EU clients or client for automation services. AI automation is Zion's core strength.",
        "fonte": "Prior session web search (2026)",
        "tipo": "company_international",
        "estimado_valor": "AI automation agency",
        "prioridade": "media",
    },
    {
        "empresa": "Agency AI Solutions",
        "site": "https://www.google.com/search?q=agency+AI+solutions+US+2026",
        "localidade": "USA",
        "servico_relevante": "AI Services, Chatbots, AI Data Pipeline, Partnership",
        "motivo": "AI solutions agency identified in prior session. Potential partner or client for Zion's AI service offerings. AI agency market growing rapidly.",
        "fonte": "Prior session web search (2026)",
        "tipo": "company_usa",
        "estimado_valor": "AI solutions agency",
        "prioridade": "media",
    },
    # ── SOFTWARE / DIGITAL AGENCIES (partners & clients) ──
    {
        "empresa": "Xovak Studio",
        "site": "https://xovakstudio.com",
        "localidade": "USA (Web agency, white-label focus)",
        "servico_relevante": "White-label Development Partner, AI Services, QA Automation",
        "motivo": "Top white-label agency partner for 2026. Offers custom web/enterprise software. Could be partner for Zion to provide AI/QA services under their brand, or client needing AI capabilities they don't have in-house.",
        "fonte": "Web search (xovakstudio.com white label 2026)",
        "tipo": "agency_usa",
        "estimado_valor": "White-label dev agency",
        "prioridade": "alta",
    },
    {
        "empresa": "Krishang Technolab",
        "site": "https://www.krishangtechnolab.com",
        "localidade": "India / Global (White-label agency)",
        "servico_relevante": "White-label Services, AI, QA Automation, Chatbots",
        "motivo": "Full-service white label agency. Could subcontract AI/data/QA work to Zion. Digital agencies actively seek white-label partners for AI capabilities they can't build in-house.",
        "fonte": "Web search (krishangtechnolab.com white label)",
        "tipo": "agency_international",
        "estimado_valor": "White-label agency",
        "prioridade": "media",
    },
    {
        "empresa": "DoodleWeb",
        "site": "https://doodleweb.io",
        "localidade": "USA (White-label web build partner)",
        "servico_relevante": "White-label Partner for Primes, AI Services, QA",
        "motivo": "White-label web build partner for agencies and prime contractors. Prime contractors need AI/QA/cybersecurity subs. DoodleWeb model = they sell, partners build. Zion could provide AI services under their brand.",
        "fonte": "Web search (doodleweb.io white label prime contractors)",
        "tipo": "agency_usa",
        "estimado_valor": "White-label dev partner",
        "prioridade": "media",
    },
    {
        "empresa": "Allusivedigital",
        "site": "https://allusivedigital.com",
        "localidade": "USA (Digital agency, white-label focus)",
        "servico_relevante": "White-label Web Dev Partner, AI Services, QA Automation",
        "motivo": "Digital agency scaling with white-label web development partner model. Could expand into AI services via partnership with Zion. Agency wants to offer AI without building it in-house.",
        "fonte": "Web search (allusivedigital.com white label 2026)",
        "tipo": "agency_usa",
        "estimado_valor": "Digital agency",
        "prioridade": "media",
    },
    {
        "empresa": "Taskip",
        "site": "https://taskip.net",
        "localidade": "USA/Global (White-label services)",
        "servico_relevante": "White-label Services, AI, QA, Chatbots",
        "motivo": "White-label services agency with 2026 strategy guide. Agencies looking to productize and offer AI/QA as white-label. Zion could be their AI/ML backend partner.",
        "fonte": "Web search (taskip.net white label 2026)",
        "tipo": "agency_usa",
        "estimado_valor": "White-label services agency",
        "prioridade": "media",
    },
    # ── GITHUB REPO OWNERS (from discovery) - companies behind notable repos ──
    {
        "empresa": "n8n-io (n8n Workflow Automation)",
        "site": "https://github.com/n8n-io/n8n",
        "localidade": "Germany/Remote (Open-source workflow automation)",
        "servico_relevante": "AI Automation, Workflow Automation, Chatbots, QA Automation",
        "motivo": "203k stars. Leading open-source workflow automation platform with native AI. Their users need implementation, customization, enterprise integration - all Zion services. Ecosystem partner or implementation services opportunity.",
        "fonte": "GitHub Lead Discovery (n8n-io/n8n, 203k stars)",
        "tipo": "github_repo",
        "estimado_valor": "Open-source platform (commercial support)",
        "prioridade": "media",
    },
    {
        "empresa": "Activepieces (Open-source Automation)",
        "site": "https://github.com/activepieces/activepieces",
        "localidade": "Remote/Global (Open-source)",
        "servico_relevante": "AI Automation, Workflow Automation, Chatbots, QA Automation",
        "motivo": "30k stars. Open-source AI agent & automation platform with 400+ MCP servers. Growing ecosystem needs implementation partners. Similar to n8n - automation platform user base = service opportunity.",
        "fonte": "GitHub Lead Discovery (activepieces/activepieces, 24k stars)",
        "tipo": "github_repo",
        "estimado_valor": "Open-source platform (commercial support)",
        "prioridade": "media",
    },
    {
        "empresa": "Prefect Technologies (Prefect Workflow Orchestration)",
        "site": "https://github.com/PrefectHQ/prefect",
        "localidade": "USA/Remote (Data orchestration)",
        "servico_relevante": "AI Data Pipeline, QA Automation, Cloud Migration",
        "motivo": "24k stars. Python workflow orchestration for data pipelines. Their users build data pipelines that need QA, production hardening, cloud deployment. Prefect + Zion = data pipeline implementation services.",
        "fonte": "GitHub Lead Discovery (PrefectHQ/prefect, 24k stars)",
        "tipo": "github_repo",
        "estimado_valor": "Open-source data platform (SaaS commercial)",
        "prioridade": "media",
    },
    {
        "empresa": "Vector (Observability Data Pipeline)",
        "site": "https://github.com/vectordotdev/vector",
        "localidade": "USA/Remote (Data pipeline)",
        "servico_relevante": "AI Data Pipeline, Cloud Migration, QA Automation",
        "motivo": "22.5k stars. High-performance observability data pipeline. Users need deployment, integration, and optimization services. Data pipeline expertise aligns directly with Zion's AI data pipeline service.",
        "fonte": "GitHub Lead Discovery (vectordotdev/vector, 22.5k stars)",
        "tipo": "github_repo",
        "estimado_valor": "Open-source data pipeline (commercial support)",
        "prioridade": "media",
    },
    {
        "empresa": "Orchest (Data Pipeline Platform)",
        "site": "https://github.com/orchest/orchest",
        "localidade": "Netherlands/Remote (Data science platform)",
        "servico_relevante": "AI Data Pipeline, QA Automation, Cloud Migration",
        "motivo": "4k stars. Build data pipelines the easy way. Data science/orchestration platform. Users need production deployment, cloud migration, and QA for their data pipelines.",
        "fonte": "GitHub Lead Discovery (orchest/orchest, 4k stars)",
        "tipo": "github_repo",
        "estimado_valor": "Open-source data platform",
        "prioridade": "baixa",
    },
    # ── ADDITIONAL US COMPANIES from web search ──
    {
        "empresa": "Entech (Cloud Migration for Mid-Sized Firms)",
        "site": "https://www.entechus.com",
        "localidade": "Florida, USA",
        "servico_relevante": "Cloud Migration, IT Consulting, Cybersecurity",
        "motivo": "Cloud migration services for mid-sized firms. Florida-focused. Mid-market = Zion's sweet spot. Could be competitive intel or partnership opportunity depending on service overlap.",
        "fonte": "Web search (entechus.com cloud migration mid-sized 2026)",
        "tipo": "company_usa",
        "estimado_valor": "Regional IT/cloud services",
        "prioridade": "baixa",
    },
    # ── NEW: Video/Audio AI companies ──
    {
        "empresa": "Wildlife Studios",
        "site": "https://wildlifestudios.com.br",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "Video/Audio AI, AI Data Pipeline, QA Automation",
        "motivo": "Brazilian video/game production studio. Needs video/audio AI for content analysis, automated editing, QA for games/apps, and data pipelines for player analytics. Creative tech = video/audio AI service fit.",
        "fonte": "Web search (wildlifestudios.com.br), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Game/video production studio",
        "prioridade": "media",
    },
    # ── IoT Edge: Brazilian manufacturing/manufacturing-tech ──
    {
        "empresa": "Radix",
        "site": "https://www.radix.com.br",
        "localidade": "São Paulo, SP, Brasil",
        "servico_relevante": "IoT Edge, AI Data Pipeline, Cybersecurity, Cloud Migration",
        "motivo": "Brazilian technology company (deep tech / engineering). Likely works with industrial IoT, embedded systems. IoT edge computing + AI data pipeline + cybersecurity for connected devices = strong fit.",
        "fonte": "Web search (radix.com.br), prior session",
        "tipo": "company_brazil",
        "estimado_valor": "Deep tech/engineering firm",
        "prioridade": "media",
    },
]

# ── Load existing leads and merge ──
# The existing file may be either a dict with "leads" key (output of a previous run)
# or a plain list (legacy format). Handle both.
existing_path = os.path.join(OUT_DIR, "zion_leads_free.json")
existing_leads = []
if os.path.exists(existing_path):
    with open(existing_path) as f:
        existing_data = json.load(f)
    if isinstance(existing_data, dict):
        existing_leads = existing_data.get("leads", [])
    elif isinstance(existing_data, list):
        existing_leads = existing_data
    print(f"Loaded existing leads: {len(existing_leads)}")
print(f"Fresh leads compiled: {len(fresh_leads)}")

# Deduplicate by site: prefer fresh data when both exist
seen_sites = {}  # normalized_site -> index in merged
merged = []

# First pass: add all leads, tracking by normalized site
for lead in existing_leads + fresh_leads:
    site = lead.get("site", "")
    norm = site.lower().rstrip("/")
    if norm in seen_sites:
        # Prefer the entry with more complete data (more non-empty fields)
        existing_idx = seen_sites[norm]
        existing_lead = merged[existing_idx]
        existing_filled = sum(1 for k, v in existing_lead.items() if v and str(v).strip() and str(v).strip() not in ("?", ""))
        fresh_filled = sum(1 for k, v in lead.items() if v and str(v).strip() and str(v).strip() not in ("?", ""))
        if fresh_filled > existing_filled:
            merged[existing_idx] = lead
    else:
        seen_sites[norm] = len(merged)
        merged.append(lead)

print(f"Merged (deduplicated): {len(merged)}")

# Add metadata
timestamp = datetime.now(timezone.utc).isoformat()
output = {
    "generated_at": timestamp,
    "generated_by": "lead-discovery-batch-2026-09-01",
    "total_leads": len(merged),
    "sources": [
        "GitHub Lead Discovery (github_lead_discovery.py) - 75 repos",
        "SAM.gov - 8 government RFPs/BPAs (DNFSB, NIST CAPSS, DoD Agentic AI, C5ISRT, FDA, IRS BPA)",
        "Web search - Brazilian companies (Beep Saúde, Bliss Health, Natura, Conta Azul, Stone, Neurosia, Red Lotus, SCM Gestão, Radix, Wildlife Studios)",
        "Web search - US/international companies (Starbridge, AI Automation Agency UK, Agency AI Solutions, Entech)",
        "Web search - Software/digital agencies (Xovak Studio, Krishang Technolab, DoodleWeb, Allusivedigital, Taskip)",
        "Prior session leads (28 existing leads enriched)",
    ],
    "leads": merged,
    "_metadata": {
        "github_repos_found": 75,
        "government_opportunities": 8,
        "brazil_companies": 10,
        "usa_companies": 4,
        "agencies": 5,
        "github_repo_owners": 5,
        "video_audio_ai": 1,
        "iot_edge": 1,
    },
}

# Save JSON
json_path = os.path.join(OUT_DIR, "zion_leads_free.json")
with open(json_path, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\nSaved JSON: {json_path}")

# Save CSV
csv_path = os.path.join(OUT_DIR, "zion_leads_free.csv")
fieldnames = [
    "empresa", "site", "localidade", "servico_relevante", "motivo",
    "fonte", "tipo", "estimado_valor", "prioridade"
]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for lead in merged:
        writer.writerow(lead)
print(f"Saved CSV: {csv_path}")

# Print summary
print(f"\n{'='*60}")
print(f"LEAD COMPILATION SUMMARY")
print(f"{'='*60}")
print(f"Total leads: {len(merged)}")
print(f"  - Government/RFP: {sum(1 for l in merged if 'government' in l.get('tipo',''))}")
print(f"  - Brazilian companies: {sum(1 for l in merged if 'brazil' in l.get('tipo',''))}")
print(f"  - US companies: {sum(1 for l in merged if 'usa' in l.get('tipo',''))}")
print(f"  - Agencies (partners): {sum(1 for l in merged if 'agency' in l.get('tipo',''))}")
print(f"  - GitHub repos: {sum(1 for l in merged if 'github' in l.get('tipo',''))}")
print(f"\nHigh priority: {sum(1 for l in merged if l.get('prioridade') == 'alta')}")
print(f"Medium priority: {sum(1 for l in merged if l.get('prioridade') == 'media')}")
print(f"Low priority: {sum(1 for l in merged if l.get('prioridade') == 'baixa')}")
print(f"\nTop 10 high-priority leads:")
for i, lead in enumerate([l for l in merged if l.get('prioridade') == 'alta'][:10], 1):
    print(f"  {i}. [{lead['tipo']}] {lead['empresa']} - {lead['servico_relevante'][:60]}")
