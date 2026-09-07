#!/usr/bin/env python3
# Lead Discovery A — Multi-source lead discovery for Zion Tech Group outreach.
# Combines web search results with GitHub API discovery to generate
# qualified leads with valid email addresses for the cold outreach pipeline.
#
# Usage:
#     python3 lead_discovery_a.py [--output PATH] [--min-confidence MIN]
#     python3 lead_discovery_a.py --help
#
# Output format: JSON file compatible with outreach-pipeline/leads loaders.
#
# IMPORTANT: This script is designed to run inside Hermes Agent where
# web_search tool is available via the hermes_tools module. For standalone
# execution, set up the environment first.

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    from hermes_tools import web_search
    HAS_WEB_SEARCH = True
except ImportError:
    HAS_WEB_SEARCH = False

# === Configuration ===

ZION_APP_DIR = Path("/Users/miami2/zion.app")
AUTOMATION_DIR = ZION_APP_DIR / "automation"
DATA_DIR = AUTOMATION_DIR / "data"
OUTPUT_DIR = AUTOMATION_DIR / "out"

DEFAULT_OUTPUT = OUTPUT_DIR / "discovered-leads-a.json"

# Service categories for search queries
SERVICE_CATEGORIES = {
    "ai_automation": {
        "keywords": [
            "AI workflow automation startup",
            "business process automation company",
            "intelligent automation platform",
            "RPA software company",
        ],
        "service_tags": ["AI Automation"],
        "regions": ["Brazil", "UK", "US", "Canada", "Australia", "Germany"],
    },
    "cloud_migration": {
        "keywords": [
            "cloud migration services company",
            "managed cloud services provider",
            "AWS migration partner",
            "cloud cost optimization services",
        ],
        "service_tags": ["Cloud Cost"],
        "regions": ["Brazil", "UK", "US", "Canada", "Australia", "Germany"],
    },
    "cybersecurity": {
        "keywords": [
            "cybersecurity consulting firm",
            "managed security services provider",
            "MDR security company",
            "security operations center services",
            "vulnerability management services",
        ],
        "service_tags": ["Cybersecurity"],
        "regions": ["Brazil", "UK", "US", "Canada", "Australia", "Germany"],
    },
    "it_consulting_smb": {
        "keywords": [
            "managed IT services company",
            "IT support MSP",
            "small business IT services",
            "IT consulting firm",
        ],
        "service_tags": ["IT Consulting"],
        "regions": ["Brazil", "UK", "US", "Canada", "Australia", "Germany"],
    },
}

# GitHub search queries for tech company discovery
GITHUB_QUERIES = {
    "ai_automation": [
        "topic:ai-automation language:Python",
        "topic:workflow-automation language:Python",
        "topic:ai-platform language:Python stars:>50",
    ],
    "cloud_migration": [
        "topic:cloud-migration language:Go",
        "topic:aws-migration language:Python stars:>100",
        "topic:cloud-infrastructure language:Go",
    ],
    "cybersecurity": [
        "topic:cybersecurity language:Python stars:>100",
        "topic:security-tools language:Go stars:>50",
        "topic:threat-detection language:Python",
    ],
    "it_consulting_smb": [
        "topic:it-management language:Python",
        "topic:msp-tools language:JavaScript stars:>50",
        "topic:digital-transformation language:Terraform",
    ],
}

# Blocked domains (aggregators, not targets)
BLOCKED_DOMAINS = {
    "google.com", "github.com", "clutch.co", "sam.gov", "goodfirms.co",
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "verifier.me", "hunter.io", "lobster.com", "crunchbase.com",
    "angellist.com", "wellfound.com", "producthunt.com",
    "stackoverflow.com", "quora.com", "reddit.com", "medium.com",
    "youtube.com", "wikipedia.org", "wordpress.com", "blogspot.com",
}

# Generic email prefixes to filter out (unless priority is high)
GENERIC_EMAILS = {
    "info@", "contact@", "hello@", "admin@", "support@", "sales@",
    "ceo@", "founder@", "founders@", "webmaster@", "mail@",
}

# === Utility Functions ===

