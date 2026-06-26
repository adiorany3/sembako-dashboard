#!/usr/bin/env python3
"""
Daily sembako price updater - all 16 items.
Scrapes latest prices from detik.com and appends to Excel.
"""
import subprocess
import re
import os
import sys
from datetime import datetime

EXCEL_PATH = os.path.expanduser("~/sembako/harga_sembako.xlsx")
sys.path.insert(0, os.path.expanduser("~/sembako"))
from create_excel import add_row

def scrape_prices():
    """Scrape all sembako prices from detik.com."""
    import urllib.request
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "id-ID,id;q=0.9",
    }
    
    search_url = "https://www.detik.com/search/searchall?query=harga+sembako+hari+ini&siteid=2&result_type=latest"
    req = urllib.request.Request(search_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        # Find article links
        links = re.findall(r'href="(https://www\.detik\.com/[^"]*sembako[^"]*)"', html)
        if not links:
            links = re.findall(r'href="(https://www\.detik\.com/[^"]*harga[^"]*bahan[^"]*pokok[^"]*)"', html)
        if not links:
            links = re.findall(r'href="(https://www\.detik\.com/[^"]*harga[^"]*sembako[^"]*)"', html)
        
        if links:
            article_url = links[0]
            req2 = urllib.request.Request(article_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                article = resp2.read().decode("utf-8", errors="ignore")
            
            # Clean HTML for text extraction
            text = re.sub(r'<[^>]+>', ' ', article)
            text = re.sub(r'\s+', ' ', text)
            
            prices = {}
            
            # Beras
            m = re.search(r'beras\s+premium[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['beras_premium'] = int(m.group(1).replace('.', ''))
            m = re.search(r'beras\s+medium[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['beras_medium'] = int(m.group(1).replace('.', ''))
            
            # Gula
            m = re.search(r'gula[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['gula'] = int(m.group(1).replace('.', ''))
            
            # Minyak
            m = re.search(r'minyak\s+goreng\s+curah[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['minyak_curah'] = int(m.group(1).replace('.', ''))
            m = re.search(r'minyak\s+goreng\s+kemasan[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['minyak_kemasan'] = int(m.group(1).replace('.', ''))
            
            # Telur
            m = re.search(r'telur\s+ayam\s+ras[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['telur_ras'] = int(m.group(1).replace('.', ''))
            m = re.search(r'telur\s+ayam\s+kampung[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['telur_kampung'] = int(m.group(1).replace('.', ''))
            
            # Daging Ayam
            m = re.search(r'daging\s+ayam\s+ras[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['ayam_ras'] = int(m.group(1).replace('.', ''))
            m = re.search(r'daging\s+ayam\s+kampung[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['ayam_kampung'] = int(m.group(1).replace('.', ''))
            
            # Daging Sapi
            m = re.search(r'daging\s+sapi[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['sapi'] = int(m.group(1).replace('.', ''))
            
            # Cabai
            m = re.search(r'cabai\s+merah\s+keriting[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['cabai_keriting'] = int(m.group(1).replace('.', ''))
            m = re.search(r'cabai\s+rawit\s+merah[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['cabai_rawit'] = int(m.group(1).replace('.', ''))
            
            # Bawang
            m = re.search(r'bawang\s+merah[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['bawang_merah'] = int(m.group(1).replace('.', ''))
            m = re.search(r'bawang\s+putih[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['bawang_putih'] = int(m.group(1).replace('.', ''))
            
            # Garam & Gas
            m = re.search(r'garam\s+halus[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['garam'] = int(m.group(1).replace('.', ''))
            m = re.search(r'gas\s+elpiji[^R]*Rp\s*([\d.]+)', text, re.I)
            if m: prices['elpiji'] = int(m.group(1).replace('.', ''))
            
            return prices, article_url
            
    except Exception as e:
        print(f"Error scraping: {e}")
    
    return None, None

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Checking prices for {today}...")
    
    prices, source = scrape_prices()
    
    if prices and len(prices) >= 5:
        add_row(today, prices, sumber=source or "detik.com")
        
        def fmt(k, label):
            v = prices.get(k, 0)
            return f"  {label}: Rp {v:,}/kg" if v else f"  {label}: -"
        
        msg = f"📊 *Harga Sembako {today}*\n\n"
        msg += "🍚 *Beras*\n"
        msg += fmt('beras_premium', 'Premium') + "\n"
        msg += fmt('beras_medium', 'Medium') + "\n\n"
        msg += "🍳 *Minyak & Gula*\n"
        msg += fmt('gula', 'Gula') + "\n"
        msg += fmt('minyak_curah', 'Minyak Curah') + "\n"
        msg += fmt('minyak_kemasan', 'Minyak Kemasan') + "\n\n"
        msg += "🥚 *Telur*\n"
        msg += fmt('telur_ras', 'Telur Ras') + "\n"
        msg += fmt('telur_kampung', 'Telur Kampung') + "\n\n"
        msg += "🐔 *Daging*\n"
        msg += fmt('ayam_ras', 'Ayam Ras') + "\n"
        msg += fmt('ayam_kampung', 'Ayam Kampung') + "\n"
        msg += fmt('sapi', 'Sapi') + "\n\n"
        msg += "🌶️ *Bumbu*\n"
        msg += fmt('cabai_keriting', 'Cabai Keriting') + "\n"
        msg += fmt('cabai_rawit', 'Cabai Rawit') + "\n"
        msg += fmt('bawang_merah', 'Bawang Merah') + "\n"
        msg += fmt('bawang_putih', 'Bawang Putih') + "\n\n"
        msg += "🧂 *Lainnya*\n"
        msg += fmt('garam', 'Garam') + "\n"
        msg += fmt('elpiji', 'Gas Elpiji')
        
        print(msg)
    else:
        print(f"⚠️ Gagal mengambil harga lengkap. Data ditemukan: {prices}")

if __name__ == "__main__":
    main()
