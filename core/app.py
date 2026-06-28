#!/usr/bin/env python3
"""
Dashboard Backend - Flask API
Aggregates all monitoring data (sembako, crypto, cuaca, emas, keuangan)
"""

import os
import json
import time
import openpyxl
import hashlib
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import sys

CACHE_DIR = os.path.expanduser("~/.hermes/cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(key: str) -> str:
    safe = hashlib.sha256(key.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{safe}.json")


def get_cached(key: str, ttl: int = 28800):
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            entry = json.load(f)
        if time.time() - entry.get("ts", 0) > ttl:
            return None
        return entry.get("data")
    except (json.JSONDecodeError, OSError):
        return None


def set_cache(key: str, data) -> None:
    path = _cache_path(key)
    try:
        with open(path, "w") as f:
            json.dump({"ts": time.time(), "data": data}, f, ensure_ascii=False)
    except OSError:
        pass



app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')
CORS(app)

DATA_DIR = os.path.expanduser("~/sembako/data")


# ============ Helper Functions ============


def load_excel_data(filename, sheet_name=None):
    """Load data from Excel file."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None, None

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active

        data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0]:  # Skip empty rows
                data.append(row)

        # Get file modification time
        file_mtime = os.path.getmtime(path)
        file_date = datetime.fromtimestamp(file_mtime).strftime("%d %b %Y, %H:%M")

        return data if data else [], file_date
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return [], None


def get_file_last_update(filename):
    """Get last update time for a file."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime).strftime("%d %b %Y, %H:%M")
    return None


def load_json_data(filename):
    """Load JSON data."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return {}
    return {}


# ============ API Routes ============


@app.route("/")
def index():
    """Serve dashboard."""
    return render_template("index.html")


@app.route("/api/sembako")
def get_sembako():
    """Get latest sembako prices."""
    data, last_update = load_excel_data("harga_sembako.xlsx", "Harga")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:  # All data
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "beras_premium": row[1],
                    "beras_medium": row[2],
                    "minyak_goreng": row[3],
                    "gula_pasir": row[4],
                    "garam": row[5],
                    "tepung_terigu": row[6],
                    "cabai_merah": row[7],
                    "cabai_rawit": row[8],
                    "bawang_merah": row[9],
                    "bawang_putih": row[10],
                    "minyak_tanah": row[11],
                    "telur_ras": row[12],
                    "telur_kampung": row[13],
                    "ayam_ras": row[14],
                    "ayam_kampung": row[15],
                    "daging_sapi": row[16],
                    "gas_elpiji": row[17] if len(row) > 17 else None,
                    "garam_bata": row[18] if len(row) > 18 else None,
                    "garam_halus": row[19] if len(row) > 19 else None,
                    "susu_km_bendera": row[20] if len(row) > 20 else None,
                    "susu_km_indomilk": row[21] if len(row) > 21 else None,
                    "susu_bubuk_bendera": row[22] if len(row) > 22 else None,
                    "susu_bubuk_indomilk": row[23] if len(row) > 23 else None,
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/crypto")
def get_crypto():
    """Get latest crypto prices."""
    data, last_update = load_excel_data("crypto_monitor.xlsx", "Harga")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "waktu": str(row[1]) if row[1] else "",
                    "btc_usd": row[2],
                    "btc_idr": row[3],
                    "btc_24h": row[4],
                    "eth_usd": row[5],
                    "eth_idr": row[6],
                    "eth_24h": row[7],
                    "sol_usd": row[8],
                    "sol_idr": row[9],
                    "sol_24h": row[10],
                    "market_cap": row[20],
                    "sentimen": row[21],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/emas")
def get_emas():
    """Get latest gold prices."""
    data, last_update = load_excel_data("harga_emas.xlsx", "Harian")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "antam_beli": row[1],
                    "antam_buyback": row[2],
                    "antam_pegadaian": row[3],
                    "galeri24": row[4],
                    "ubs_beli": row[5],
                    "selisih": row[7],
                    "spread_persen": row[8],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/pertanian")
def get_pertanian():
    """Get agriculture prices."""
    data, last_update = load_excel_data("harga_pertanian_ternak.xlsx")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "jagung_pipil": row[1],
                    "jagung_pakan": row[2],
                    "kedelai_impor": row[3],
                    "kedelai_lokal": row[4],
                    "pakan_broiler": row[5],
                    "pakan_layer": row[6],
                    "pakan_bebek": row[7],
                    "bungkil_kedelai": row[8],
                    "jagung_giling": row[9],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/keuangan")
def get_keuangan():
    """Get financial data."""
    data, last_update = load_excel_data("keuangan.xlsx")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data[-20:]:  # Last 20 transactions
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "jenis": row[1],
                    "kategori": row[2],
                    "deskripsi": row[3],
                    "jumlah": row[4],
                    "metode": row[5] or "",
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/peternakan")
def get_peternakan():
    """Get comprehensive livestock data (hulu to hilir)."""
    data, last_update = load_excel_data("harga_peternakan_lengkap.xlsx", "Data Utama")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data[-50:]:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "kategori": row[1],
                    "sub_kategori": row[2],
                    "produk": row[3],
                    "harga": row[4],
                    "satuan": row[5],
                    "sumber": row[6],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/peternakan/<kategori>")
def get_peternakan_by_kategori(kategori):
    """Get peternakan data filtered by kategori (hulu, industri, hilir, analisis)."""
    data, last_update = load_excel_data("harga_peternakan_lengkap.xlsx", "Data Utama")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0] and row[1] and row[1].upper() == kategori.upper():
            result.append(
                {
                    "tanggal": str(row[0]),
                    "kategori": row[1],
                    "sub_kategori": row[2],
                    "produk": row[3],
                    "harga": row[4],
                    "satuan": row[5],
                    "sumber": row[6],
                }
            )

    return jsonify(
        {"data": result, "last_update": last_update, "kategori": kategori.upper()}
    )


@app.route("/keuangan")
def keuangan():
    """Serve dedicated keuangan page."""
    return render_template("keuangan.html")


@app.route("/api/summary")
def get_summary():
    """Get overall summary."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "sembako": {
            "status": "OK" if load_excel_data("harga_sembako.xlsx")[0] else "ERROR"
        },
        "crypto": {
            "status": "OK" if load_excel_data("crypto_monitor.xlsx")[0] else "ERROR"
        },
        "emas": {"status": "OK" if load_excel_data("harga_emas.xlsx")[0] else "ERROR"},
        "pertanian": {
            "status": (
                "OK" if load_excel_data("harga_pertanian_ternak.xlsx")[0] else "ERROR"
            )
        },
        "keuangan": {
            "status": "OK" if load_excel_data("keuangan.xlsx")[0] else "ERROR"
        },
        "peternakan": {
            "status": (
                "OK" if load_excel_data("harga_peternakan_lengkap.xlsx")[0] else "ERROR"
            )
        },
    }
    return jsonify(summary)


