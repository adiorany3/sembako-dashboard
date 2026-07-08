#!/usr/bin/env python3
"""
Monitor crypto prices + sentimen harian.
Sumber harga: CoinGecko API (gratis)
Sumber sentimen: scraping berita detik.com
"""
import urllib.request
import json
import re
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/sembako/scripts"))
from create_crypto_excel import add_price_row, add_sentimen_row

HISTORY_PATH = os.path.expanduser("~/sembako/data/crypto_history.json")

COINS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin", "ripple"]
COIN_MAP = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
            "cardano": "ADA", "dogecoin": "DOGE", "ripple": "XRP"}
COIN_SHORT = {"bitcoin": "btc", "ethereum": "eth", "solana": "sol",
              "cardano": "ada", "dogecoin": "doge", "ripple": "xrp"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Kata kunci sentimen crypto
CRYPTO_POS = ["bullish", "surge", "rally", "pump", "breakout", "all-time high", "ATH",
              "adopsi", "partnership", "upgrade", "listing", "buy", "accumulate",
              "naik", "melonjak", "meroket", "positif", "optimis", "recovery"]
CRYPTO_NEG = ["bearish", "crash", "dump", "sell-off", "hack", "scam", "rug pull",
              "regulation", "ban", "SEC", "lawsuit", "decline", "drop",
              "turun", "anjlok", "merosot", "negatif", "fear", "liquidasi"]

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  Error: {e}")
        return None
def get_ohlc_daily():
    """Fetch 4h OHLC candles -> aggregate daily OHLC per coin.
    Returns dict: {date: {coin: {o, h, l, c, change}}}
    """
    import time as _time
    daily_agg = {}  # {date: {coin: OHLC}}
    
    for coin in COINS:
        short = COIN_SHORT[coin]
        
        # Retry on 429 (up to 3 attempts, long backoff for free tier)
        candles = None
        for attempt in range(3):
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/ohlc?vs_currency=usd&days=7"
            raw = fetch_url(url)
            if not raw:
                _time.sleep(20 * (attempt + 1))
                continue

            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                _time.sleep(20 * (attempt + 1))
                continue

            if isinstance(parsed, dict) and 'error' in parsed:
                print(f"  ⚠️ OHLC retry {attempt+1}: {coin} - {parsed.get('error', '')}")
                _time.sleep(20 * (attempt + 1))
                continue

            if isinstance(parsed, list) and len(parsed) > 0:
                candles = parsed
                break

            _time.sleep(20 * (attempt + 1))
        
        if not candles:
            print(f"  ❌ OHLC gagal: {coin} (3 retries)")
            continue
        
        # Aggregate 4h candles -> daily
        for c in candles:
            if len(c) < 5:
                continue  # skip malformed entries
            ts = datetime.fromtimestamp(c[0] / 1000)
            d = ts.strftime("%Y-%m-%d")
            
            if d not in daily_agg:
                daily_agg[d] = {}
            if short not in daily_agg[d]:
                daily_agg[d][short] = {'o': c[1], 'h': c[2], 'l': c[3], 'c': c[4]}
            else:
                daily_agg[d][short]['h'] = max(daily_agg[d][short]['h'], c[2])
                daily_agg[d][short]['l'] = min(daily_agg[d][short]['l'], c[3])
                daily_agg[d][short]['c'] = c[4]  # close = latest candle
        
        _time.sleep(18)  # rate limit: free tier ~10-30 req/min, be generous
    
    # Calculate change% for each coin per day
    for d in daily_agg:
        for short, ohlc in daily_agg[d].items():
            if ohlc['o'] > 0:
                ohlc['change'] = round((ohlc['c'] - ohlc['o']) / ohlc['o'] * 100, 2)
            else:
                ohlc['change'] = 0
    
    return daily_agg


def get_prices():
    """Fetch current spot prices from CoinGecko with retry."""
    import time as _time
    ids = ",".join(COINS)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd,idr&include_24hr_change=true&include_market_cap=true"
    
    data = None
    for attempt in range(3):
        raw = fetch_url(url)
        if not raw:
            _time.sleep(15 * (attempt + 1))
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and 'error' in parsed:
                print(f"  ⚠️ Spot retry {attempt+1}: {parsed.get('error', '')}")
                _time.sleep(15 * (attempt + 1))
                continue
            data = parsed
            break
        except (json.JSONDecodeError, ValueError):
            _time.sleep(15 * (attempt + 1))
            continue
    
    if not data:
        return None
    
    result = {}
    total_mcap = 0
    
    for coin in COINS:
        if coin in data:
            d = data[coin]
            short = COIN_SHORT[coin]
            result[f"{short}_usd"] = d.get("usd", 0)
            result[f"{short}_idr"] = d.get("idr", 0)
            result[f"{short}_change"] = round(d.get("usd_24h_change", 0), 2)
            total_mcap += d.get("usd_market_cap", 0)
    
    result["total_mcap"] = total_mcap
    return result

def get_crypto_news():
    """Scrape crypto news from detik.com (only today's news)."""
    url = "https://www.detik.com/search/searchall?query=crypto+bitcoin+ethereum&siteid=2&result_type=latest"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, OSError) as e:
        print(f"  ⚠️ News fetch error: {e}")
        return []
    
    raw_titles = re.findall(r'title="([^"]+)"', html)
    skip = ['detikcom', 'WIB', 'MENU', 'Beranda', 'Login', 'Daftar', 'Terpopuler',
            'Koleksi', 'Selengkapnya', 'search', 'img-title']
    
    # Outdated/seasonal patterns to skip
    outdated_patterns = [
        r'\b202[0-5]\b',  # 2020-2025
        r'\bRamadhan\b', r'\bRamadan\b', r'\bLebaran\b', r'\bMudik\b',
        r'\bjelang\s*ramadan\b', r'\b sebelum ramadan\b',
    ]
    
    news = []
    for t in raw_titles:
        t = t.strip()
        if len(t) < 15: continue
        if any(s.lower() in t.lower() for s in skip): continue
        if re.match(r'\w+,\s+\d{1,2}\s+\w+\s+\d{4}', t): continue
        
        # Skip outdated headlines
        t_lower = t.lower()
        if any(re.search(p, t_lower) for p in outdated_patterns):
            continue
        
        news.append(t)
    
    return news[:10]

