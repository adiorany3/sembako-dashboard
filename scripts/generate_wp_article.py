#!/usr/bin/env python3
"""
WordPress Article Generator v2 — Catatan Insani
================================================
Title and body always coherent. Each article = one complete blog post.
"""

import json, os, random
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WP_DIR = DATA_DIR / "wp_articles"
WP_DIR.mkdir(exist_ok=True)


def fetch(endpoint):
    import urllib.request
    try:
        url = f"http://127.0.0.1:5000/api/{endpoint}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return {"data": []}


def get_prices(items, n=8):
    result = []
    for item in items[-n:]:
        name = item.get("produk", item.get("komoditas", item.get("nama", "")))
        price = item.get("harga_rata", item.get("harga", item.get("price", 0)))
        if name and isinstance(price, (int, float)) and price > 0:
            result.append((name, price))
    return result


def fmt(n):
    return f"Rp{n:,.0f}".replace(",", ".")


def price_table_html(prices, max_rows=6):
    rows = ""
    for name, price in prices[:max_rows]:
        rows += f'<tr><td style="padding:6px;border-bottom:1px solid #eee">{name}</td><td style="padding:6px;border-bottom:1px solid #eee">{fmt(price)}/kg</td></tr>\n'
    if not rows:
        rows = '<tr><td colspan="2" style="padding:6px;color:#999">Data sedang diperbarui</td></tr>\n'
    return f'''<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:14px">
<tr style="background:#0073aa;color:#fff"><th style="padding:8px;text-align:left">Komoditas</th><th style="padding:8px;text-align:left">Harga</th></tr>
{rows}</table>'''


# ================================================================
# ARTICLE DEFINITIONS — each returns {title, category, content}
# ================================================================

def art_harga_update(ds, prices, sentimen):
    """Harga terkini + rekomendasi beli/jual."""
    pos = sum(1 for s in (sentimen or []) if "positif" in str(s.get("sentimen", "")).lower())
    neg = sum(1 for s in (sentimen or []) if "negatif" in str(s.get("sentimen", "")).lower())
    tren = "positif" if pos >= neg else "perlu waspada"
    return {
        "title": f"Harga Ternak & Pakan Hari Ini ({ds}): Update Lengkap",
        "category": "Update Harga",
        "content": f"""<p>Memantau harga bahan pakan dan produk ternak secara rutin membantu peternak menentukan kapan waktu terbaik untuk beli pakan, kapan harus jual ternak, dan bagaimana mengelola cash flow.</p>
<p>Berikut ringkasan harga terkini periode <strong>{ds}</strong> berdasarkan data monitoring pasar.</p>
<h4>Daftar Harga</h4>
{price_table_html(prices)}
<h4>Analisis Singkat</h4>
<p>Kondisi pasar saat ini cenderung <strong>{tren}</strong>. {"Sebanyak " + str(pos) + " dari " + str(pos+neg) + " data menunjukkan tren positif." if pos+neg > 0 else "Data sentimen masih terkumpul."}</p>
<p>Beberapa hal yang perlu diperhatikan:</p>
<ul>
<li>Pantau perubahan harga bahan pakan mingguan — beli saat turun, tahan stok saat naik.</li>
<li>Harga produk ternak relatif stabil. Pastikan biaya produksi tetap terkendali.</li>
<li>Perhatikan fluktuasi harga global yang bisa mempengaruhi bahan impor (bungkil kedelai, premix).</li>
</ul>
<h4>Rekomendasi</h4>
<ol>
<li>Catat harga mingguan, bandingkan dengan minggu sebelumnya.</li>
<li>Jangan panic buying saat harga naik sedikit — tunggu 2-3 hari.</li>
<li>Evaluasi supplier secara berkala untuk dapat harga terbaik.</li>
<li>Simpan catatan transaksi untuk analisis laba rugi bulanan.</li>
</ol>"""
    }


