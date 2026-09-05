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


def _expand_local_aliases(origins):
    expanded = []
    seen = set()
    for origin in origins:
        if origin in seen:
            continue
        expanded.append(origin)
        seen.add(origin)

        if not origin.startswith(("http://", "https://")):
            continue

        scheme, rest = origin.split("://", 1)
        host_port = rest.split("/", 1)[0]
        host = host_port.split(":", 1)[0].lower()
        if host not in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            continue

        alias_hosts = ["localhost", "127.0.0.1"]
        for alias in alias_hosts:
            if alias == host:
                continue
            alias_value = f"{scheme}://{alias}"
            if ":" in host_port:
                alias_value = f"{alias_value}:{host_port.split(':', 1)[1]}"
            if alias_value not in seen:
                expanded.append(alias_value)
                seen.add(alias_value)
    return expanded


def get_allowed_origins(is_production=False, env=None):
    env = env or os.environ
    allowed_origins = env.get("READWISE_ALLOWED_ORIGINS", "")
    origins = [
        _normalize_origin(item)
        for item in allowed_origins.split(",")
        if _normalize_origin(item)
    ]
    if origins:
        return _expand_local_aliases(origins)

    if is_production:
        candidates = []
        for key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_URL", "RAILWAY_HTTP_URL", "PUBLIC_URL", "APP_URL", "URL"):
            raw = str(env.get(key, "") or "").strip()
            if raw:
                origin = _normalize_origin(raw)
                if origin and origin not in candidates:
                    candidates.append(origin)
        if candidates:
            return _expand_local_aliases(candidates)

    return _expand_local_aliases([
        "http://localhost",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:5000",
    ])