def analyze_sentiment(text):
    """Analyze crypto sentiment."""
    text_lower = text.lower()
    pos = sum(1 for w in CRYPTO_POS if w in text_lower)
    neg = sum(1 for w in CRYPTO_NEG if w in text_lower)
    
    if pos > neg:
        return "BULLISH", min(0.5 + (pos - neg) * 0.15, 1.0)
    elif neg > pos:
        return "BEARISH", max(-0.5 - (neg - pos) * 0.15, -1.0)
    else:
        return "NETRAL", 0.0

def determine_overall_sentiment(prices, news):
    """Determine overall market sentiment."""
    # Price-based sentiment
    changes = []
    for coin in COINS:
        short = COIN_SHORT[coin]
        change = prices.get(f"{short}_change", 0)
        changes.append(change)
    
    avg_change = sum(changes) / len(changes) if changes else 0
    
    # News-based sentiment
    news_scores = []
    for headline in news:
        _, score = analyze_sentiment(headline)
        news_scores.append(score)
    
    avg_news = sum(news_scores) / len(news_scores) if news_scores else 0
    
    # Combined
    combined = avg_change * 0.02 + avg_news * 0.5  # weighted
    
    if combined > 0.1:
        return "BULLISH 🟢"
    elif combined < -0.1:
        return "BEARISH 🔴"
    else:
        return "NETRAL ⚪"

