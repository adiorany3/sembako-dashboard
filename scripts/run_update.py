#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/sembako')
from create_excel import add_row

today = "2026-06-26"
source = "detik.com/jatim - 25 Jun 2026"

prices = {
    'beras_premium': 15009,
    'beras_medium': 12944,
    'gula': 17190,
    'minyak_curah': 20775,
    'minyak_kemasan': 22097,
    'telur_ras': 24671,
    'telur_kampung': 44907,
    'ayam_ras': 31443,
    'ayam_kampung': 69282,
    'sapi': 124926,
    'cabai_keriting': 33780,
    'cabai_rawit': 43428,
    'bawang_merah': 39631,
    'bawang_putih': 34865,
    'garam': 9040,
    'elpiji': 20017,
}

add_row(today, prices, sumber=source)

def fmt(k, label):
    v = prices.get(k, 0)
    return f"  {label}: Rp {v:,}/kg" if v else f"  {label}: -"

msg = f"📊 Harga Sembako {today}\n\n"
msg += "🍚 Beras\n"
msg += fmt('beras_premium', 'Premium') + "\n"
msg += fmt('beras_medium', 'Medium') + "\n\n"
msg += "🍳 Minyak & Gula\n"
msg += fmt('gula', 'Gula') + "\n"
msg += fmt('minyak_curah', 'Minyak Curah') + "\n"
msg += fmt('minyak_kemasan', 'Minyak Kemasan') + "\n\n"
msg += "🥚 Telur\n"
msg += fmt('telur_ras', 'Telur Ras') + "\n"
msg += fmt('telur_kampung', 'Telur Kampung') + "\n\n"
msg += "🐔 Daging\n"
msg += fmt('ayam_ras', 'Ayam Ras') + "\n"
msg += fmt('ayam_kampung', 'Ayam Kampung') + "\n"
msg += fmt('sapi', 'Sapi') + "\n\n"
msg += "🌶️ Bumbu\n"
msg += fmt('cabai_keriting', 'Cabai Keriting') + "\n"
msg += fmt('cabai_rawit', 'Cabai Rawit') + "\n"
msg += fmt('bawang_merah', 'Bawang Merah') + "\n"
msg += fmt('bawang_putih', 'Bawang Putih') + "\n\n"
msg += "🧂 Lainnya\n"
msg += fmt('garam', 'Garam') + "\n"
msg += fmt('elpiji', 'Gas Elpiji') + "\n\n"
msg += f"Sumber: {source}"

print(msg)