def art_optimasi_pakan(ds, prices):
    """Hemat biaya pakan 20-30%."""
    protein = [(n, p) for n, p in prices if any(k in n.lower() for k in ["kedelai", "bungkil", "ampas", "dedak"])]
    if len(protein) < 2:
        protein = [("Bungkil Kedelai", 5500), ("Dedak Padi", 3200), ("Ampas Tahu", 2500), ("Jagung Kuning", 4800)]
    pl = "".join(f"<li><strong>{n}</strong>: {fmt(p)}/kg</li>" for n, p in protein[:4])
    return {
        "title": f"Optimasi Biaya Pakan Ternak: Strategi Hemat 20-30%",
        "category": "Optimasi Biaya",
        "content": f"""<p>Pakan menyumbang <strong>60-70% biaya peternakan</strong>. Efisiensi di area ini langsung berdampak pada keuntungan. Berikut strategi yang bisa diterapkan mulai sekarang.</p>
<h4>Harga Bahan Pakan Alternatif</h4>
<ul>{pl}</ul>
<h4>Pakan Komersial vs Formulasi Mandiri</h4>
<ul>
<li><strong>Pakan komersial</strong>: Rp7.000-8.500/kg</li>
<li><strong>Formulasi mandiri</strong>: Rp5.000-6.000/kg</li>
<li><strong>Hemat per kg</strong>: Rp1.500-2.500</li>
<li><strong>Hemat per 1.000 ekor/bulan (broiler)</strong>: Rp1.500.000-2.500.000</li>
</ul>
<h4>Contoh Ransum Broiler Finisher (Mandiri)</h4>
<ol>
<li>Jagung kuning 50% — sumber energi utama</li>
<li>Bungkil kedelai 20% — sumber protein</li>
<li>Dedak padi 15% — serat + energi</li>
<li>Konsentrat premix 10% — vitamin & mineral</li>
<li>Minyak sawit 5% — energy density</li>
</ol>
<p>Bisa ditambah ampas tahu 10-15% untuk ganti sebagian bungkil kedelai jika harganya lebih murah di daerah Anda.</p>
<h4>Tips Penghematan Tambahan</h4>
<ul>
<li><strong>Fermentasi pakan</strong> — tingkatkan daya cerna. Campur ragi + gula, diamkan 24 jam.</li>
<li><strong>Beli saat panen raya</strong> — jagung biasanya murah Juli-September.</li>
<li><strong>Simpan dengan benar</strong> — gunakan wadah kedap udara. Pakan basi = buang uang.</li>
<li><strong>Evaluasi FCR</strong> — hitung tiap periode. Target broiler: 1.6-1.8.</li>
</ul>
<h4>Kesimpulan</h4>
<p>Optimasi pakan = menggunakan bahan tepat dengan harga tepat. Mulai catat pengeluaran pakan bulanan, evaluasi, dan sesuaikan formulasi. Selisih kecil per kg × ribuan kg = perbedaan signifikan di akhir tahun.</p>"""
    }