def is_blocked_domain(domain: str) -> bool:
    """Check if domain is a known aggregator/non-target."""
    domain_lower = domain.lower()
    return any(bd in domain_lower for bd in BLOCKED_DOMAINS)

def is_generic_email(email: str, priority: str = "media") -> bool:
    """Check if email is generic (info@, contact@, etc.)."""
    email_lower = email.lower()
    is_generic = any(email_lower.startswith(g) for g in GENERIC_EMAILS)
    if is_generic and priority != "alta":
        return True
    return False

def extract_email(text: str) -> Optional[str]:
    """Extract first valid email from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(pattern, text)
    for email in matches:
        email_lower = email.lower()
        # Skip ziontechgroup emails and blocked domains
        if "ziontechgroup" in email_lower:
            continue
        domain = email_lower.split("@")[-1]
        if is_blocked_domain(domain):
            continue
        return email
    return None

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None

def domain_to_email_candidates(domain: str) -> list:
    """Generate email candidates from domain."""
    if not domain:
        return []
    
    prefixes = [
        "contact", "info", "hello", "sales", "support",
        "founder", "founders", "ceo", "admin", "tech", "ti",
        "diretoria", "administracao", "gestao",
    ]
    
    candidates = []
    for prefix in prefixes:
        candidates.append(f"{prefix}@{domain}")
    
    return candidates

def generate_company_email(company: str, domain: str, website: str) -> Optional[str]:
    """Try to generate/find a valid email for a company."""
    # Try to extract from website URL or company name patterns
    candidates = domain_to_email_candidates(domain)
    
    # Add company-specific prefixes
    company_slug = company.lower().replace(" ", "").replace("-", "")
    for prefix in ["contact", "info"]:
        candidates.append(f"{prefix}@{domain}")
    
    # Try to find email in company name patterns
    # e.g. "John Doe" -> "john.doe@domain"
    
    for email in candidates:
        # Basic validation
        if "@" in email and "." in email.split("@")[-1]:
            return email
    
    return None

# === Web Search Integration ===

def web_search_leads(category: str, region: str, limit: int = 10) -> list:
    """Search web for companies matching category in region."""
    from hermes_tools import web_search
    
    keywords = SERVICE_CATEGORIES[category]["keywords"]
    results = []
    
    for keyword in keywords[:3]:  # Limit to 3 keywords per category
        query = f"{keyword} {region} 2025 2026"
        try:
            search_result = web_search(query=query, limit=limit)
            data = search_result.get("data", {})
            web_results = data.get("web", [])
            
            for item in web_results[:5]:
                title = item.get("title", "")
                url = item.get("url", "")
                description = item.get("description", "")
                
                domain = extract_domain(url)
                if not domain or is_blocked_domain(domain):
                    continue
                
                # Skip if it looks like an aggregator or directory
                if any(skip in title.lower() for skip in [
                    "list", "top", "ranking", "best", "directory",
                    "review", "comparison", "vs", "alternatives",
                ]):
                    continue
                
                results.append({
                    "company": title.split("|")[0].split("-")[0].strip(),
                    "website": url,
                    "domain": domain,
                    "description": description[:200],
                    "source": f"web_search:{keyword}",
                    "region": region,
                    "category": category,
                })
        except Exception as e:
            print(f"  ⚠ Web search error for '{keyword}': {e}", file=sys.stderr)
        
        time.sleep(0.5)  # Rate limiting
    
    return results

# === GitHub API Integration ===

def github_search_repos(query: str, limit: int = 10) -> list:
    """Search GitHub repositories matching query."""
    url = f"{GITHUB_API}?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={limit}"
    
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Zion-Tech-Group-Lead-Discovery",
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            items = data.get("items", [])
            
            repos = []
            for item in items[:limit]:
                repo_name = item.get("full_name", "")
                repo_url = item.get("html_url", "")
                description = item.get("description", "") or ""
                language = item.get("language", "")
                stars = item.get("stargazers_count", 0)
                updated_at = item.get("updated_at", "")
                
                # Extract domain from repository website if available
                domain = None
                whitespace_pattern = r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                
                # Try to extract company info from description
                company = repo_name.split("/")[-1].replace("-", " ").replace("_", " ").title()
                
                repos.append({
                    "company": company,
                    "website": repo_url,
                    "domain": extract_domain(repo_url),
                    "description": description[:200],
                    "language": language,
                    "stars": stars,
                    "updated_at": updated_at,
                    "source": f"github:{query}",
                    "region": "Global",
                    "category": "tech_company",
                })
            
            return repos
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  ⚠ GitHub API rate limit exceeded for '{query}'", file=sys.stderr)
        else:
            print(f"  ⚠ GitHub API error for '{query}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"  ⚠ GitHub search error for '{query}': {e}", file=sys.stderr)
    
    return []

def github_discover_companies(category: str, limit: int = 15) -> list:
    """Discover companies via GitHub search for a service category."""
    queries = GITHUB_QUERIES.get(category, [])
    results = []
    
    for query in queries:
        repos = github_search_repos(query, limit=limit)
        results.extend(repos)
        time.sleep(1)  # Rate limiting between queries
    
    # Deduplicate by domain
    seen_domains = set()
    unique_results = []
    
    for item in results:
        domain = item.get("domain", "")
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            unique_results.append(item)
    
    return unique_results

# === Lead Processing ===

@dataclass
class LeadCandidate:
    """A lead candidate with validated email."""
    company: str
    email: str
    website: str
    domain: str
    role: str
    personal_note: str
    source: str
    region: str
    category: str
    priority: str = "media"
    confidence: float = 0.0

def score_lead(lead: LeadCandidate) -> float:
    """Score lead quality (0-1)."""
    score = 0.0
    
    # Email quality
    email = lead.email.lower()
    if not any(email.startswith(g) for g in GENERIC_EMAILS):
        score += 0.3
    if "@" in email and "." in email.split("@")[-1]:
        score += 0.2
    
    # Domain quality
    domain = lead.domain.lower()
    if domain and not is_blocked_domain(domain):
        score += 0.2
    
    # Website presence
    if lead.website and lead.website.startswith("http"):
        score += 0.15
    
    # Region relevance
    if lead.region in ["Brazil", "UK", "US", "Canada", "Australia", "Germany"]:
        score += 0.15
    
    return min(score, 1.0)

def process_discovered_company(data: dict, category: str, region: str) -> Optional[LeadCandidate]:
    """Process a discovered company into a lead candidate."""
    company = data.get("company", "").strip()
    website = data.get("website", "")
    domain = data.get("domain", "") or extract_domain(website) or ""
    description = data.get("description", "")
    source = data.get("source", "")
    
    if not company or not domain or is_blocked_domain(domain):
        return None
    
    # Try to generate/find email
    email = generate_company_email(company, domain, website)
    
    if not email:
        return None
    
    if is_generic_email(email):
        priority = "media"
    else:
        priority = "alta"
    
    # Generate personal note from description
    personal_note = description[:150] if description else f"{category} services for {company}."
    
    # Determine role from company name/context
    role = "TI"
    if "cyber" in (company + description).lower():
        role = "CISO/Security Lead"
    elif "cloud" in (company + description).lower():
        role = "Cloud/Infrastructure Lead"
    elif "ai" in (company + description).lower() or "automa" in (company + description).lower():
        role = "CTO/Founder"
    
    confidence = score_lead(LeadCandidate(
        company=company,
        email=email,
        website=website,
        domain=domain,
        role=role,
        personal_note=personal_note,
        source=source,
        region=region,
        category=category,
        priority=priority,
    ))
    
    if confidence < 0.3:
        return None
    
    return LeadCandidate(
        company=company,
        email=email,
        website=website,
        domain=domain,
        role=role,
        personal_note=personal_note,
        source=source,
        region=region,
        category=SERVICE_CATEGORIES[category]["service_tags"][0],
        priority=priority,
        confidence=confidence,
    )

def process_github_company(data: dict, category: str) -> Optional[LeadCandidate]:
    """Process a GitHub-discovered company into a lead candidate."""
    company = data.get("company", "").strip()
    website = data.get("website", "")
    domain = data.get("domain", "") or extract_domain(website) or ""
    description = data.get("description", "")
    source = data.get("source", "")
    stars = data.get("stars", 0)
    
    if not company or not domain or is_blocked_domain(domain):
        return None
    
    # GitHub repos often point to the company's main site
    # Try to extract actual company website from description
    if description:
        website_pattern = r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(website_pattern, description)
        if match:
            domain = match.group(1)
    
    email = generate_company_email(company, domain, website)
    
    if not email:
        return None
    
    priority = "alta" if stars > 200 else "media"
    
    personal_note = description[:150] if description else f"Tech company with {stars} GitHub stars. {category} services."
    
    role = "CTO/Founder"
    if "cyber" in (company + description).lower():
        role = "Security Lead"
    elif "cloud" in (company + description).lower():
        role = "Cloud Lead"
    
    confidence = score_lead(LeadCandidate(
        company=company,
        email=email,
        website=website,
        domain=domain,
        role=role,
        personal_note=personal_note,
        source=source,
        region="Global",
        category="Tech",
        priority=priority,
    ))
    
    if confidence < 0.3:
        return None
    
    return LeadCandidate(
        company=company,
        email=email,
        website=website,
        domain=domain,
        role=role,
        personal_note=personal_note,
        source=source,
        region="Global",
        category="Tech Services",
        priority=priority,
        confidence=confidence,
    )

# === Main Discovery Pipeline ===

def discover_leads(
    output_path: Optional[Path] = None,
    min_confidence: float = 0.3,
    dry_run: bool = False,
) -> dict:
    """Run the full lead discovery pipeline."""
    
    output_path = output_path or DEFAULT_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Lead Discovery A — Zion Tech Group")
    print("=" * 60)
    print()
    
    all_candidates = []
    discovered_count = 0
    qualified_count = 0
    
    # Phase 1: Web search discovery
    print("📱 Phase 1: Web Search Discovery")
    print("-" * 40)
    
    for category, config in SERVICE_CATEGORIES.items():
        print(f"\n  Category: {category} ({', '.join(config['service_tags'])})")
        
        for region in config["regions"][:3]:  # Limit regions per category
            print(f"    Searching {region}...")
            results = web_search_leads(category, region, limit=10)
            
            for result in results:
                discovered_count += 1
                candidate = process_discovered_company(result, category, region)
                
                if candidate:
                    qualified_count += 1
                    candidate.priority = "alta" if candidate.confidence >= 0.6 else "media"
                    all_candidates.append(candidate)
                    print(f"      ✓ {candidate.company} | {candidate.email} | {candidate.region} | conf={candidate.confidence:.2f}")
                else:
                    print(f"      - {result.get('company', '?')} | no valid email")
    
    # Phase 2: GitHub discovery
    print("\n📱 Phase 2: GitHub Discovery")
    print("-" * 40)
    
    for category, queries in GITHUB_QUERIES.items():
        print(f"\n  Category: {category}")
        
        for query in queries[:2]:  # Limit queries per category
            print(f"    Searching: {query}...")
            results = github_discover_companies(category, limit=10)
            
            for result in results:
                discovered_count += 1
                candidate = process_github_company(result, category)
                
                if candidate:
                    qualified_count += 1
                    all_candidates.append(candidate)
                    print(f"      ✓ {candidate.company} | {candidate.email} | stars={result.get('stars', 0)}")
                else:
                    print(f"      - {result.get('company', '?')} | no valid domain")
    
    # Deduplicate by domain
    print("\n📱 Phase 3: Deduplication")
    print("-" * 40)
    
    seen_domains = {}
    deduplicated = []
    
    for candidate in all_candidates:
        domain = candidate.domain.lower()
        if domain in seen_domains:
            # Keep the higher confidence one
            existing = seen_domains[domain]
            if candidate.confidence > existing.confidence:
                seen_domains[domain] = candidate
                print(f"  ↑ Replacing: {existing.company} → {candidate.company} ({domain})")
        else:
            seen_domains[domain] = candidate
            deduplicated.append(candidate)
    
    deduplicated.sort(key=lambda c: (-c.confidence, c.company))
    
    print(f"  Discovered: {discovered_count}")
    print(f"  Qualified: {qualified_count}")
    print(f"  After dedup: {len(deduplicated)}")
    
    # Filter by minimum confidence
    final_leads = [c for c in deduplicated if c.confidence >= min_confidence]
    filtered_out = len(deduplicated) - len(final_leads)
    
    print(f"\n  Min confidence: {min_confidence}")
    print(f"  Final leads: {len(final_leads)}")
    print(f"  Filtered out: {filtered_out}")
    
    # Format output
    leads_output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "lead-discovery-a",
        "total_candidates": discovered_count,
        "qualified_candidates": qualified_count,
        "after_dedup": len(deduplicated),
        "final_leads": len(final_leads),
        "filter_min_confidence": min_confidence,
        "sources": {
            "web_search": len([c for c in final_leads if c.source.startswith("web_search")]),
            "github": len([c for c in final_leads if c.source.startswith("github")]),
        },
        "leads": [
            {
                "empresa": c.company,
                "site": c.website,
                "localidade": c.region,
                "servico_relevante": c.category,
                "motivo": c.personal_note,
                "fonte": c.source,
                "tipo": "discovered",
                "estimado_valor": "To be determined",
                "prioridade": c.priority,
                "email": c.email,
                "domain": c.domain,
                "role": c.role,
                "confidence": c.confidence,
            }
            for c in final_leads
        ],
    }
    
    # Also output pipeline-compatible format
    pipeline_output = [
        {
            "company": c.company,
            "email": c.email,
            "name": c.company,
            "role": c.role,
            "personal_note": c.personal_note,
        }
        for c in final_leads
    ]
    
    # Write outputs
    if not dry_run:
        output_path.write_text(json.dumps(leads_output, indent=2, ensure_ascii=False))
        print(f"\n  📄 Main output: {output_path}")
        
        pipeline_path = output_path.with_name("pipeline-leads.json")
        pipeline_path.write_text(json.dumps(pipeline_output, indent=2, ensure_ascii=False))
        print(f"  📄 Pipeline output: {pipeline_path}")
    else:
        print(f"\n  🔬 DRY RUN — outputs not written")
        print(f"  Main output would be: {output_path}")
    
    print()
    print("=" * 60)
    print("Discovery Summary")
    print("=" * 60)
    print(f"  Total discovered: {discovered_count}")
    print(f"  Qualified: {qualified_count}")
    print(f"  Final leads: {len(final_leads)}")
    print()
    
    if final_leads:
        print("📧 Leads ready for pipeline:")
        for lead in final_leads:
            print(f"  • {lead.email} — {lead.company} [{lead.region}] [{lead.category}]")
    
    return leads_output

def main():
    parser = argparse.ArgumentParser(
        description="Lead Discovery A — Multi-source lead discovery for Zion Tech Group",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 lead_discovery_a.py
  python3 lead_discovery_a.py --output /path/to/output.json
  python3 lead_discovery_a.py --min-confidence 0.5
  python3 lead_discovery_a.py --dry-run
        """,
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output JSON file path (default: out/discovered-leads-a.json)",
    )
    parser.add_argument(
        "--min-confidence", "-m",
        type=float,
        default=0.3,
        help="Minimum lead confidence score (0-1, default: 0.3)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Run discovery but don't write output files",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed discovery logs",
    )
    
    args = parser.parse_args()
    
    result = discover_leads(
        output_path=args.output,
        min_confidence=args.min_confidence,
        dry_run=args.dry_run,
    )
    
    # Print stats
    print("\n📊 Stats:")
    print(f"  Sources: {result['sources']}")
    print(f"  Total leads: {result['final_leads']}")
    
    # Category breakdown
    categories = {}
    for lead in result["leads"]:
        cat = lead.get("servico_relevante", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("  By category:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")
    
    print(f"\n✅ Lead discovery complete. Ready for pipeline processing.")

if __name__ == "__main__":
    main()
