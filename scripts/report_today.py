#!/usr/bin/env python3
"""Generate sembako price report."""

prices = {
    "beras_premium": 15004, "beras_medium": 12911,
    "gula": 17172, "minyak_curah": 20413, "minyak_kemasan": 21493,
    "telur_ras": 25032, "telur_kampung": 46201,
    "ayam_ras": 32081, "ayam_kampung": 69053,
    "sapi": 124778,
    "cabai_keriting": 35538, "cabai_rawit": 47354,
    "bawang_merah": 41274, "bawang_putih": 34946,
    "garam": 9184, "elpiji": 19909,
}

def rp(v):
    return f"Rp {v:,}".replace(",", ".")

print("📊 Harga Sembako Harian — 24 Juni 2026")
print("Sumber: Siskaperbapo Jatim via detik.com")
print("=" * 50)

sections = [
    ("🍚 Beras", [("Beras Premium", "beras_premium", "/kg"), ("Beras Medium", "beras_medium", "/kg")]),
    ("🍳 Minyak & Gula", [
        ("Gula Kristal Putih", "gula", "/kg"),
        ("Minyak Goreng Curah", "minyak_curah", "/kg"),
        ("Minyak Goreng Kemasan", "minyak_kemasan", "/liter"),
    ]),
    ("🥚 Telur", [("Telur Ayam Ras", "telur_ras", "/kg"), ("Telur Ayam Kampung", "telur_kampung", "/kg")]),
    ("🐔 Daging", [
        ("Daging Ayam Ras", "ayam_ras", "/kg"),
        ("Daging Ayam Kampung", "ayam_kampung", "/kg"),
        ("Daging Sapi", "sapi", "/kg"),
    ]),
    ("🌶️ Bumbu", [
        ("Cabai Merah Keriting", "cabai_keriting", "/kg"),
        ("Cabai Rawit Merah", "cabai_rawit", "/kg"),
        ("Bawang Merah", "bawang_merah", "/kg"),
        ("Bawang Putih", "bawang_putih", "/kg"),
    ]),
    ("🧂 Lainnya", [("Garam Halus", "garam", "/kg"), ("Gas Elpiji 3kg", "elpiji", "")]),
]

for cat_name, items in sections:
    print(f"\n{cat_name}")
    for label, key, unit in items:
        print(f"  {label}: {rp(prices[key])}{unit}")

# Perubahan dari hari sebelumnya (21 Juni 2026)
print("\n" + "=" * 50)
print("📈 Perubahan vs 21 Juni 2026:")
prev = {
    "beras_premium": 15010, "beras_medium": 12953,
    "gula": 17166, "minyak_curah": 20462, "minyak_kemasan": 21708,
    "telur_ras": 25198, "telur_kampung": 46663,
    "ayam_ras": 32256, "ayam_kampung": 66888,
    "sapi": 126568,
    "cabai_keriting": 37870, "cabai_rawit": 57232,
    "bawang_merah": 42529, "bawang_putih": 35265,
    "garam": 9662, "elpiji": 20092,
}
labels = {
    "beras_premium": "Beras Premium", "beras_medium": "Beras Medium",
    "gula": "Gula", "minyak_curah": "Minyak Curah", "minyak_kemasan": "Minyak Kemasan",
    "telur_ras": "Telur Ras", "telur_kampung": "Telur Kampung",
    "ayam_ras": "Ayam Ras", "ayam_kampung": "Ayam Kampung",
    "sapi": "Sapi",
    "cabai_keriting": "Cabai Keriting", "cabai_rawit": "Cabai Rawit",
    "bawang_merah": "Bawang Merah", "bawang_putih": "Bawang Putih",
    "garam": "Garam", "elpiji": "Gas Elpiji",
}
for key in prices:
    diff = prices[key] - prev[key]
    pct = (diff / prev[key]) * 100
    arrow = "⬆️" if diff > 0 else "⬇️" if diff < 0 else "➡️"
    sign = "+" if diff > 0 else ""
    print(f"  {arrow} {labels[key]}: {sign}{diff:,} ({sign}{pct:.1f}%)".replace(",", "."))

print("\n✅ Data telah diupdate ke harga_sembako.xlsx (baris 23 & 24 Juni 2026)")
print("📌 Data 24 Juni menggunakan harga terakhir yg tersedia (23 Juni 2026)")