def art_tips_pemula(ds, prices):
    """Panduan lengkap untuk peternak pemula."""
    ayam = [(n, p) for n, p in prices if "ayam" in n.lower()]
    sapi = [(n, p) for n, p in prices if "sapi" in n.lower()]
    if sapi:
        ref = f"Saat ini harga daging sapi di kisaran {fmt(sapi[0][1])}/kg. Ternak sapi potong menjanjikan margin baik per ekor, meski modal awal lebih besar."
    elif ayam:
        ref = f"Harga daging ayam segar {fmt(ayam[0][1])}/kg. Ternak broiler jadi pilihan populer pemula karena siklus panen cepat."
    else:
        ref = "Kondisi pasar cukup stabil. Waktu yang baik untuk memulai."
    return {
        "title": f"Mulai Beternak dari Nol: Panduan Praktis untuk Pemula ({ds})",
        "category": "Panduan Pemula",
        "content": f"""<p>Banyak orang tertarik beternak setelah melihat harga produk hewan terus naik. Tapi mulai tanpa panduan bisa berujung kerugian. Berikut langkah-langkah praktis yang perlu diperhatikan.</p>
<h4>Pilih Jenis Ternak</h4>
<ul>
<li><strong>Ayam broiler</strong> — siklus 35-40 hari, modal kecil, permintaan tinggi. Cocok pemula.</li>
<li><strong>Ayam petelur</strong> — penghasilan rutin dari telur, butuh kandang lebih baik.</li>
<li><strong>Kambing/domba</strong> — modal sedang, permintaan tinggi menjelang Idul Adha.</li>
<li><strong>Sapi potong</strong> — modal besar, siklus 8-12 bulan, margin per ekor tinggi.</li>
</ul>
<p>{ref}</p>
<h4>Persiapan Kandang</h4>
<ol>
<li><strong>Lokasi</strong> — jauh dari pemukiman padat, akses jalan baik, dekat sumber air.</li>
<li><strong>Ventilasi</strong> — sirkulasi udara baik mencegah stres panas dan penyebaran penyakit.</li>
<li><strong>Drainase</strong> — kandang harus kering. Basah = bibit penyakit.</li>
<li><strong>Skala awal</strong> — mulai 100-500 ekor (broiler) sebelum expand.</li>
</ol>
<h4>Manajemen Kesehatan</h4>
<ul>
<li>Vaksinasi sesuai jadwal — ini wajib, bukan opsional.</li>
<li>Biosekuriti dasar: sepatu khusus kandang, disinfektan di pintu masuk.</li>
<li>Amati perilaku ternak setiap hari. Perubahan kecil = tanda awal masalah.</li>
<li>Siapkan isolasi untuk ternak sakit.</li>
</ul>
<h4>Catat Setiap Pengeluaran</h4>
<p>Banyak pemula gagal karena tidak tahu biaya produksi sebenarnya. Catat:</p>
<ul>
<li>Harga bibit/DOC per ekor</li>
<li>Biaya pakan per periode</li>
<li>Obat & vaksin</li>
<li>Listrik, air, tenaga kerja</li>
<li>Dana darurat 10-15% dari total budget</li>
</ul>
<p>Selisih harga jual - total biaya = laba bersih. Tanpa catatan, kamu tidak tahu apakah benar-benar untung.</p>
<h4>Langkah Pertama</h4>
<ol>
<li>Tentukan jenis ternak berdasarkan budget & lokasi</li>
<li>Riset 3-5 supplier pakan, bandingkan harga</li>
<li>Buat rancangan kandang sederhana</li>
<li>Siapkan dana darurat minimal 20%</li>
<li>Mulai kecil, belajar, baru scale up</li>
</ol>"""
    }


