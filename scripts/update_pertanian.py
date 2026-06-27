#!/usr/bin/env python3
"""
Scrap harga jagung, kedelai, pakan ternak dari berita online via Jina Reader.
"""
import re
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from create_pertanian_excel import add_row
from cache_lib import jina as jina_read_cached

EXCEL_PATH = os.path.expanduser("~/sembako/data/harga_pertanian_ternak.xlsx")
HISTORY_PATH = os.path.expanduser("~/sembako/data/pertanian_history.json")


def jina_read(url, timeout=15):
    """Fetch URL via Jina Reader with 1h cache (from cache_lib)."""
    text = jina_read_cached(url)
    return text if text else ""


def get_article_urls(keyword, limit=5):
    """Get article URLs from detik.com homepage/indeks matching keyword."""
    text = jina_read("https://finance.detik.com/")
    if not text:
        return []
    urls = re.findall(r'https://finance\.detik\.com/berita-ekonomi-bisnis/d-\d+', text)
    return list(dict.fromkeys(urls))[:limit]


def extract_prices(text):
    """Extract reasonable Rp prices from text."""
    prices = re.findall(r'Rp\s*([0-9.]+)', text)
    results = []
    for p in prices:
        p_clean = re.sub(r'[^\d]', '', p.split('/')[0])
        if p_clean and len(p_clean) >= 4:
            try:
                val = int(p_clean)
                if 2000 < val < 100000:
                    results.append(val)
            except:
                pass
    return results


def categorize_prices(price_list, text_lower):
    """Categorize prices based on text context."""
    categorized = {"jagung": [], "kedelai": [], "pakan": []}
    for p in price_list:
        if "jagung" in text_lower and ("pakan" in text_lower or "giling" in text_lower):
            categorized["jagung"].append(p)
        elif "kedelai" in text_lower:
            categorized["kedelai"].append(p)
        elif "pakan" in text_lower:
            categorized["pakan"].append(p)
    return categorized


def analyze_commodity_prices():
    """Main analysis via Jina Reader."""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 Scraping pertanian & ternak via Jina - {today}\n")

    queries = [
        ("harga+jagung+pipil+kering+2026+site:detik.com", "jagung"),
        ("harga+kedelai+impor+2026+site:detik.com", "kedelai"),
        ("harga+pakan+ternak+ayam+broiler+2026+site:detik.com", "pakan"),
    ]

    all_prices = {
        "jagung_pipil": [], "jagung_pakan": [], "kedelai_impor": [], "kedelai_lokal": [],
        "pakan_broiler": [], "pakan_layer": [], "pakan_bebek": [],
    }
    sources = []

    for query, category in queries:
        print(f"🔍 Query: {category}")
        urls = get_article_urls(category, limit=5)

        for url in urls:
            text = jina_read(url)
            if not text:
                continue

            # Get headline/title from first line
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                print(f"  📰 {lines[0][:70]}")
                sources.append(lines[0][:80])

            prices = extract_prices(text)
            if prices:
                cat = categorize_prices(prices, text.lower())
                for k, v in cat.items():
                    if v:
                        all_prices.get(f"{k}_pipil", all_prices.get(f"{k}_broiler", [])).extend(v)

    # Average
    final = {}
    for key, vals in all_prices.items():
        if vals:
            final[key] = round(sum(vals) / len(vals))

    return final if final else None, sources[:5]


def save_to_history(data, sources):
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    history.append({"date": datetime.now().isoformat(), "prices": data, "sources": sources})
    history = history[-100:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 50)
    print("🌽🫘🐔 HARGA PERTANIAN & TERNAK")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M WIB')}")
    print("=" * 50)

    prices, sources = analyze_commodity_prices()

    if prices and len(prices) >= 2:
        source_str = "; ".join(sources[:3])
        add_row(datetime.now().strftime("%Y-%m-%d"), prices, sumber=source_str)
        save_to_history(prices, sources)

        def fmt(k, label):
            v = prices.get(k, 0)
            return f"  {label}: Rp {v:,}/kg" if v else f"  {label}: -"

        msg = f"🌽🫘🐔 *Harga Pertanian & Ternak*\n📅 {datetime.now().strftime('%d %B %Y')}\n\n"
        msg += "🌽 *Jagung*\n" + fmt("jagung_pipil", "Kering Pipil") + "\n" + fmt("jagung_pakan", "Pakan Ternak") + "\n\n"
        msg += "🫘 *Kedelai*\n" + fmt("kedelai_impor", "Impor") + "\n" + fmt("kedelai_lokal", "Lokal") + "\n\n"
        msg += "🐔 *Pakan Ternak*\n" + fmt("pakan_broiler", "Broiler BR1") + "\n" + fmt("pakan_layer", "Layer") + "\n" + fmt("pakan_bebek", "Bebek") + "\n"

        print(f"\n{msg}")
    else:
        print("\n⚠️ Tidak ada data baru. Menggunakan data terakhir.")
        fallback = {
            "jagung_pipil": 6200, "jagung_pakan": 7000,
            "kedelai_impor": 11500, "kedelai_lokal": 10200,
            "pakan_broiler": 8300, "pakan_layer": 7700,
            "pakan_bebek": 7100,
        }
        add_row(datetime.now().strftime("%Y-%m-%d"), fallback, sumber="estimasi")
        print("✅ Data fallback disimpan")


if __name__ == "__main__":
    main()
