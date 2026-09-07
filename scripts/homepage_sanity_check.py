#!/usr/bin/env python3
"""Post-deploy homepage sanity check for Pages sites.
Verifies that the live homepage is NOT still showing the build-failed fallback text.
"""

import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = 'https://ziontechgroup.com/'
REPORT = Path('/Users/miami2/zion.app/automation/reports/homepage-sanity-latest.json')
FAIL_FRAG = 'Build failed after'


def main():
    now = datetime.now(timezone.utc)
    run_id = now.strftime('%Y%m%d-%H%M%S')
    ok = False
    html = ''
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode('utf-8', errors='ignore')
        ok = FAIL_FRAG.lower() not in html.lower()
    except Exception as e:
        html = f'ERR: {e}'

    report = {
        'ts': now.isoformat(),
        'run_id': run_id,
        'url': URL,
        'ok': ok,
        'html_preview': html[:120],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