def art_biosekuriti(ds):
    """Kesehatan & pencegahan penyakit ternak."""
    return {
        "title": f"Biosekuriti Ternak: Protokol Pencegahan yang Wajib Diterapkan",
        "category": "Kesehatan Ternak",
        "content": f"""<p>Penyakit ternak bukan hanya ancaman kesehatan — tapi ancaman finansial serius. Satu wabak bisa menghabiskan investasi dalam hitungan hari. Pencegahan melalui biosekuriti jauh lebih murah daripada pengobatan.</p>
<h4>Apa Itu Biosekuriti?</h4>
<p>Serangkaian langkah pencegahan untuk membatasi masuknya dan penyebaran penyakit ke/dari area peternakan. Bukan cuma menyemprot disinfektan — tapi sistem yang menyeluruh.</p>
<h4>Protokol Dasar</h4>
<ol>
<li><strong>Kontrol akses</strong> — batasi orang masuk kandang. Ganti sepatu/baju kandang.</li>
<li><strong>Disinfektan pintu masuk</strong> — footbath wajib dilewati setiap kali.</li>
<li><strong>Karantina ternak baru</strong> — 7-14 hari sebelum bergabung dengan kawanan.</li>
<li><strong>Pisahkan area</strong> — anakan, pembesaran, dan produksi terpisah.</li>
<li><strong>Pengelolaan bangkai</strong> — kubur dalam atau bakar. Jangan buang sembarangan.</li>
</ol>
<h4>Jadwal Vaksinasi Unggas</h4>
<ul>
<li>Hari 1: ND+IB tetes mata/hidung</li>
<li>Hari 7-10: ND+IB ulang</li>
<li>Hari 14: IBD (Gumboro)</li>
<li>Hari 21: ND booster</li>
<li>Layer: ND booster tiap 3 bulan</li>
</ul>
<h4>Jadwal Vaksinasi Ternak Besar</h4>
<ul>
<li>Vaksin FMD (PMK) sesuai jadwal dinas peternakan</li>
<li>Dehelmintasi tiap 3-6 bulan</li>
<li>Vaksin Brucellosis untuk sapi perah</li>
</ul>
<h4>Tanda Ternak Sakit</h4>
<ul>
<li>Nafsu makan menurun drastis</li>
<li>Lebih diam dari biasanya</li>
<li>Bulu/kotoran tidak normal</li>
<li>Demam — sentuh hidung, harus lembab & dingin</li>
<li>Bengkak di bagian tubuh tertentu</li>
<li>Produksi telur/susu menurun</li>
</ul>
<p>Jika menemukan tanda ini, <strong>isolasi segera</strong> dan hubungi dokter hewan. Jangan obati sendiri.</p>
<h4>Biaya Pencegahan vs Pengobatan</h4>
<ul>
<li>Vaksin ND: Rp500-1.000/ekor</li>
<li>Disinfektan kandang: Rp200.000-500.000/bulan</li>
<li>Biaya wabak: Rp5.000.000-50.000.000</li>
</ul>
<p>Rasionya jelas. Biosekuriti bukan biaya — ini investasi.</p>"""
    }


def art_sapi_potong(ds, prices):
    """Panduan lengkap ternak sapi potong."""
    sapi = [(n, p) for n, p in prices if "sapi" in n.lower()]
    ref = f"Harga daging sapi saat ini {fmt(sapi[0][1])}/kg." if sapi else "Permintaan daging sapi terus meningkat."
    return {
        "title": f"Ternak Sapi Potong: Panduan dari Bibit hingga Panen ({ds})",
        "category": "Panduan Ternak",
        "content": f"""<p>{ref} Kebutuhan daging sapi nasional masih tergantung impor — peluang bagi peternak lokal masih terbuka lebar.</p>
<h4>Pemilihan Bibit</h4>
<ul>
<li><strong>Silsilah</strong> — cari dari indukan produktif. Crossbreed populer: Simental, Limousin, Brahman Cross.</li>
<li><strong>Berat</strong> — feeder ideal 200-250 kg. Sudah melewati fase rentan sakit.</li>
<li><strong>Fisik</strong> — tubuh berisi, mata cerah, nafsu makan baik.</li>
<li><strong>Usia</strong> — 12-18 bulan saat dibeli. Siap panen dalam 6-8 bulan.</li>
</ul>
<h4>Persiapan Kandang</h4>
<ol>
<li>Tipe: individu lebih mudah untuk pemula.</li>
<li>Ukuran: minimal 3x3m per ekor.</li>
<li>Air bersih tersedia 24 jam — sapi minum 30-50 liter/hari.</li>
<li>Alas: jerami/sekam, ganti 2x seminggu.</li>
</ol>
<h4>Ransum Pakan</h4>
<ul>
<li>Hijauan (rumput gajah, kolonjono): 30-40 kg/hari/ekor</li>
<li>Konsentrat (ampas tahu + bekatul + jagung): 5-8 kg/hari/ekor</li>
<li>Blok mineral / garam + kalsium</li>
<li>Air minum: bersih, tidak terbatas</li>
</ul>
<p>Rasio ideal: 70% hijauan + 30% konsentrat. Terlalu banyak konsentrat menyebabkan asidosis.</p>
<h4>Manajemen Pemeliharaan</h4>
<ul>
<li>Timbang berkala — sebelum masuk & sebelum jual.</li>
<li>Dehelmintasi tiap 3 bulan.</li>
<li>Vaksinasi sesuai jadwal dinas peternakan.</li>
<li>Kurangi stres transportasi saat pengiriman.</li>
</ul>
<h4>Analisis Biaya Kasar (Per Ekor)</h4>
<ul>
<li>Bibit 250 kg: Rp18-22 juta</li>
<li>Pakan 8 bulan: Rp8-12 juta</li>
<li>Obat & vaksin: Rp500rb-1 juta</li>
<li>Biaya lain: Rp2-3 juta</li>
<li><strong>Total modal</strong>: Rp28-38 juta</li>
<li><strong>Target jual</strong>: 350-400 kg × Rp75-80rb = Rp26-32 juta</li>
</ul>
<p>Analisis kasar — margin tergantung harga bibit, efisiensi pakan, dan harga jual. Konsultasi peternak lokal untuk data akurat di daerah Anda.</p>
<h4>Tips Sukses</h4>
<ol>
<li>Jangan beli bibit murah — kualitas menentukan hasil akhir.</li>
<li>Investasi kandang baik — kandang buruk = stres = pertumbuhan lambat.</li>
<li>Catat setiap pengeluaran.</li>
<li>Jalin hubungan dengan beberapa rumah potong.</li>
</ol>"""
    }


