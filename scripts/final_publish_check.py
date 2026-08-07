import os
import re
import sys
import urllib.request
from urllib.error import URLError, HTTPError

REQUIRED_ENV_VARS = [
    "READWISE_ENV",
    "READWISE_SECRET_KEY",
    "READWISE_DB_HOST",
    "READWISE_DB_PORT",
    "READWISE_DB_USER",
    "READWISE_DB_PASSWORD",
    "READWISE_DB_NAME",
    "READWISE_ALLOWED_ORIGINS",
]

RENDER_FILE = os.path.join(os.path.dirname(__file__), "..", "render.yaml")
DEFAULT_HEALTH_URL = "http://127.0.0.1:5000"


def load_render_manifest():
    if not os.path.exists(RENDER_FILE):
        raise FileNotFoundError(f"render.yaml not found at {RENDER_FILE}")

    start_command = None
    env_keys = []
    in_env_vars = False
    with open(RENDER_FILE, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("startCommand:"):
                start_command = stripped.split(":", 1)[1].strip()
            if stripped.startswith("envVars:"):
                in_env_vars = True
                continue
            if in_env_vars:
                if stripped.startswith("- key:"):
                    env_keys.append(stripped.split(":", 1)[1].strip())
                elif stripped and not stripped.startswith("-"):
                    break
    return start_command, env_keys


def validate_render_manifest():
    start_command, env_keys = load_render_manifest()
    issues = []
    if not start_command:
        issues.append("render.yaml is missing startCommand")
    elif not start_command.startswith("gunicorn app:app"):
        issues.append(f"render.yaml startCommand should use 'gunicorn app:app', got: {start_command}")

    missing_keys = [key for key in REQUIRED_ENV_VARS if key not in env_keys]
    if missing_keys:
        issues.append(f"render.yaml envVars is missing required keys: {', '.join(missing_keys)}")

    return issues


def check_environment():
    missing = [key for key in REQUIRED_ENV_VARS if not os.environ.get(key)]
    return missing


def run_health_check(base_url=DEFAULT_HEALTH_URL):
    endpoints = ["/health", "/api/health"]
    failures = []
    for path in endpoints:
        url = base_url.rstrip("/") + path
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status != 200:
                    failures.append(f"{path} returned {response.status}")
        except (HTTPError, URLError) as exc:
            failures.append(f"{path} failed: {exc}")
    return failures


def main():
    print("Final publish readiness check")
    print("- Checking render manifest...")
    try:
        manifest_issues = validate_render_manifest()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    if manifest_issues:
        print("ERROR: render.yaml validation failed:")
        for item in manifest_issues:
            print(f"  - {item}")
        return 1

    print("  render.yaml startCommand and env var keys look good.")

    print("- Checking local environment variables...")
    missing_env = check_environment()
    if missing_env:
        print("WARNING: The following publish env vars are not defined in the current environment:")
        for key in missing_env:
            print(f"  - {key}")
    else:
        print("  All required publish env vars are present.")

    if os.environ.get("RUN_FINAL_HEALTH_CHECK", "false").lower() in {"1", "true", "yes"}:
        print("- Running local health checks...")
        health_failures = run_health_check(os.environ.get("FINAL_HEALTH_URL", DEFAULT_HEALTH_URL))
        if health_failures:
            print("ERROR: Health checks failed:")
            for item in health_failures:
                print(f"  - {item}")
            return 1
        print("  Health checks passed.")
    else:
        print("  Skipped local health checks. Set RUN_FINAL_HEALTH_CHECK=true to enable.")

    print("Final publish readiness check completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
