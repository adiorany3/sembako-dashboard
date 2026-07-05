#!/usr/bin/env python3
import os, urllib.request, json

token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

if not token or not chat_id:
    print(f'ERROR: TOKEN={bool(token)} CHAT_ID={bool(chat_id)}')
    exit(1)

msg = (
    "\U0001f4ca *Analisa Sentimen Berita Indonesia*\n"
    "\U0001f4c5 05 July 2026\n\n"
    "\U0001f4f0 Total berita: *16*\n"
    "\U0001f7e2 Positif: *2* (12%)\n"
    "\U0001f534 Negatif: *2* (12%)\n"
    "\u26aa Netral: *12* (75%)\n"
    "\U0001f4c8 Skor rata-rata: *0.00*\n\n"
    "\u2696\ufe0f Sentimen *SEIMBANG* hari ini\n\n"
    "\U0001f4cc Headline:\n"
    "\u2022 Pegang 24,99% Saham, GOTO Buka Suara soal PHK Massal Tokopedia \U0001f534\n"
    "\u2022 Nasib Tokopedia Usai Diterjang Badai PHK \U0001f534\n"
    "\u2022 OJK Perketat Aturan Bank Kecil, Tak Penuhi Modal Bisa Kena Sanksi \U0001f7e2\n"
    "\u2022 BPR Modal Inti di Bawah Rp 6 Miliar Siap-siap Kena Sanksi \U0001f7e2\n"
    "\u2022 Purbaya Buka-bukaan Kondisi Ekonomi Indonesia, Singgung MBG \u26aa\n"
    "\u2022 Sederet Janji demi Tarik Investor Asing Masuk RI \u26aa"
)

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print("OK:", result.get("description", "sent"))