def art_sentimen(ds, sentimen):
    """Analisis sentimen pasar."""
    entries = (sentimen or [])[:5]
    if not entries:
        return art_harga_update(ds, [], sentimen)
    items = "".join(
        f'<li><strong>{s.get("komoditas", s.get("produk", ""))}</strong>: {s.get("sentimen", "netral")} (skor: {s.get("skor", s.get("score", "-"))})</li>'
        for s in entries
    )
    return {
        "title": f"Analisis Sentimen Pasar Peternakan ({ds}): Apa Kata Data?",
        "category": "Analisis Pasar",
        "content": f"""<p>Memahami sentimen pasar membantu peternak melihat gambaran besar — apakah kondisi berpihak atau perlu waspada.</p>
<h4>Sentimen Terkini</h4>
<ul>{items}</ul>
<h4>Apa Artinya untuk Peternak?</h4>
<p>Sentimen positif = permintaan kuat atau pasokan terbatas, potensi harga naik. Sentimen negatif = oversupply atau penurunan permintaan.</p>
<h4>Strategi Berdasarkan Sentimen</h4>
<ol>
<li><strong>Positif</strong> → pertahankan produksi. Jangan buru-buru jual massal — tunggu puncak harga.</li>
<li><strong>Negatif</strong> → kurangi stok, jual lebih awal untuk minimalkan kerugian.</li>
<li><strong>Netral</strong> → stabilkan operasional, fokus efisiensi biaya.</li>
</ol>
<h4>Pantau Terus</h4>
<p>Sentimen bisa berubah cepat. Pantau data minimal 2-3x seminggu untuk mengantisipasi perubahan pasar. Gunakan dashboard monitoring untuk data real-time.</p>"""
    }


