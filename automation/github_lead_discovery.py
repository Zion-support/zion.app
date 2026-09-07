#!/usr/bin/env python3
"""
github_lead_discovery.py - Discover GitHub repos related to Zion Tech Group services.
Services: AI automation, cloud migration, cybersecurity, IT consulting for SMBs.
"""

import json
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error

GITHUB_API = "https://api.github.com/search/repositories"
GITHUB_API_EMAIL = "https://api.github.com/search/code"

# Service keywords mapped to GitHub search queries
SERVICE_QUERIES = {
    "ai_automation": [
        "AI workflow automation",
        "automation platform",
        "business process automation",
        "RPA tool",
        "intelligent automation",
    ],
    "cloud_migration": [
        "cloud migration",
        "cloud infrastructure",
        "multi-cloud management",
        "AWS migration",
        "Azure migration GCP migration",
    ],
    "cybersecurity": [
        "cybersecurity platform",
        "threat detection",
        "security monitoring",
        "vulnerability management",
        "MDR service",
    ],
    "it_consulting_smb": [
        "IT managed services",
        "MSP platform",
        "IT service management",
        "small business IT",
        "IT support automation",
    ],
    "data_ai": [
        "predictive analytics",
        "data pipeline",
        "machine learning platform",
        "AI dashboard",
        "business intelligence tool",
    ],
}

def search_github_repos(query, max_results=10):
    """Search GitHub repos with a query via API (unauthenticated)."""
    results = []
    try:
        # Use gh CLI if available, otherwise urllib
        try:
            out = subprocess.check_output(
                ["gh", "search", "repos", query, "--limit", str(max_results),
                 "--json", "name,url,description,stargazersCount,language,updatedAt,owner"],
                stderr=subprocess.DEVNULL,
                timeout=30,
            ).decode()
            data = json.loads(out)
            for item in data:
                results.append({
                    "name": item["name"],
                    "url": item["url"],
                    "description": item.get("description") or "",
                    "stars": item.get("stargazersCount", 0),
                    "language": item.get("language") or "N/A",
                    "updated": item.get("updatedAt", ""),
                    "owner": item.get("owner", {}).get("login", ""),
                })
            return results
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # Fallback: GitHub REST API
        params = urllib.parse.urlencode({
            "q": query,
            "per_page": str(max_results),
            "sort": "updated",
            "order": "desc",
        })
        url = f"{GITHUB_API}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "ZionLeadDiscovery/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                results.append({
                    "name": item["name"],
                    "url": item["html_url"],
                    "description": item.get("description") or "",
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language") or "N/A",
                    "updated": item.get("updated_at", ""),
                    "owner": item.get("owner", {}).get("login", ""),
                })
    except Exception as e:
        print(f"[WARN] GitHub search failed for '{query}': {e}", file=sys.stderr)
    return results

def main():
    all_results = {}
    print("=" * 60)
    print("GITHUB LEAD DISCOVERY - Zion Tech Group")
    print("=" * 60)

    for service, queries in SERVICE_QUERIES.items():
        print(f"\n--- {service} ---")
        service_results = []
        for q in queries:
            repos = search_github_repos(q, max_results=8)
            for r in repos:
                if r not in service_results:
                    service_results.append(r)
            print(f"  query='{q}': {len(repos)} repos")
            if len(service_results) >= 15:
                break
        all_results[service] = service_results[:15]

    # Flatten for output
    flat = []
    for service, repos in all_results.items():
        for r in repos:
            flat.append({
                "service_category": service,
                "repo_name": r["name"],
                "repo_url": r["url"],
                "description": r["description"][:200],
                "stars": r["stars"],
                "language": r["language"],
                "owner": r["owner"],
                "updated": r["updated"],
            })

    out_path = "/Users/miami2/zion.app/automation/data/github_leads.json"
    with open(out_path, "w") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"TOTAL REPOS FOUND: {len(flat)}")
    print(f"Saved to: {out_path}")
    print(f"{'=' * 60}")

    # Print top picks
    print("\nTOP PICKS (>= 50 stars or recent activity):")
    for r in sorted(flat, key=lambda x: x["stars"], reverse=True)[:15]:
        if r["stars"] >= 50 or r["updated"] > "2025-01-01":
            print(f"  ⭐ {r['stars']} | {r['repo_name']} ({r['service_category']})")
            print(f"    {r['repo_url']}")
            print(f"    {r['description'][:120]}")

if __name__ == "__main__":
    main()
