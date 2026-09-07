import json, os, sys

# Read existing environment, ensure DRY_RUN_OUTREACH is set
dry_run = os.environ.get("DRY_RUN_OUTREACH", "").strip()
if not dry_run:
    os.environ["DRY_RUN_OUTREACH"] = "0"
    print("Set DRY_RUN_OUTREACH=0 (live sends)")
else:
    print(f"DRY_RUN_OUTREACH already set to: {dry_run}")

# Show current env summary
for k in ["DRY_RUN_OUTREACH", "LIVE_SEND_ALLOW_SEND", "GOG_ACCOUNT"]:
    print(f"  {k}={os.environ.get(k, '<not set>')}")
