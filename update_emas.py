#!/usr/bin/env python3
"""
Scrap harga emas Antam & UBS harian dari detik.com.
"""
import urllib.request
import re
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/sembako"))
from create_emas_excel import add_daily_row, add_detail_row

HISTORY_PATH = os.path.expanduser("~/sembako/emas_history.json")

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

def parse_prices(text):
    """Parse emas prices from cleaned text."""
    prices = {}
    lines = text.split('\n')
    
    current_brand = None
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Detect brand sections
        if 'Logam Mulia' in line or ('Antam' in line and 'Pegadaian' not in line and 'Galeri' not in line):
            if 'harga' in line.lower() or 'emas' in line.lower() or 'Rp' in line:
                current_brand = 'antam'
        elif 'Antam Pegadaian' in line:
            current_brand = 'antam_pegadaian'
        elif 'Galeri24' in line:
            current_brand = 'galeri24'
        elif 'UBS' in line and ('harga' in line.lower() or 'emas' in line.lower()):
            current_brand = 'ubs'
        
        # Parse buyback
        if 'buyback' in line.lower():
            m = re.search(r'Rp\s*([\d.]+)', line)
            if m:
                val = int(m.group(1).replace('.', ''))
                if val > 100000:
                    prices['antam_buyback'] = val
        
        # Parse formats: "X gram: Rp Y" or "Emas Batangan X gram: Rp Y" or "Xgr: Rp Y"
        m = re.search(r'(?:Emas\s+Batangan\s+)?([\d.,]+)\s*(?:gram|gr)[:\s]+Rp\s*([\d.]+)', line, re.I)
        if m:
            weight_str = m.group(1).replace(',', '.')
            try:
                weight = float(weight_str)
            except:
                continue
            price = int(m.group(2).replace('.', ''))
            
            if current_brand and price > 500000:
                if current_brand not in prices:
                    prices[current_brand] = {}
                prices[current_brand][weight] = price
        
        # Also parse "Rp X per gram" or "Rp X/gram"
        m2 = re.search(r'Rp\s*([\d.]+)\s*(?:per|/)\s*gram', line, re.I)
        if m2:
            price = int(m2.group(1).replace('.', ''))
            if price > 500000:
                if current_brand and current_brand not in prices:
                    prices[current_brand] = {}
                if current_brand:
                    prices[current_brand][1] = price
                # Also check context for buyback
                if 'buyback' in line.lower():
                    prices['antam_buyback'] = price
    
    return prices

def clean_html(html):
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&#\d+;', '', text)
    return text

def scrape_harga_emas():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 Scraping harga emas - {today}\n")
    
    search_url = "https://www.detik.com/search/searchall?query=Update+Harga+Emas+Hari+Ini&siteid=2&result_type=latest"
    html = fetch_url(search_url)
    
    if not html:
        print("⚠️ Gagal mengakses detik.com")
        return None
    
    # Find article URLs
    article_links = re.findall(r'href="(https://(?:www|finance)\.detik\.com/[^"]*(?:emas|Emas)[^"]*)"', html)
    article_links = [l.replace('&amp;', '&') for l in article_links 
                     if 'searchall' not in l and '/foto/' not in l and '/video/' not in l]
    
    if not article_links:
        print("⚠️ Tidak menemukan artikel harga emas")
        return None
    
    # Get title
    titles = re.findall(r'title="(Update Harga Emas[^"]+)"', html)
    if titles:
        print(f"📰 {titles[0]}")
    
    article_url = article_links[0]
    print(f"  📄 {article_url}")
    article_html = fetch_url(article_url)
    
    if not article_html or len(article_html) < 500:
        print("⚠️ Gagal mengambil artikel")
        return None
    
    text = clean_html(article_html)
    prices = parse_prices(text)
    
    if prices.get('antam'):
        antam_1gr = prices['antam'].get(1, 0)
        buyback = prices.get('antam_buyback', 0)
        if buyback == 0:
            buyback = round(antam_1gr * 0.905)
        antam_pg = prices.get('antam_pegadaian', {}).get(1, 0)
        galeri24_1gr = prices.get('galeri24', {}).get(1, 0)
        ubs_1gr = prices.get('ubs', {}).get(1, 0)
        
        print(f"\n💰 Hasil Scraping:")
        print(f"  Antam 1gr Beli    : Rp {antam_1gr:,}")
        print(f"  Antam 1gr Buyback : Rp {buyback:,}")
        print(f"  Antam Pegadaian   : Rp {antam_pg:,}")
        print(f"  Galeri24          : Rp {galeri24_1gr:,}")
        print(f"  UBS 1gr           : Rp {ubs_1gr:,}")
        
        add_daily_row(today, antam_1gr, buyback, antam_pg, galeri24_1gr, ubs_1gr)
        
        for brand, label in [('antam', 'Antam'), ('antam_pegadaian', 'Antam Pegadaian'), 
                             ('galeri24', 'Galeri24'), ('ubs', 'UBS')]:
            if prices.get(brand):
                add_detail_row(today, label, prices[brand])
        
        save_history(today, antam_1gr, buyback, antam_pg, galeri24_1gr, ubs_1gr)
        
        return prices
    
    print("⚠️ Tidak bisa parse harga emas dari artikel")
    return None

def save_history(tanggal, antam, buyback, pegadaian, galeri24, ubs):
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    history.append({
        "date": tanggal, "antam_beli": antam, "antam_buyback": buyback,
        "antam_pegadaian": pegadaian, "galeri24": galeri24, "ubs": ubs
    })
    history = history[-365:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

def main():
    print("=" * 50)
    print("💰 HARGA EMAS ANTAM & UBS")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M WIB')}")
    print("=" * 50)
    
    result = scrape_harga_emas()
    
    if result:
        antam = result.get('antam', {}).get(1, 0)
        buyback = result.get('antam_buyback', 0)
        ubs = result.get('ubs', {}).get(1, 0)
        spread = antam - buyback
        
        msg = f"💰 *Harga Emas Hari Ini*\n📅 {datetime.now().strftime('%d %B %Y')}\n\n"
        msg += f"*Antam*\n"
        msg += f"  Beli    : Rp {antam:,}/gr\n"
        msg += f"  Buyback : Rp {buyback:,}/gr\n"
        msg += f"  Spread  : Rp {spread:,} ({spread/antam*100:.1f}%)\n\n"
        if ubs:
            msg += f"*UBS*\n  Beli    : Rp {ubs:,}/gr\n\n"
        
        if antam > 2700000:
            msg += "📈 Emas di level tinggi"
        elif antam < 2600000:
            msg += "📉 Emas relatif murah"
        else:
            msg += "⚖️ Emas di level moderat"
        
        print(f"\n{msg}")
    else:
        print("\n⚠️ Gagal mengambil data harga emas")

if __name__ == "__main__":
    main()