def main():
    now = datetime.now()
    tanggal = now.strftime("%Y-%m-%d")
    waktu = now.strftime("%H:%M")
    
    print("=" * 55)
    print("🪙 MONITOR CRYPTO & SENTIMEN (OHLC Harian)")
    print(f"📅 {tanggal} {waktu} WIB")
    print("=" * 55)
    
    # 1. Get OHLC daily data (Open/High/Low/Close per coin per day)
    print("\n📊 Mengambil OHLC harian dari CoinGecko...")
    ohlc_daily = get_ohlc_daily()
    
    if not ohlc_daily:
        print("⚠️ Gagal mengambil data OHLC")
        return
    
    # 2. Get current spot + market cap (wait after OHLC rate limit)
    import time as _time
    _time.sleep(30)  # cooldown after OHLC calls
    print("\n💰 Mengambil spot price + market cap...")
    spot = get_prices()
    total_mcap = spot.get("total_mcap", 0) if spot else 0

    # Get USD/IDR rate for OHLC fallback
    usd_idr_rate = 0
    if spot:
        btc_idr = spot.get("btc_idr", 0)
        btc_usd = spot.get("btc_usd", 0)
        if btc_usd > 0:
            usd_idr_rate = btc_idr / btc_usd
    if not usd_idr_rate:
        usd_idr_rate = 17800  # approximate fallback
    
    # 3. Get news
    print("\n📰 Mengambil berita crypto...")
    news = get_crypto_news()
    print(f"  Ditemukan {len(news)} berita")
    
    # 4. Write daily OHLC rows to Excel (1 baris per hari)
    sentimen = "NETRAL ⚪"
    loaded = 0
    for date in sorted(ohlc_daily.keys()):
        coins_data = ohlc_daily[date]
        
        # Build price dict in format add_price_row expects
        row_data = {}
        for short in ['btc', 'eth', 'sol', 'ada', 'doge', 'xrp']:
            if short in coins_data:
                ohlc = coins_data[short]
                usd_val = round(ohlc['c'], 2)  # Close as spot
                row_data[f"{short}_usd"] = usd_val
                row_data[f"{short}_idr"] = round(usd_val * usd_idr_rate, 0) if usd_idr_rate else 0
                row_data[f"{short}_change"] = ohlc['change']
            else:
                row_data[f"{short}_usd"] = 0
                row_data[f"{short}_idr"] = 0
                row_data[f"{short}_change"] = 0
        row_data["total_mcap"] = total_mcap
        
        # Sentimen berdasarkan rata-rata perubahan hari ini
        changes = [coins_data[s]['change'] for s in coins_data if s in ['btc', 'eth', 'sol', 'ada', 'doge', 'xrp']]
        avg_change = sum(changes) / len(changes) if changes else 0
        
        # News sentiment
        news_scores = [analyze_sentiment(h)[1] for h in news]
        avg_news = sum(news_scores) / len(news_scores) if news_scores else 0
        combined = avg_change * 0.02 + avg_news * 0.5
        
        if combined > 0.1:
            sentimen = "BULLISH 🟢"
        elif combined < -0.1:
            sentimen = "BEARISH 🔴"
        else:
            sentimen = "NETRAL ⚪"
        
        # Write OHLC info: Waktu shows OHLC summary
        btc = coins_data.get('btc', {})
        waktu_ohlc = f"O:{btc.get('o',0):.0f} H:{btc.get('h',0):.0f} L:{btc.get('l',0):.0f} C:{btc.get('c',0):.0f}"
        
        add_price_row(date, waktu_ohlc, row_data, sentimen)
        loaded += 1
    
    print(f"\n✅ {loaded} baris OHLC harian ditulis")
    
    # 5. Save to history (latest close per coin)
    if ohlc_daily:
        latest_date = sorted(ohlc_daily.keys())[-1]
        latest = ohlc_daily[latest_date]
        history_entry = {
            "date": latest_date,
            "time": waktu,
            "type": "ohlc_daily",
            "prices": {},
            "sentiment": sentimen,
            "news": news[:5]
        }
        for short, ohlc in latest.items():
            usd_c = ohlc['c']
            history_entry["prices"][f"{short}_usd"] = usd_c
            history_entry["prices"][f"{short}_idr"] = round(usd_c * usd_idr_rate, 0) if usd_idr_rate else 0
            history_entry["prices"][f"{short}_change"] = ohlc['change']
        save_history(latest_date, waktu, history_entry["prices"], sentimen, news)
    
    # 6. Print report
    print(f"\n{'='*55}")
    print(f"📊 *Laporan Crypto OHLC {tanggal}*\n")
    
    for coin in COINS:
        short = COIN_SHORT[coin]
        ticker = COIN_MAP[coin]
        if short in ohlc_daily.get(tanggal, {}):
            ohlc = ohlc_daily[tanggal][short]
            change = ohlc['change']
            arrow = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            
            print(f"{arrow} *{ticker}*")
            print(f"  Open:  ${ohlc['o']:,.2f}")
            print(f"  High:  ${ohlc['h']:,.2f}")
            print(f"  Low:   ${ohlc['l']:,.2f}")
            print(f"  Close: ${ohlc['c']:,.2f}")
            print(f"  Range: ${ohlc['h']-ohlc['l']:,.2f} ({change:+.2f}%)\n")
    
    print(f"📈 Sentimen Pasar: *{sentimen}*")
    
    if news:
        print(f"\n📰 *Berita Terkini:*")
        for i, n in enumerate(news[:5], 1):
            label, _ = analyze_sentiment(n)
            emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NETRAL": "⚪"}[label]
            print(f"  {i}. {emoji} {n[:65]}")
    
    # Save message for cron delivery
    msg = f"🪙 *Crypto OHLC {tanggal}*\n\n"
    for coin in COINS:
        short = COIN_SHORT[coin]
        ticker = COIN_MAP[coin]
        if short in ohlc_daily.get(tanggal, {}):
            ohlc = ohlc_daily[tanggal][short]
            change = ohlc['change']
            arrow = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            msg += f"{arrow} *{ticker}* C:${ohlc['c']:,.2f} H:${ohlc['h']:,.2f} L:${ohlc['l']:,.2f} [{change:+.2f}%]\n"
    
    msg += f"\n📈 Sentimen: *{sentimen}*"
    
    if news:
        msg += "\n\n📰 *Berita:*\n"
        for i, n in enumerate(news[:3], 1):
            msg += f"{i}. {n[:60]}\n"
    
    with open(os.path.expanduser("~/sembako/crypto_report.txt"), "w") as f:
        f.write(msg)

def save_history(tanggal, waktu, prices, sentimen, news):
    history = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    history.append({
        "date": tanggal, "time": waktu,
        "prices": prices, "sentiment": sentimen, "news": news[:5]
    })
    history = history[-365:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
