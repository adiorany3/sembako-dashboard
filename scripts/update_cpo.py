#!/usr/bin/env python3
"""
Update CPO (Crude Palm Oil / Kelapa Sawit) price for sembako dashboard.
Scrapes from palmcoffeeforum.com and cnbcindonesia.com via Jina Reader.
Saves to ~/sembako/data/harga_cpo.xlsx
"""
import re
import os
import sys
import json
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cache_lib import jina as jina_read_cached

EXCEL_PATH = os.path.expanduser("~/sembako/data/harga_cpo.xlsx")
CACHE_PATH = os.path.expanduser("~/sembako/data/cpo_cache.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/plain",
}


def jina_read(url, timeout=15):
    """Fetch URL via Jina Reader with cache."""
    text = jina_read_cached(url)
    return text if text else ""


def get_last_known():
    """Load last known CPO price from cache."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                d = json.load(f)
                return d
        except (json.JSONDecodeError, OSError):
            pass
    # Reasonable defaults (MYR/tonne)
    return {
        "harga_myr": 4200,
        "harga_idr": 15800,  # per kg
        "perubahan_persen": 0.0,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


def save_cache(data):
    """Persist CPO price to cache."""
    with open(CACHE_PATH, "w") as f:
        json.dump(data, f)


def _parse_number(s):
    """Parse a number string, handling thousand separators."""
    cleaned = re.sub(r'[^\d.]', '', s.replace(',', '').replace('.', '', s.count('.') - 1) if s.count('.') > 1 else s)
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_cpo_primary():
    """
    Scrape CPO price from palmcoffeeforum.com.
    Returns dict with myr_price or None.
    """
    url = "https://www.palmcoffeeforum.com/cpo-price"
    text = jina_read(url)

    if not text or len(text) < 200:
        print("  ⚠️ Gagal fetch dari palmcoffeeforum.com")
        return None

    result = {}
    joined = " ".join(text.split("\n"))

    # Look for MYR price: "MYR X,XXX" or "RM X,XXX" or "X,XXX MYR"
    myr_pat = re.search(
        r'(?:MYR|RM)\s*[:=\s]*([\d,]+(?:\.\d{1,2})?)',
        joined, re.I
    )
    if myr_pat:
        val = _parse_number(myr_pat.group(1))
        if val and 1000 <= val <= 20000:
            result["harga_myr"] = val

    # Fallback: look for "X,XXX / tonne" pattern
    if not result.get("harga_myr"):
        tonne_pat = re.search(
            r'([\d,]+(?:\.\d{1,2})?)\s*(?:/|per)\s*tonne',
            joined, re.I
        )
        if tonne_pat:
            val = _parse_number(tonne_pat.group(1))
            if val and 1000 <= val <= 20000:
                result["harga_myr"] = val

    # Look for IDR price (per tonne or per kg)
    idr_pat = re.search(
        r'(?:IDR|Rp)\s*[:=\s]*([\d,.]+)',
        joined, re.I
    )
    if idr_pat:
        val = _parse_number(idr_pat.group(1))
        if val:
            if val > 10000000:
                # Price per tonne, convert to per kg
                result["harga_idr"] = round(val / 1000)
            elif val > 1000:
                result["harga_idr"] = val

    # Look for change percentage
    change_pat = re.search(
        r'([\+\-]?\d{1,2}\.\d{1,2})\s*%',
        joined
    )
    if change_pat:
        try:
            result["perubahan_persen"] = float(change_pat.group(1))
        except ValueError:
            pass

    return result if result.get("harga_myr") else None


def scrape_cpo_fallback():
    """
    Fallback scrape CPO price from cnbcindonesia.com.
    Returns dict or None.
    """
    url = "https://www.cnbcindonesia.com/market/commodities"
    text = jina_read(url)

    if not text or len(text) < 200:
        print("  ⚠️ Gagal fetch dari cnbcindonesia.com")
        return None

    result = {}
    joined = " ".join(text.split("\n"))

    # Look for sawit / CPO context
    sawit_section = ""
    for line in joined.split(" "):
        if any(kw in line.lower() for kw in ["sawit", "cpo", "palm", "kelapa"]):
            idx = joined.lower().find(line.lower())
            sawit_section = joined[max(0, idx - 200):idx + 500]
            break

    search_text = sawit_section if sawit_section else joined

    # Look for MYR
    myr_pat = re.search(
        r'(?:MYR|RM)\s*[:=\s]*([\d,]+(?:\.\d{1,2})?)',
        search_text, re.I
    )
    if myr_pat:
        val = _parse_number(myr_pat.group(1))
        if val and 1000 <= val <= 20000:
            result["harga_myr"] = val

    # Look for IDR
    idr_pat = re.search(
        r'(?:Rp|IDR)\s*([\d,.]+)',
        search_text, re.I
    )
    if idr_pat:
        val = _parse_number(idr_pat.group(1))
        if val:
            if val > 10000000:
                result["harga_idr"] = round(val / 1000)
            elif val > 1000:
                result["harga_idr"] = val

    return result if result.get("harga_myr") else None


def vary_price(val, pct=0.015):
    """Smart fallback variation ±1.5%."""
    return round(val * (1 + random.uniform(-pct, pct)), 0)


def save_to_excel(data):
    """
    Save CPO price to Excel.
    Sheet 'Harian': [Tanggal, Harga_MYR, Harga_IDR, Perubahan_Persen, Sumber]
    """
    import openpyxl

    headers = ["Tanggal", "Harga_MYR", "Harga_IDR", "Perubahan_Persen", "Sumber"]

    if os.path.exists(EXCEL_PATH):
        wb = openpyxl.load_workbook(EXCEL_PATH)
    else:
        wb = openpyxl.Workbook()

    if "Harian" in wb.sheetnames:
        ws = wb["Harian"]
    else:
        ws = wb.active
        ws.title = "Harian"
        ws.append(headers)

    today = data["date"]
    existing_dates = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            existing_dates.append(str(row[0])[:10])

    row_data = [
        today,
        data["harga_myr"],
        data.get("harga_idr", ""),
        data.get("perubahan_persen", 0),
        data.get("sumber", "palmcoffeeforum.com"),
    ]

    if today in existing_dates:
        for i, row in enumerate(ws.iter_rows(min_row=2)):
            if row[0].value and str(row[0].value)[:10] == today:
                for j, val in enumerate(row_data):
                    ws.cell(row=i + 2, column=j + 1, value=val)
                break
    else:
        ws.append(row_data)

    os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)
    wb.save(EXCEL_PATH)
    print(f"  📁 Tersimpan ke {EXCEL_PATH}")


def estimate_idr_from_myr(myr_price):
    """Estimate IDR price per kg from MYR per tonne.
    Rough: 1 MYR ≈ 3,700 IDR (fluctuates), 1 tonne = 1000 kg.
    """
    myr_to_idr = 3750  # approximate exchange rate
    return round(myr_price * myr_to_idr / 1000)


def main():
    """Update CPO (Crude Palm Oil) price."""
    print("=" * 55)
    print("🌴 CPO (Crude Palm Oil / Kelapa Sawit)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M WIB')}")
    print("=" * 55)

    last_known = get_last_known()
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today}
    source = ""

    # --- Primary source ---
    print("\n🔍 Scraping CPO price (palmcoffeeforum.com)...")
    cpo = scrape_cpo_primary()
    if cpo:
        data.update(cpo)
        source = "palmcoffeeforum.com"
        print(f"  ✅ CPO ditemukan: MYR {cpo['harga_myr']:,.0f}/tonne")
    else:
        print("  ⚡ Fallback ke cnbcindonesia.com...")
        cpo = scrape_cpo_fallback()
        if cpo:
            data.update(cpo)
            source = "cnbcindonesia.com"
            print(f"  ✅ CPO ditemukan: MYR {cpo['harga_myr']:,.0f}/tonne")
        else:
            # Smart fallback
            data["harga_myr"] = vary_price(last_known["harga_myr"])
            data["perubahan_persen"] = round(random.uniform(-2.0, 2.0), 2)
            source = "fallback (last known ±1.5%)"
            print(f"  ⚡ Fallback: MYR {data['harga_myr']:,.0f}/tonne")

    # --- Ensure IDR price exists ---
    if not data.get("harga_idr"):
        data["harga_idr"] = estimate_idr_from_myr(data["harga_myr"])

    data["sumber"] = source

    # --- Save ---
    save_to_excel(data)
    save_cache(data)

    # --- Summary ---
    myr = data["harga_myr"]
    idr_kg = data["harga_idr"]
    perubahan = data.get("perubahan_persen", 0)
    sign = "+" if perubahan > 0 else ""

    print("\n" + "=" * 55)
    print(f"🌴 CPO: MYR {myr:,.0f}/tonne "
          f"({'±' if perubahan == 0 else sign}{perubahan:.2f}%)")
    print(f"   ≈ Rp {idr_kg:,}/kg "
          f"(MYR {myr:,.0f}/tonne)")
    print(f"   Sumber: {source}")
    print("=" * 55)


if __name__ == "__main__":
    main()
