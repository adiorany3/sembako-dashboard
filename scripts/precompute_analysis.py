#!/usr/bin/env python3
"""
Pre-compute market analysis via Groq API.
Runs as cron job once daily. Saves result to JSON.
API endpoint reads from this file - ZERO Groq calls at request time.
"""
import os
import json
import sys
import openpyxl
from datetime import datetime

DATA_DIR = os.path.expanduser("~/sembako/data")
OUTPUT_PATH = os.path.expanduser("~/sembako/data/daily_analysis.json")
CACHE_PATH = os.path.expanduser("~/.hermes/cache/groq_daily_analysis.json")

# Groq API
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))
try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = ""


def load_all_data() -> str:
    """Compact data summary for prompt - minimal but informative."""
    lines = []
    today = datetime.now().strftime("%d %b %Y, %H:%M")
    lines.append(f"# MARKET SNAPSHOT — {today}\n")

    # IHSG
    try:
        path = os.path.join(DATA_DIR, "harga_saham_ihsg.xlsx")
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb["IHSG"]
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            if rows:
                r = rows[-1]
                lines.append(f"## IHSG\n{r[1]} | {r[2]} ({r[3]}%) | H:{r[4]} L:{r[5]}\n")
    except:
        pass

    # Crypto
    try:
        path = os.path.join(DATA_DIR, "crypto_monitor.xlsx")
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb["Harga"]
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            if rows:
                lines.append("## CRYPTO\n")
                for r in rows[:5]:
                    if r[0]:
                        lines.append(f"{r[0]}:${r[1]} ({r[4]}%)\n")
    except:
        pass

    # Emas
    try:
        path = os.path.join(DATA_DIR, "harga_emas.xlsx")
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb["Harga"]
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            if rows:
                lines.append("## EMAS\n")
                for r in rows[:2]:
                    if r[0]:
                        lines.append(f"{r[0]}: Rp{r[1]}\n")
    except:
        pass

    # Sembako
    try:
        path = os.path.join(DATA_DIR, "harga_sembako.xlsx")
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb["Harga"]
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            if rows:
                lines.append("## SEMBAKO\n")
                for r in rows[:6]:
                    if r[0]:
                        lines.append(f"{r[0]}: Rp{r[1]}\n")
    except:
        pass

    # Sentimen
    try:
        path = os.path.join(DATA_DIR, "sentimen_berita.xlsx")
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb["Summary"]
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            if rows:
                r = rows[-1]
                lines.append(f"## SENTIMEN\nPositif:{r[1]} Negatif:{r[3]} Netral:{r[2]} Avg:{r[4]}\n")
    except:
        pass

    return "".join(lines)


def check_cache(ttl=28800) -> str | None:
    """Return cached analysis if not expired (default 8h)."""
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH) as f:
            entry = json.load(f)
        age = time.time() - entry.get("ts", 0)
        if age < ttl:
            return entry.get("analysis")
    except:
        pass
    return None


def save_cache(analysis: str) -> None:
    import time
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump({"ts": time.time(), "analysis": analysis}, f)
    except:
        pass


def call_groq(prompt: str) -> str:
    """Call Groq API."""
    import urllib.request

    if not GROQ_API_KEY:
        return "[GROQ_API_KEY not set]"

    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": """Kamu analis keuangan Indonesia.
分析的market data dari berbagai sumber.
Kasih:
1. Tren market (naik/turun/stabil)
2. Rekomendasi singkat (RSI<30=BUY, RSI>70=SELL)
3. Warning jika ada perubahan signifikan
4. Prediksi 1-3 hari

Jawaban dalam Bahasa Indonesia. Format markdown. Jangan mengarang data."""
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }).encode()

    req = urllib.request.Request(
        GROQ_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"]


def main():
    import time

    print(f"[{datetime.now():%H:%M:%S}] Pre-compute market analysis...")

    # Check cache first
    cached = check_cache()
    if cached:
        print(f"[{datetime.now():%H:%M:%S}] Using cached analysis (fresh)")
        analysis = cached
    else:
        print(f"[{datetime.now():%H:%M:%S}] Fetching fresh data...")
        data = load_all_data()
        print(f"[{datetime.now():%H:%M:%S}] Calling Groq...")
        analysis = call_groq(data)
        save_cache(analysis)
        print(f"[{datetime.now():%H:%M:%S}] Cached for 8h")

    # Save to output file for API endpoint
    entry = {
        "analysis": analysis,
        "generated_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "next_update": (datetime.now().timestamp() + 28800),
        "source": "groq_precomputed",
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now():%H:%M:%S}] Saved to {OUTPUT_PATH}")
    print(f"Analysis preview: {analysis[:100]}...")


if __name__ == "__main__":
    main()
