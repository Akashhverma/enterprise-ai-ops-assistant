from __future__ import annotations

import os
import sys
import urllib.request


url = os.environ.get("HEALTHCHECK_URL")
if not url:
    print("HEALTHCHECK_URL is required", file=sys.stderr)
    raise SystemExit(2)

try:
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status >= 400:
            raise RuntimeError(f"Unhealthy status: {response.status}")
except Exception as exc:
    print(f"Health check failed for {url}: {exc}", file=sys.stderr)
    raise SystemExit(1)

raise SystemExit(0)
