#!/usr/bin/env python3
"""
Shared cache library for all scripts.
File-based TTL cache in ~/.hermes/cache/
"""
import os
import json
import time
import hashlib
import urllib.request

CACHE_DIR = os.path.expanduser("~/.hermes/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/plain",
}


def _key(path: str) -> str:
    return os.path.join(CACHE_DIR, hashlib.md5(path.encode()).hexdigest()[:12] + ".json")


def cached_get(path: str, ttl: int = 28800) -> dict | None:
    """Load cached JSON if not expired. TTL in seconds (default 8h)."""
    fpath = _key(path)
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath) as f:
            e = json.load(f)
        if time.time() - e.get("t", 0) > ttl:
            return None
        return e.get("d")
    except (json.JSONDecodeError, OSError):
        return None


def cached_set(path: str, data: dict) -> None:
    """Save data to cache."""
    fpath = _key(path)
    with open(fpath, "w") as f:
        json.dump({"t": time.time(), "d": data}, f)


# ── Groq API with cache ──────────────────────────────────────

def groq(prompt: str, model: str = "llama-3.1-8b-instant",
         api_key: str = None, ttl: int = 28800) -> dict:
    """
    Call Groq API with 8h cache. Cache key = hash(prompt).
    Returns {"content": str, "usage": dict} or raises.
    """
    key = f"groq:{model}:{hashlib.md5(prompt.encode()).hexdigest()[:12]}"
    prev = cached_get(key, ttl)
    if prev:
        return prev

    if not api_key:
        from config import GROQ_API_KEY as api_key

    import urllib.request
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500,
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
    result = {
        "content": r["choices"][0]["message"]["content"],
        "usage": dict(r["usage"]),
    }
    cached_set(key, result)
    return result


# ── Jina Reader with cache ────────────────────────────────────

def jina(url: str, ttl: int = 3600) -> str:
    """
    Fetch URL via Jina Reader with 1h cache.
    Falls back to stale cache (24h) on error.
    """
    key = f"jina:{url}"
    prev = cached_get(key, ttl)
    if prev:
        return prev

    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(jina_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            cached_set(key, text)
            return text
    except Exception:
        stale = cached_get(key, 86400)
        return stale if stale else ""


# ── Excel mtime-aware cache ──────────────────────────────────

def excel_data_cachekey(file: str, sheet: str = None) -> str:
    return f"excel:{file}:{sheet or 'active'}"


def cached_excel_load(file: str, sheet: str = None, ttl: int = 28800):
    """
    Load Excel data with mtime-aware cache.
    Invalidates if file mtime changed since cached.
    Returns list of rows (or None on cache miss).
    """
    import openpyxl
    path = os.path.expanduser(f"~/sembako/data/{file}")
    if not os.path.exists(path):
        return None

    key = excel_data_cachekey(file, sheet)
    mtime = os.path.getmtime(path)

    prev = cached_get(key, ttl)
    if prev and prev.get("_mtime") == mtime:
        return prev.get("data")

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = [[c.value for c in r] for r in ws.iter_rows(values_only=True)]

    cached_set(key, {"_mtime": mtime, "data": rows})
    return rows
