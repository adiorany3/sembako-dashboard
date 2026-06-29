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

sys.path.insert(0, os.path.expanduser("~/sembako"))
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

def get_prices():
    """Fetch prices from CoinGecko."""
    ids = ",".join(COINS)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd,idr&include_24hr_change=true&include_market_cap=true"
    
    raw = fetch_url(url)
    if not raw:
        return None
    
    data = json.loads(raw)
    
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
    except:
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
    print("🪙 MONITOR CRYPTO & SENTIMEN")
    print(f"📅 {tanggal} {waktu} WIB")
    print("=" * 55)
    
    # 1. Get prices
    print("\n💰 Mengambil harga dari CoinGecko...")
    prices = get_prices()
    
    if not prices:
        print("⚠️ Gagal mengambil harga crypto")
        return
    
    # 2. Get news
    print("\n📰 Mengambil berita crypto...")
    news = get_crypto_news()
    print(f"  Ditemukan {len(news)} berita")
    
    # 3. Analyze sentiment
    print("\n🔍 Menganalisa sentimen...")
    sentimen = determine_overall_sentiment(prices, news)
    
    # 4. Per-coin sentiment from news
    coin_sentiments = {}
    for headline in news:
        headline_lower = headline.lower()
        for coin_name, ticker in COIN_MAP.items():
            if coin_name in headline_lower or ticker.lower() in headline_lower:
                label, score = analyze_sentiment(headline)
                if ticker not in coin_sentiments:
                    coin_sentiments[ticker] = []
                coin_sentiments[ticker].append((label, score, headline))
    
    # 5. Save to Excel
    add_price_row(tanggal, waktu, prices, sentimen)
    
    for ticker, sentiments in coin_sentiments.items():
        if sentiments:
            avg_score = sum(s[1] for s in sentiments) / len(sentiments)
            label = "BULLISH" if avg_score > 0.1 else "BEARISH" if avg_score < -0.1 else "NETRAL"
            headline = sentiments[0][2][:80]
            coin_key = [k for k, v in COIN_MAP.items() if v == ticker][0]
            short = COIN_SHORT[coin_key]
            harga = prices.get(f"{short}_usd", 0)
            change = prices.get(f"{short}_change", 0)
            add_sentimen_row(tanggal, ticker, harga, change, label, round(avg_score, 2), headline)
    
    # 6. Save history
    save_history(tanggal, waktu, prices, sentimen, news)
    
    # 7. Print report
    print(f"\n{'='*55}")
    print(f"📊 *Laporan Crypto {tanggal}*\n")
    
    for coin in COINS:
        short = COIN_SHORT[coin]
        ticker = COIN_MAP[coin]
        usd = prices.get(f"{short}_usd", 0)
        idr = prices.get(f"{short}_idr", 0)
        change = prices.get(f"{short}_change", 0)
        arrow = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        
        print(f"{arrow} *{ticker}*")
        print(f"  USD: ${usd:,.2f} | IDR: Rp {idr:,.0f}")
        print(f"  24h: {change:+.2f}%\n")
    
    total_mcap_t = prices.get("total_mcap", 0) / 1e12
    print(f"📊 Total Market Cap: ${total_mcap_t:.2f}T")
    print(f"📈 Sentimen Pasar: *{sentimen}*")
    
    if news:
        print(f"\n📰 *Berita Terkini:*")
        for i, n in enumerate(news[:5], 1):
            label, _ = analyze_sentiment(n)
            emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NETRAL": "⚪"}[label]
            print(f"  {i}. {emoji} {n[:65]}")
    
    # Save message for cron delivery
    msg = f"🪙 *Laporan Crypto {tanggal}*\n\n"
    for coin in COINS:
        short = COIN_SHORT[coin]
        ticker = COIN_MAP[coin]
        usd = prices.get(f"{short}_usd", 0)
        idr = prices.get(f"{short}_idr", 0)
        change = prices.get(f"{short}_change", 0)
        arrow = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        msg += f"{arrow} *{ticker}* ${usd:,.2f} (Rp {idr:,.0f}) [{change:+.2f}%]\n"
    
    msg += f"\n📊 Market Cap: ${total_mcap_t:.2f}T"
    msg += f"\n📈 Sentimen: *{sentimen}*"
    
    if news:
        msg += "\n\n📰 *Berita:*\n"
        for i, n in enumerate(news[:3], 1):
            msg += f"{i}. {n[:60]}\n"
    
    # Write message to file for cron delivery
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
