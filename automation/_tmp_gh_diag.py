#!/usr/bin/env python3
import json, glob, sys

RUN_ID = 33836715799
files = {
    "run": f"/tmp/gh_run_{RUN_ID}.json",
    "jobs": f"/tmp/gh_jobs_{RUN_ID}.json",
}

def load(p):
    try:
        return json.load(open(p))
    except Exception as e:
        print(f"[warn] cannot load {p}: {e}")
        return {}

run = load(files["run"])
jobs_data = load(files["jobs"])

print("Run:", run.get("display_title") or run.get("displayTitle") or "?")
print("Status:", run.get("status"))
print("Conclusion:", run.get("conclusion"))
print("Head SHA:", (run.get("head_sha") or run.get("headSha") or "")[:12])
print("Event:", run.get("event"))
print()

if jobs_data:
    print("=== jobs ===")
    for item in jobs_data.get("jobs", []):
        name = item.get("name") or "?"
        status = item.get("status")
        conclusion = item.get("conclusion")
        print(f"  - {name}: {status} / {conclusion}")
    print()
