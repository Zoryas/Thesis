import json
import os
import sys
import urllib.request

BASE_URL = os.environ.get("READWISE_SMOKE_BASE_URL", "http://127.0.0.1:5000")


def main():
    checks = []
    for path in ["/health", "/api/health"]:
        req = urllib.request.Request(BASE_URL + path, headers={"X-Request-ID": "smoke-test"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8")
                checks.append({"path": path, "status": response.status, "body": body})
        except Exception as exc:  # pragma: no cover - smoke script
            checks.append({"path": path, "status": "error", "body": str(exc)})

    print(json.dumps({"checks": checks}, indent=2))
    if any(item.get("status") not in {200, 201} for item in checks):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    main()
