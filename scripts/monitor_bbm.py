#!/usr/bin/env python3
"""
Monitor kenaikan/penurunan harga BBM Indonesia.
Cek dari berita detik.com, filter statement belum pasti.
"""
import urllib.request
import re
import os
import json
from datetime import datetime, timedelta

HISTORY_PATH = os.path.expanduser("~/sembako/bbm_history.json")
SEEN_PATH = os.path.expanduser("~/sembako/bbm_seen.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9",
}

# Harga BBM terakhir yang diketahui (Juni 2026)
HARGA_TERAKHIR = {
    "Pertalite": 10000,
    "Pertamax": 13500,
    "Pertamax Turbo": 15700,
    "Solar": 6800,
    "Dexlite": 14200,
    "Bio Solar": 6800,
}

# Keyword yang menunjukkan berita BELUM PASTI (skip these)
UNCONFIRMED_PATTERNS = [
    r'\btidak\s+(?:akan|juga|pernah)\b',
    r'\bseharusnya\b',
    r'\brencana?\b',
    r'\bbelum\b',
    r'\bmasih\s+(?:dalam\s+)?pertimbangan\b',
    r'\bEvaluasi\b',
    r'\bPengawasan\b',
    r'\bDitunda\b',
    r'\bMasih\s+Diprotes\b',
    r'\bApakah\b',  # "Apakah harga BBM akan naik?"
    r'\bSemoga\b',
    r'\bDiharapkan\b',
    r'\bPerlu\s+Perhitungan\b',
    r'\bHarus\s+Berkaca\b',
    r'\bPasokan\s+Bbm\b',
    r'\bStok\s+Bbm\b',
    r'\bPasar\s+B\b',
    r'\bPasar\s+Nonsubsidi\b',
    r'\bSubsidi\b',
]

# Keyword yang menunjukkan perubahan PASTI
CONFIRMED_NAIK_PATTERNS = [
    r'\bharga\s+naik\b',
    r'\bnaik\s+harga\b',
    r'\bkenaikan\s+harga\b',
    r'\bptalite\s+naik\b',
    r'\bpertalite\s+naik\b',
    r'\bpertamax\s+naik\b',
    r'\bmelorot\b',
    r'\bmeroket\b',
    r'\bmelebihi\s+rc\b',
]

CONFIRMED_TURUN_PATTERNS = [
    r'\bharga\s+turun\b',
    r'\bturun\s+harga\b',
    r'\bpenurunan\s+harga\b',
    r'\bpertalite\s+turun\b',
    r'\bpertamax\s+turun\b',
    r'\blebih\s+murah\b',
    r'\bharga\s+lebih\s+murah\b',
]

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Error: {e}")
        return ""

def load_seen():
    if os.path.exists(SEEN_PATH):
        with open(SEEN_PATH) as f:
            return json.load(f)
    return {"seen": []}

def save_seen(data):
    with open(SEEN_PATH, "w") as f:
        json.dump(data, f)

def get_article_date(article_url):
    """Fetch article page and extract publish date. Returns None if not today."""
    html = fetch_url(article_url, timeout=10)
    if not html:
        return None
    
    # Try multiple date patterns
    date_patterns = [
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"dateModified"\s*:\s*"([^"]+)"',
        r'<meta\s+[^>]*property="article:published_time"\s+[^>]*content="([^"]+)"',
        r'<meta\s+[^>]*content="([^"]+)"\s+[^>]*property="article:published_time"',
    ]
    
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    for pattern in date_patterns:
        match = re.search(pattern, html)
        if match:
            date_str = match.group(1)[:10]  # Get YYYY-MM-DD
            if date_str == today_str:
                return today
            else:
                return None  # Not today's article
    
    # Try detik date format
    date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', html)
    if date_match:
        try:
            day, month_str, year = date_match.groups()
            month_map = {
                'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
                'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
                'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
            }
            month = month_map.get(month_str, 1)
            article_date = datetime(int(year), month, int(day))
            if article_date.date() == today.date():
                return article_date
        except (ValueError, OverflowError):
            pass  # Invalid date, continue
    
    return None  # Could not determine date or not today

def check_bbm_news():
    """Check for BBM price change news from detik.com."""
    queries = [
        "harga BBM naik",
        "harga BBM turun",
        "Pertalite harga naik",
        "Pertamax harga naik",
        "BBM subsidi perubahan",
    ]
    
    all_articles = []  # Store (url, headline)
    
    for q in queries:
        url = f"https://www.detik.com/search/searchall?query={q.replace(' ', '+')}&siteid=2&result_type=latest"
        html = fetch_url(url)
        if not html:
            continue
        
        raw_titles = re.findall(r'title="([^"]+)"', html)
        links = re.findall(r'href="(https://(?:www|finance)\.detik\.com/[^"]+)"', html)
        
        skip = ['detikcom', 'WIB', 'MENU', 'Beranda', 'Login', 'Daftar', 'Terpopuler',
                'Koleksi', 'Selengkapnya', 'search', 'img-title']
        
        for i, t in enumerate(raw_titles):
            t = t.strip()
            if len(t) < 15:
                continue
            if any(s.lower() in t.lower() for s in skip):
                continue
            if re.match(r'\w+,\s+\d{1,2}\s+\w+\s+\d{4}', t):
                continue
            
            # Filter only BBM-related
            t_lower = t.lower()
            if any(kw in t_lower for kw in ['bbm', 'pertalite', 'pertamax', 'solar', 'bensin', 'spbu']):
                article_url = links[i] if i < len(links) else None
                all_articles.append((article_url, t))
    
    return all_articles[:10]