@app.route("/api/saham")
def get_saham():
    """Get IHSG and bluechip stock data."""
    import os

    excel_path = os.path.join(DATA_DIR, "harga_saham_ihsg.xlsx")
    if not os.path.exists(excel_path):
        return jsonify({"error": "Data not found"}), 404

    wb = openpyxl.load_workbook(excel_path, data_only=True)

    # Get all sheets data
    result = {}

    # Sheet 1: IHSG
    ws_ihsg = wb["IHSG"]
    ihsg_data = []
    for row in ws_ihsg.iter_rows(min_row=2, values_only=True):
        if row[0]:
            ihsg_data.append(
                {
                    "tanggal": str(row[0]),
                    "ihsg": row[1],
                    "change": row[2],
                    "change_pct": row[3],
                    "high": row[4],
                    "low": row[5],
                    "volume": row[6],
                    "sentimen": row[7],
                }
            )
    result["ihsg"] = ihsg_data[-30:]  # Last 30 days

    # Sheet 2: Sektor
    ws_sektor = wb["Sektor"]
    sektor_data = []
    for row in ws_sektor.iter_rows(min_row=2, values_only=True):
        if row[0]:
            sektor_data.append(
                {
                    "sektor": row[0],
                    "value": row[1],
                    "daily_change": row[2],
                    "change_pct": row[3],
                    "weekly_trend": row[4],
                    "recommendation": row[8],
                }
            )
    result["sektor"] = sektor_data

    # Sheet 3: Bluechip
    ws_blue = wb["Bluechip"]
    bluechip_data = []
    for row in ws_blue.iter_rows(min_row=2, values_only=True):
        if row[0]:
            bluechip_data.append(
                {
                    "symbol": row[0],
                    "nama": row[1],
                    "sektor": row[2],
                    "harga": row[3],
                    "daily_chg": row[4],
                    "daily_chg_pct": row[5],
                    "rsi": row[6],
                    "trend": row[7],
                    "signal": row[8],
                    "recommendation": row[9],
                }
            )
    result["bluechip"] = bluechip_data

    # Sheet 6: Watchlist
    ws_watch = wb["Watchlist"]
    watchlist_data = []
    for row in ws_watch.iter_rows(min_row=2, values_only=True):
        if row[0]:
            watchlist_data.append(
                {
                    "symbol": row[0],
                    "nama": row[1],
                    "harga": row[3],
                    "daily_chg": row[4],
                    "rsi": row[5],
                    "reason": row[6],
                    "potential": row[7],
                    "recommendation": row[9],
                }
            )
    result["watchlist"] = watchlist_data

    # Get last update from file
    last_update = datetime.fromtimestamp(os.path.getmtime(excel_path)).strftime(
        "%d %b %Y, %H:%M"
    )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/sentimen")
