#!/usr/bin/env python3
"""Send sentiment analysis results to Telegram."""
import sys
sys.path.insert(0, "/root/sembako/core")
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import urllib.request, json

msg = (
    "\U0001f4ca *Analisa Sentimen Berita Hari Ini*\n"
    "\U0001f4c5 02 July 2026\n\n"
    "\U0001f4f0 Total berita: *16*\n"
    "\U0001f7e2 Positif: *0* (0%)\n"
    "\U0001f534 Negatif: *4* (25%)\n"
    "\u26aa Netral: *12* (75%)\n"
    "\U0001f4c8 Skor rata-rata: *-0.19*\n\n"
    "\u26a0\ufe0f Sentimen cenderung *NEGATIF*\n\n"
    "\U0001f4cc Headline Negatif:\n"
    "\u2022 Prabowo Ungkap Biang Kerok Kemiskinan: Korupsi-Penyelundupan\n"
    "\u2022 Pesanan Membludak! Konveksi Seragam Sekolah di Semarang Keb...\n"
    "\u2022 Penasihat Presiden Minta Danantara Turun Tangan soal PHK 2...\n"
    "\u2022 Sinyal dari Purbaya Harga Pertamax Bakal Turun"
)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print("Telegram sent:", json.loads(resp.read()))
