import os


def _normalize_origin(value):
    if not value:
        return None
    raw = str(value).strip().rstrip("/")
    if not raw:
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if raw.startswith("localhost") or raw.startswith("127.0.0.1"):
        return f"http://{raw}"
    return f"https://{raw}"


def get_allowed_origins(is_production=False, env=None):
    env = env or os.environ
    allowed_origins = env.get("READWISE_ALLOWED_ORIGINS", "")
    origins = [
        _normalize_origin(item)
        for item in allowed_origins.split(",")
        if _normalize_origin(item)
    ]
    if origins:
        return origins

    if is_production:
        candidates = []
        for key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_URL", "RAILWAY_HTTP_URL", "PUBLIC_URL", "APP_URL", "URL"):
            raw = str(env.get(key, "") or "").strip()
            if raw:
                origin = _normalize_origin(raw)
                if origin and origin not in candidates:
                    candidates.append(origin)
        if candidates:
            return candidates

    return [
        "http://localhost",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:5000",
    ]