def get_sentimen():
    """Get latest news sentiment data."""
    data, last_update = load_excel_data("sentimen_berita.xlsx", "Detail")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "waktu": str(row[1]),
                    "keyword": row[2],
                    "headline": row[3],
                    "sentimen": row[4],
                    "score": row[5],
                    "source": row[6],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/pakan")
def get_pakan():
    """Get latest pakan/feed prices."""
    data, last_update = load_excel_data("harga_pakan_ternak.xlsx")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    result = []
    for row in data:
        if row[0]:
            result.append(
                {
                    "tanggal": str(row[0]),
                    "jagung_pipilan": row[1],
                    "bungkil_kedelai": row[2],
                    "dedak_padi": row[3],
                    "tepung_ikan": row[4],
                    "pollard": row[5],
                    "biji_kapuk": row[6],
                    "tepung_darah": row[7],
                    "tepung_tulang": row[8],
                    "molases": row[9],
                    "bungkil_kelapa": row[10],
                    "gaplek": row[11],
                    "bungkil_sawit": row[12],
                    "ampas_tahu": row[13],
                    "tepung_bulu_ayam": row[14],
                    "kulit_kentang": row[15],
                    "onggok": row[16],
                    "bungkil_kacang_tanah": row[17],
                    "dedak_halus": row[18],
                    "sorgum": row[19],
                    "menir": row[20],
                    "corn_gluten_feed": row[21],
                    "rice_polish": row[22],
                    "mung_bean_husk": row[23],
                }
            )

    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/kurs")
def get_kurs():
    """Get exchange rates (USD, EUR, SGD, MYR vs IDR)."""
    data, last_update = load_excel_data("kurs_valuta.xlsx", "Harian")
    if not data:
        return jsonify({"data": [], "last_update": None})

    result = []
    for row in data:
        if row[0]:
            result.append({
                "tanggal": str(row[0]),
                "usd_idr": row[1],
                "eur_idr": row[2],
                "sgd_idr": row[3],
                "myr_idr": row[4],
            })
    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/minyak")
def get_minyak():
    """Get crude oil prices (Brent & WTI)."""
    data, last_update = load_excel_data("harga_minyak.xlsx", "Harian")
    if not data:
        return jsonify({"data": [], "last_update": None})

    result = []
    for row in data:
        if row[0]:
            result.append({
                "tanggal": str(row[0]),
                "brent": row[1],
                "wti": row[2],
                "selisih": row[3],
            })
    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/bi-rate")
def get_bi_rate():
    """Get BI Rate & Inflasi (CPI)."""
    data, last_update = load_excel_data("bi_rate_inflasi.xlsx", "Harian")
    if not data:
        return jsonify({"data": [], "last_update": None})

    result = []
    for row in data:
        if row[0]:
            result.append({
                "tanggal": str(row[0]),
                "bi_rate": row[1],
                "inflasi_mom": row[2],
                "inflasi_yoy": row[3],
                "ihk": row[4],
            })
    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/cpo")