def art_jelang_hari_raya(ds):
    """Persiapan ternak menjelang hari raya."""
    return {
        "title": f"Persiapan Ternak Menjelang Hari Raya: Strategi Untung Maksimal",
        "category": "Strategi Bisnis",
        "content": f"""<p>Hari raya = puncak permintaan daging. Peternak yang mempersiapkan diri dari jauh hari bisa mendapatkan margin terbaik. Berikut strategi yang perlu diperhatikan.</p>
<h4>Timeline Persiapan</h4>
<ol>
<li><strong>3-4 bulan sebelum</strong> — mulai pembesaran. Pastikan bibit/DOC berkualitas.</li>
<li><strong>2 bulan sebelum</strong> — evaluasi pertumbuhan. Sesuaikan pakan jika perlu.</li>
<li><strong>1 bulan sebelum</strong> — pastikan kandang siap, jalin hubungan dengan pembeli.</li>
<li><strong>2 minggu sebelum</strong> — distribusi ke pengepul/bandar mulai aktif. Pantau harga harian.</li>
</ol>
<h4>Manajemen Stok</h4>
<ul>
<li>Jangan tahan terlalu lama — biaya pakan terus berjalan.</li>
<li>Jual bertahap, jangan sekaligus saat harga belum puncak.</li>
<li>Siapkan 2-3 channel penjualan (bandar langsung, pasar modern, rumah potong).</li>
</ul>
<h4>Optimasi Kualitas</h4>
<ul>
<li>Tingkatkan pakan 2-4 minggu sebelum jual untuk bobot maksimal.</li>
<li>Pastikan ternak sehat — sakit saat mendekati panen = kerugian besar.</li>
<li>Grooming sederhana: bersihkan tubuh sebelum dijual.</li>
</ul>
<h4>Harga & Negosiasi</h4>
<ul>
<li>Pantau harga H-30, H-14, H-7 — cari pola.</li>
<li>Jangan langsung terima tawaran pertama bandar — bandingkan minimal 2-3 pembeli.</li>
<li>Harga naik tajam menjelang H-3 sampai H-1. Tapi juga bisa turun jika pasokan berlebih.</li>
</ul>
<h4>Risiko & Mitigasi</h4>
<ul>
<li><strong>Penurunan harga</strong> — diversifikasi penjualan (langsung ke konsumen, katering).</li>
<li><strong>Penyakit mendadak</strong> — vaksinasi tepat waktu, biosekuriti ketat.</li>
<li><strong>Keterlambatan pembayaran</strong> — pastikan kesepakatan tertulis.</li>
</ul>"""
    }


# ================================================================
# MAIN — pick article based on day, generate, save
# ================================================================

ALL_ARTICLES = [
    art_harga_update,
    art_optimasi_pakan,
    art_tips_pemula,
    art_biosekuriti,
    art_sapi_potong,
    art_sentimen,
    art_jelang_hari_raya,
]


def main():
    now = datetime.now()
    ds = now.strftime("%d %B %Y")

    print("=" * 60)
    print("WordPress Article Generator v2 — Catatan Insani")
    print("=" * 60)

    # Fetch data
    print("\nFetching dashboard data...")
    pet = fetch("peternakan")
    sent = fetch("sentimen")
    prices = get_prices(pet.get("data", []))
    sent_list = sent.get("data", [])
    print(f"  Peternakan: {'OK' if prices else 'empty'}")
    print(f"  Sentimen: {'OK' if sent_list else 'empty'}")

    # Pick article (rotate daily, seed ensures same article all day)
    random.seed(now.timetuple().tm_yday)
    art_fn = random.choice(ALL_ARTICLES)

    # Call with appropriate args
    import inspect
    params = inspect.signature(art_fn).parameters
    kwargs = {}
    if "ds" in params:
        kwargs["ds"] = ds
    if "prices" in params:
        kwargs["prices"] = prices
    if "sentimen" in params:
        kwargs["sentimen"] = sent_list
    article = art_fn(**kwargs)

    print(f"\n{'=' * 60}")
    print(f"Title:    {article['title']}")
    print(f"Category: {article['category']}")
    print(f"Date:     {ds}")
    print(f"{'=' * 60}")

    # Build HTML file (for browser copy-paste)
    html = article["content"]

    # Save HTML (clean content only, for WordPress paste)
    html_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.html"
    html_path.write_text(html, encoding="utf-8")

    # Save JSON meta
    meta_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.json"
    meta_path.write_text(json.dumps({
        "title": article["title"],
        "category": article["category"],
        "content": html,
        "date": ds,
        "generated_at": now.isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nFiles saved:")
    print(f"  HTML: {html_path}")
    print(f"  Meta: {meta_path}")
    print(f"\nHow to publish:")
    print(f"  1. Buka http://43.153.196.161:5000/article")
    print(f"  2. Copy title & content")
    print(f"  3. Paste ke WordPress admin")


if __name__ == "__main__":
    main()
