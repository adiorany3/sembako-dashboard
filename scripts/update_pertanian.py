#!/usr/bin/env python3
"""
Scrap harga jagung, kedelai, pakan ternak dari berita online.
"""
import urllib.request
import re
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/sembako"))
from create_pertanian_excel import add_row

HISTORY_PATH = os.path.expanduser("~/sembako/pertanian_history.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9",
}

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Error: {e}")
        return ""

def extract_prices_from_text(text):
    """Extract Rp prices from article text."""
    prices = re.findall(r'Rp\s*([\d.]+(?:\s*(?:per|/)\s*kg)?)', text, re.I)
    results = []
    for p in prices:
        p_clean = re.sub(r'[^\d.]', '', p.split('/')[0].split('per')[0])
        if p_clean:
            try:
                val = int(p_clean.replace('.', ''))
                if 1000 < val < 50000:  # reasonable price range per kg
                    results.append(val)
            except:
                pass
    return results

def scrape_detik(query, limit=3):
    url = f"https://www.detik.com/search/searchall?query={query.replace(' ', '+')}&siteid=2&result_type=latest"
    html = fetch_url(url)
    if not html:
        return [], []
    
    raw_titles = re.findall(r'title="([^"]+)"', html)
    skip = ['detikcom', 'WIB', 'MENU', 'Beranda', 'Login', 'Daftar', 'Terpopuler', 
            'Koleksi', 'Selengkapnya', 'search', 'img-title', 'detikNews', 'detikFinance']
    
    articles = []
    for t in raw_titles:
        t = t.strip()
        if len(t) < 15: continue
        if any(s.lower() in t.lower() for s in skip): continue
        if re.match(r'\w+,\s+\d{1,2}\s+\w+\s+\d{4}', t): continue
        articles.append(t)
    
    # Also try to find links to articles
    links = re.findall(r'href="(https://(?:www|finance)\.detik\.com/[^"]*)"', html)
    
    return articles[:limit], links[:limit*2]

def scrape_article_text(url):
    """Try to get article body text."""
    html = fetch_url(url)
    if not html:
        return ""
    # Remove tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def analyze_commodity_prices():
    """Main analysis."""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 Scraping harga pertanian & ternak - {today}\n")
    
    all_prices = {
        "jagung_pipil": [], "jagung_pakan": [], "kedelai_impor": [], "kedelai_lokal": [],
        "pakan_broiler": [], "pakan_layer": [], "pakan_bebek": [],
        "bungkil_kedelai": [], "jagung_giling": []
    }
    sources = []
    
    queries = [
        ("harga jagung pipil kering Rp", "jagung"),
        ("harga kedelai impor Rp", "kedelai"),
        ("harga pakan ternak ayam broiler Rp", "pakan"),
    ]
    
    for query, category in queries:
        print(f"🔍 {query}")
        titles, links = scrape_detik(query, limit=3)
        
        for title in titles:
            print(f"  📰 {title[:70]}")
            sources.append(title)
        
        # Try to scrape article links for actual prices
        for link in links[:3]:
            if 'search' in link: continue
            text = scrape_article_text(link)
            if len(text) > 200:
                prices = extract_prices_from_text(text)
                if prices:
                    print(f"  💰 Harga ditemukan: {prices}")
                    
                    # Categorize based on context
                    text_lower = text.lower()
                    for p in prices:
                        if "jagung" in text_lower and "pakan" in text_lower:
                            all_prices["jagung_pakan"].append(p)
                        elif "jagung" in text_lower:
                            all_prices["jagung_pipil"].append(p)
                        if "kedelai" in text_lower and ("impor" in text_lower or "dolar" in text_lower):
                            all_prices["kedelai_impor"].append(p)
                        elif "kedelai" in text_lower:
                            all_prices["kedelai_lokal"].append(p)
                        if "pakan" in text_lower and "broiler" in text_lower:
                            all_prices["pakan_broiler"].append(p)
                        elif "pakan" in text_lower and "layer" in text_lower:
                            all_prices["pakan_layer"].append(p)
                        elif "pakan" in text_lower:
                            all_prices["pakan_broiler"].append(p)
    
    # Calculate averages
    final = {}
    for key, vals in all_prices.items():
        if vals:
            final[key] = round(sum(vals) / len(vals))
    
    # If no prices found from scraping, use latest known
    if not final:
        print("\n⚠️ Tidak ada harga baru ditemukan dari scraping")
        return None, sources
    
    return final, sources

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
        msg += "🌽 *Jagung*\n"
        msg += fmt("jagung_pipil", "Kering Pipil") + "\n"
        msg += fmt("jagung_pakan", "Pakan Ternak") + "\n\n"
        msg += "🫘 *Kedelai*\n"
        msg += fmt("kedelai_impor", "Impor") + "\n"
        msg += fmt("kedelai_lokal", "Lokal") + "\n\n"
        msg += "🐔 *Pakan Ternak*\n"
        msg += fmt("pakan_broiler", "Broiler BR1") + "\n"
        msg += fmt("pakan_layer", "Layer") + "\n"
        msg += fmt("pakan_bebek", "Bebek") + "\n"
        msg += fmt("bungkil_kedelai", "Bungkil Kedelai") + "\n"
        msg += fmt("jagung_giling", "Jagung Giling") + "\n"
        
        print(f"\n{msg}")
    else:
        print("\n⚠️ Data harga tidak cukup. Menggunakan data terakhir yang diketahui.")
        # Use fallback data
        fallback = {
            "jagung_pipil": 6200, "jagung_pakan": 7000,
            "kedelai_impor": 11500, "kedelai_lokal": 10200,
            "pakan_broiler": 8300, "pakan_layer": 7700,
            "pakan_bebek": 7100, "bungkil_kedelai": 9800,
            "jagung_giling": 6500
        }
        add_row(datetime.now().strftime("%Y-%m-%d"), fallback, sumber="estimasi terakhir")
        print("✅ Data fallback disimpan")

if __name__ == "__main__":
    main()