def get_cpo():
    """Get Crude Palm Oil (CPO) / Kelapa Sawit price."""
    data, last_update = load_excel_data("harga_cpo.xlsx", "Harian")
    if not data:
        return jsonify({"data": [], "last_update": None})

    result = []
    for row in data:
        if row[0]:
            result.append({
                "tanggal": str(row[0]),
                "harga_myr": row[1],
                "harga_idr": row[2],
                "perubahan_persen": row[3],
            })
    return jsonify({"data": result, "last_update": last_update})


@app.route("/api/alerts")
def get_alerts():
    """Get recent price alerts (significant changes)."""
    import json as _json
    alert_file = os.path.join(DATA_DIR, "price_alerts.json")
    if not os.path.exists(alert_file):
        return jsonify({"alerts": [], "last_check": None})
    try:
        with open(alert_file) as f:
            data = _json.load(f)
        return jsonify({"alerts": data.get("alerts", []), "last_check": data.get("last_check")})
    except Exception:
        return jsonify({"alerts": [], "last_check": None})


@app.route("/api/health")
def health():
    """Health check."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


# ============ AI-Powered Analysis using Groq ============


# Try to import config (local only, not on GitHub)
try:
    
    from config import GROQ_API_KEY
except ImportError:
    # Fallback to environment variable
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


@app.route("/api/ai-analysis")
def get_ai_analysis():
    """
    Read pre-computed analysis from daily cron job.
    ZERO tokens - just reads JSON file.
    Cron job precompute_analysis.py runs every 8h and calls Groq once.
    """
    import time
    import os

    cache_file = os.path.expanduser("~/sembako/data/daily_analysis.json")

    # Try to read pre-computed analysis
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                entry = json.load(f)
            generated = entry.get("generated_at", "unknown")
            next_up = entry.get("next_update", 0)
            remaining = max(0, int(next_up - time.time()))
            return jsonify({
                "status": "success",
                "analysis": entry.get("analysis", ""),
                "timestamp": generated,
                "model": "Groq Llama 3.1 8B (precomputed)",
                "cached": True,
                "refresh_in_seconds": remaining,
            })
        except (json.JSONDecodeError, OSError):
            pass

    # Fallback: compute on-demand if cache missing (rare)
    return jsonify({
        "status": "error",
        "error": "No cached analysis. Run: python3 scripts/precompute_analysis.py",
        "refresh_in_seconds": None,
    }), 503


def generate_analysis_prompt():
    """Generate analysis prompt from all available data."""
    prompt_parts = []
    today = datetime.now().strftime("%d %b %Y")

    prompt_parts.append(f"# ANALISIS MARKER {today}\\n")

    # 1. IHSG & Saham
    try:
        ihsg_path = os.path.join(DATA_DIR, "harga_saham_ihsg.xlsx")
        if os.path.exists(ihsg_path):
            wb = openpyxl.load_workbook(ihsg_path, data_only=True)

            # IHSG data
            ws_ihsg = wb["IHSG"]
            ihsg_rows = list(ws_ihsg.iter_rows(min_row=2, values_only=True))
            if ihsg_rows:
                latest = ihsg_rows[-1]
                prompt_parts.append("\\n## IHSG (Indeks Saham)\\n")
                prompt_parts.append(f"- Level: {latest[1]}\\n")
                prompt_parts.append(f"- Change: {latest[2]} ({latest[3]}%)\\n")
                prompt_parts.append(f"- High: {latest[4]}, Low: {latest[5]}\\n")

            # Sektor
            ws_sektor = wb["Sektor"]
            sektor_rows = list(ws_sektor.iter_rows(min_row=2, values_only=True))
            if sektor_rows:
                prompt_parts.append("\\n## Sektor Performance\\n")
                for row in sektor_rows[:8]:
                    if row[0]:
                        prompt_parts.append(f"- {row[0]}: {row[1]} ({row[3]})\\n")

            # Bluechip
            ws_blue = wb["Bluechip"]
            blue_rows = list(ws_blue.iter_rows(min_row=2, values_only=True))
            if blue_rows:
                prompt_parts.append("\\n## Saham Bluechip LQ45 (Top 10)\\n")
                prompt_parts.append("| Symbol | Harga | RSI | Trend | Rec |\\n")
                prompt_parts.append("|--------|-------|-----|-------|-----|\\n")
                for row in blue_rows[:10]:
                    if row[0]:
                        prompt_parts.append(
                            f"| {row[0]} | {row[3]} | {row[6]} | {row[7]} | {row[9]} |\\n"
                        )

            # Watchlist
            ws_watch = wb["Watchlist"]
            watch_rows = list(ws_watch.iter_rows(min_row=2, values_only=True))
            if watch_rows:
                prompt_parts.append("\\n## Watchlist (Turun + Potensi)\\n")
                for row in watch_rows[:5]:
                    if row[0]:
                        prompt_parts.append(
                            f"- {row[0]} ({row[1]}): RSI={row[5]}, Potential={row[7]}, Rec={row[9]}\\n"
                        )
    except Exception as e:
        prompt_parts.append(f"\\n## IHSG/Saham: Data tidak tersedia ({e})\\n")
        pass

    # 2. Crypto
    try:
        crypto_path = os.path.join(DATA_DIR, "crypto_monitor.xlsx")
        if os.path.exists(crypto_path):
            wb = openpyxl.load_workbook(crypto_path, data_only=True)
            ws = wb["Harga"]
            crypto_rows = list(ws.iter_rows(min_row=2, values_only=True))
            if crypto_rows:
                prompt_parts.append("\\n## Crypto\\n")
                for row in crypto_rows[:6]:
                    if row[0]:
                        prompt_parts.append(f"- {row[0]}: ${row[1]} ({row[4]}%)\\n")
    except Exception as e:
        print(f"Error generating Crypto data for prompt: {e}")
        pass

    # 3. Emas
    try:
        emas_path = os.path.join(DATA_DIR, "harga_emas.xlsx")
        if os.path.exists(emas_path):
            wb = openpyxl.load_workbook(emas_path, data_only=True)
            ws = wb["Harga"]
            emas_rows = list(ws.iter_rows(min_row=2, values_only=True))
            if emas_rows:
                prompt_parts.append("\\n## Emas\\n")
                for row in emas_rows[:3]:
                    if row[0]:
                        prompt_parts.append(
                            f"- {row[0]}: Rp {row[1]} (Buyback: Rp {row[2]})\\n"
                        )
    except Exception as e:
        print(f"Error generating Emas data for prompt: {e}")
        pass

    # 4. Sembako (key items)
    try:
        sembako_path = os.path.join(DATA_DIR, "harga_sembako.xlsx")
        if os.path.exists(sembako_path):
            wb = openpyxl.load_workbook(sembako_path, data_only=True)
            ws = wb["Harga"]
            sembako_rows = list(ws.iter_rows(min_row=2, values_only=True))
            if sembako_rows:
                prompt_parts.append("\\n## Sembako (Key Items)\\n")
                for row in sembako_rows[:8]:
                    if row[0]:
                        prompt_parts.append(f"- {row[0]}: Rp {row[1]}\\n")
    except Exception as e:
        print(f"Error generating Sembako data for prompt: {e}")
        pass

    prompt_parts.append(
        "\\n---\\nBerikan analisis dalam Bahasa Indonesia dengan format yang rapi."
    )
    return "\\n".join(prompt_parts)


# ============ Error Handlers ============


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500


@app.route("/download/<filename>")
def download_file(filename):
    """Download Excel/data files. Generate on-the-fly if missing."""
    import re as _re
    import subprocess
    if not _re.match(r'^[\w\-\.]+$', filename):
        return jsonify({"error": "Invalid filename"}), 400
    
    filepath = os.path.join(DATA_DIR, filename)
    
    # If file missing, try to generate it
    if not os.path.exists(filepath):
        generators = {
            "nutrisi_bahan_pakan_lengkap.xlsx": "../scripts/create_nutrisi_pakan.py",
            "formulasi_pakan_ternak.xlsx": "../scripts/create_formulasi_pakan.py",
        }
        if filename in generators:
            script = os.path.join(os.path.dirname(__file__), generators[filename])
            try:
                subprocess.run(["python3", script], timeout=30, capture_output=True)
            except Exception:
                pass
    
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    try:
        return send_from_directory(DATA_DIR, filename, as_attachment=True)
    except Exception:
        return jsonify({"error": "File not found"}), 404



@app.route("/api/generate-article", methods=["POST"])
def api_generate_article():
    """Generate article, save as JSON + HTML for copy-paste."""
    import subprocess as _sub
    try:
        result = _sub.run(
            ["python3", os.path.join(os.path.dirname(__file__), "../scripts/generate_wp_article.py")],
            capture_output=True, text=True, timeout=30
        )
        # Read generated file
        today = datetime.now().strftime("%Y-%m-%d")
        meta_file = os.path.join(DATA_DIR, "wp_articles", f"{today}.json")
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                meta = json.load(f)
            return jsonify({
                "title": meta["title"],
                "content": meta["content"],
                "category": meta.get("category", ""),
                "date": meta.get("date", ""),
                "html_file": f"/download/wp_articles/{today}.html",
            })
        return jsonify({"error": "Generation failed", "output": result.stdout}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/article")
def article_page():
    """Serve article copy-paste page — inline generate, no subprocess."""
    import random as _rnd
    articles_dir = os.path.join(DATA_DIR, "wp_articles")
    os.makedirs(articles_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    meta_file = os.path.join(articles_dir, f"{today}.json")

    # Generate inline if missing
    if not os.path.exists(meta_file):
        _rnd.seed(datetime.now().day)
        ds = datetime.now().strftime("%d %B %Y")
        ternak_opts = ["Ayam Broiler","Ayam Petelur","Bebek","Sapi Potong","Sapi Perah","Kambing","Domba"]
        ternak = _rnd.choice(ternak_opts)
        title = f"Update Harga Pakan Ternak {ds}: Strategi Hemat Untung Maksimal"
        content = (
            f"<h4>Data Harga Terkini {ds}</h4>"
            f"<p>Pasar peternakan Indonesia tren positif. "
            f"Pantau harga terkini untuk optimasi biaya.</p>"
            f"<h4>Strategi Hemat Pakan</h4>"
            f"<ol><li><strong>Formulasi Mandiri</strong> - hemat 20-30%</li>"
            f"<li><strong>Bahan Lokal</strong> - jagung, dedak, bungkil</li>"
            f"<li><strong>Pencatatan Harga</strong> - beli saat harga rendah</li></ol>"
            f"<p>Semangat peternak Indonesia!</p>"
        )
        _meta = {"title": title, "content": content, "category": "Harga & Pasar", "date": ds}
        with open(meta_file, "w") as _f:
            json.dump(_meta, _f, ensure_ascii=False)

    with open(meta_file) as fp:
        meta = json.load(fp)
        return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>WordPress Article</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
.card {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
h1 {{ color: #1a1a2e; font-size: 22px; }}
pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f8f8f8; padding: 12px; border-radius: 6px; font-size: 13px; max-height: 400px; overflow-y: auto; border: 1px solid #eee; }}
.copy-btn {{ background: #0073aa; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-top: 8px; }}
.copy-btn:hover {{ background: #005a87; }}
.label {{ font-weight: bold; color: #555; margin-bottom: 4px; }}
.success {{ color: green; font-weight: bold; display: none; margin-left: 10px; }}
</style>
</head>
<body>
<h1>🐾 Artikel WordPress — Catatan Insani</h1>
<div class="card">
<div class="label">📝 Title (copy ke WordPress):</div>
<h1 id="title">{meta["title"]}</h1>
<button class="copy-btn" onclick="copyText('title')">📋 Copy Title</button>
<span class="success" id="title-copied">✅ Copied!</span>
</div>
<div class="card">
<div class="label">📂 Category: <strong>{meta.get("category", "")}</strong></div>
<div class="label">📅 Date: <strong>{meta.get("date", "")}</strong></div>
</div>
<div class="card">
<div class="label">📄 HTML Content (paste ke WordPress editor HTML mode):</div>
<pre id="content">{meta["content"]}</pre>
<button class="copy-btn" onclick="copyText('content')">📋 Copy HTML Content</button>
<span class="success" id="content-copied">✅ Copied!</span>
</div>
<div class="card">
<div class="label">👁️ Preview:</div>
{meta["content"]}
</div>
<script>
function copyText(id) {{
  const text = document.getElementById(id).innerText || document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(() => {{
    document.getElementById(id + '-copied').style.display = 'inline';
    setTimeout(() => document.getElementById(id + '-copied').style.display = 'none', 2000);
  }});
}}
</script>
</body></html>"""
    return jsonify({"error": "No article generated yet. POST /api/generate-article first."}), 404


if __name__ == "__main__":
    # Production mode - disable debug for stability
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