def is_unconfirmed_news(headline_lower):
    """Check if headline is just a statement/plan, not confirmed change."""
    for pattern in UNCONFIRMED_PATTERNS:
        if re.search(pattern, headline_lower):
            return True
    return False

def is_confirmed_change(headline_lower):
    """Check if headline indicates CONFIRMED price change."""
    # Must have "naik" or "turun" context
    has_change_context = any(
        re.search(p, headline_lower) for p in CONFIRMED_NAIK_PATTERNS + CONFIRMED_TURUN_PATTERNS
    )
    if not has_change_context:
        return None  # No clear change signal
    
    # Must NOT have unconfirmed signals
    if is_unconfirmed_news(headline_lower):
        return None
    
    # Check if it's a "naik" or "turun" pattern
    for p in CONFIRMED_NAIK_PATTERNS:
        if re.search(p, headline_lower):
            return "NAIK"
    for p in CONFIRMED_TURUN_PATTERNS:
        if re.search(p, headline_lower):
            return "TURUN"
    
    return None

def analyze_bbm_news(articles):
    """Analyze articles for confirmed price changes."""
    alerts = []
    seen = load_seen()
    
    for article_url, headline in articles:
        if headline in seen["seen"]:
            continue
        
        headline_lower = headline.lower()
        
        # Check if unconfirmed/plan/rumor
        if is_unconfirmed_news(headline_lower):
            print(f"  ⏭️  SKIP (unconfirmed): {headline[:60]}")
            continue
        
        # Check if confirmed change
        change_type = is_confirmed_change(headline_lower)
        
        if change_type:
            # Verify date by fetching article
            print(f"  🔍 CHECKING: {headline[:60]}")
            if article_url:
                article_date = get_article_date(article_url)
                if article_date is None:
                    print(f"     ❌ Not today's article, skipping")
                    seen["seen"].append(headline)  # Mark as seen anyway
                    continue
            
            # Extract prices
            prices = re.findall(r'Rp\s*([\d.,]+)', headline)
            
            # Detect fuel type
            fuel_types = []
            if 'pertalite' in headline_lower: fuel_types.append('Pertalite')
            if 'pertamax' in headline_lower and 'turbo' in headline_lower: fuel_types.append('Pertamax Turbo')
            elif 'pertamax' in headline_lower: fuel_types.append('Pertamax')
            if 'solar' in headline_lower: fuel_types.append('Solar')
            if 'dexlite' in headline_lower: fuel_types.append('Dexlite')
            if 'bbm' in headline_lower and not fuel_types:
                fuel_types.append('BBM Umum')
            
            status = "NAIK 📈" if change_type == "NAIK" else "TURUN 📉"
            
            alert = {
                "headline": headline,
                "status": status,
                "fuel_types": fuel_types,
                "prices": prices,
                "timestamp": datetime.now().isoformat()
            }
            alerts.append(alert)
            print(f"     ✅ CONFIRMED: {status}")
            
            seen["seen"].append(headline)
        else:
            print(f"  ⏭️  SKIP (no confirmed change): {headline[:60]}")
    
    seen["seen"] = seen["seen"][-100:]
    save_seen(seen)
    
    return alerts

def save_history(alerts):
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    history.extend(alerts)
    history = history[-200:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

def main():
    print("=" * 50)
    print("⛽ MONITOR HARGA BBM INDONESIA")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M WIB')}")
    print("=" * 50)
    
    print("\n🔍 Mencari berita perubahan harga BBM (confirmed only)...")
    articles = check_bbm_news()
    print(f"  Ditemukan {len(articles)} berita BBM")
    
    if not articles:
        print("  Tidak ada berita BBM baru")
        return
    
    print("\n📰 Berita BBM terkini:")
    for i, (url, h) in enumerate(articles[:5], 1):
        print(f"  {i}. {h[:70]}")
    
    alerts = analyze_bbm_news(articles)
    
    if alerts:
        save_history(alerts)
        
        print(f"\n🚨 DITEMUKAN {len(alerts)} PERUBAHAN BBM TERKONFIRMASI!")
        
        msg = f"⛽ *Perubahan Harga BBM Terkonfirmasi*\n📅 {datetime.now().strftime('%d %B %Y')}\n\n"
        
        for alert in alerts:
            msg += f"{alert['status']}\n"
            msg += f"📰 {alert['headline'][:100]}\n"
            if alert['fuel_types']:
                msg += f"⛽ Jenis: {', '.join(alert['fuel_types'])}\n"
            if alert['prices']:
                msg += f"💰 Harga: Rp {', Rp '.join(alert['prices'])}\n"
            msg += "\n"
        
        # Add reference prices
        msg += "📊 *Harga BBM Saat Ini (Referensi):*\n"
        for fuel, price in HARGA_TERAKHIR.items():
            msg += f"  {fuel}: Rp {price:,}/liter\n"
        
        print(f"\n{msg}")
        
        # Write to file for cron delivery
        with open(os.path.expanduser("~/sembako/bbm_report.txt"), "w") as f:
            f.write(msg)
    else:
        # Silent - no confirmed changes, no report
        # Clear any stale report file
        report_path = os.path.expanduser("~/sembako/bbm_report.txt")
        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == "__main__":
    main()
