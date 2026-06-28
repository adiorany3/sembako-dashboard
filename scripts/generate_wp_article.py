#!/usr/bin/env python3
"""
WordPress Article Generator v3 — Catatan Insani
================================================
Prinsip: judul DAN konten harus koheren. Setiap artikel = tulisan utuh.
Data real dari dashboard dipakai langsung di konten (bukan template).
"""

import json, random, os
from datetime import datetime
from pathlib import Path
import urllib.request

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WP_DIR = DATA_DIR / "wp_articles"
WP_DIR.mkdir(exist_ok=True)


def fetch_api(endpoint):
    try:
        url = f"http://127.0.0.1:5000/api/{endpoint}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("data", [])
    except Exception:
        return []


def fmt(n):
    return f"Rp{n:,.0f}".replace(",", ".")


def categorize_prices(items):
    """Sort items into categories."""
    cats = {
        "hewan_hidup": [],
        "daging": [],
        "telur": [],
        "olah": [],
        "jasa": [],
        "packaging": [],
        "supermarket": [],
    }
    for it in items:
        name = (it.get("produk") or it.get("komoditas") or "").lower()
        price = it.get("harga_rata") or it.get("harga") or 0
        src = (it.get("sumber") or "").lower()
        if not price:
            continue
        entry = (it.get("produk") or it.get("komoditas", ""), price, src)

        if "jasa" in name or "pemotongan" in name or "cold" in name or "transportasi" in name:
            cats["jasa"].append(entry)
        elif "hidup" in name:
            cats["hewan_hidup"].append(entry)
        elif "daging" in name or "fillet" in name or "marge" in name or "liver" in name or "feet" in name:
            cats["daging"].append(entry)
        elif "telur" in name:
            cats["telur"].append(entry)
        elif "sosis" in name or "nugget" in name:
            cats["olah"].append(entry)
        elif "kardus" in name or "plastik" in name or "label" in name or "code date" in name:
            cats["packaging"].append(entry)
        elif "superindo" in src or "hypermart" in src or "carrefour" in src:
            cats["supermarket"].append(entry)
    return cats


def make_table(rows, title=""):
    """Build HTML table from list of (name, price, source) tuples."""
    if not rows:
        return ""
    html = f'<h4>{title}</h4>\n<table style="width:100%;border-collapse:collapse;font-size:14px;margin:10px 0">\n'
    html += '<tr style="background:#0073aa;color:#fff"><th style="padding:6px;text-align:left">Komoditas</th><th style="padding:6px;text-align:right">Harga/kg</th><th style="padding:6px;text-align:left">Sumber</th></tr>\n'
    for name, price, src in rows:
        html += f'<tr><td style="padding:5px;border-bottom:1px solid #eee">{name}</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">{fmt(price)}</td><td style="padding:5px;border-bottom:1px solid #eee;color:#888">{src}</td></tr>\n'
    html += "</table>\n"
    return html


# ================================================================
# 7 ARTICLE TYPES — each returns {title, category, body}
# ================================================================


def art_1_harga_hari_ini(cats, sentimen, ds):
    """Ringkasan harga lengkap hari ini — hewan hidup, daging, telur."""
    hidup = cats["hewan_hidup"][:6]
    daging = cats["daging"][:6]
    telur = cats["telur"][:4]
    olah = cats["olah"][:4]

    pos = sum(1 for s in sentimen if "positif" in str(s.get("sentimen", "")).lower())
    neg = sum(1 for s in sentimen if "negatif" in str(s.get("sentimen", "")).lower())
    total_s = pos + neg
    tren_txt = f"Positif ({pos}/{total_s} data)" if pos > neg else f"Waspada ({neg}/{total_s} data negatif)" if neg > pos else "Netral"

    # Average prices for summary
    avg_hidup = sum(p for _, p, _ in hidup) / len(hidup) if hidup else 0
    avg_daging = sum(p for _, p, _ in daging) / len(daging) if daging else 0

    body = f"""<p>Berikut rangkuman harga peternakan terkini per <strong>{ds}</strong> berdasarkan data monitoring dari berbagai pasar dan sumber.</p>

<h4>Hewan Hidup (Basis Peternak)</h4>
{make_table(hidup)}

<h4>Daging Segar</h4>
{make_table(daging)}

<h4>Telur</h4>
{make_table(telur)}

<h4>Produk Olahan</h4>
{make_table(olah)}

<h4>Ringkasan</h4>
<p>Rata-rata harga hewan hidup berkisar <strong>{fmt(avg_hidup)}/kg</strong>, sedangkan daging segar di kisaran <strong>{fmt(avg_daging)}/kg</strong>. Sentimen pasar: <strong>{tren_txt}</strong>.</p>
<p>Peternak perlu memantau pergerakan harga mingguan untuk menentukan timing beli pakan dan jual ternak yang tepat.</p>"""

    return {
        "title": f"Update Harga Peternakan {ds}: Hewan Hidup, Daging & Telur",
        "category": "Update Harga",
        "body": body,
    }


def art_2_selisih_grosir_eceran(cats, ds):
    """Analisis selisih harga grosir vs eceran — peluang untuk peternak."""
    daging = cats["daging"]
    telur = cats["telur"]

    # Find grosir vs eceran pairs
    pairs = []
    grosir_items = [(n, p, s) for n, p, s in daging + telur if "grosir" in s.lower() or "kim" in s.lower() or "peternakan" in s.lower()]
    eceran_items = [(n, p, s) for n, p, s in daging + telur if "eceran" in s.lower() or "sm" in s.lower()]

    # Match by similar product name
    for gn, gp, gs in grosir_items:
        for en, ep, es in eceran_items:
            # Simple match: both contain "ayam" or both contain "sapi" or both contain "telur"
            for keyword in ["ayam", "sapi", "telur", "kambing"]:
                if keyword in gn.lower() and keyword in en.lower():
                    if gp > 0 and ep > 0 and ep > gp:
                        margin = ep - gp
                        pct = (margin / gp) * 100
                        pairs.append((gn, gp, en, ep, margin, pct))
                        break

    pairs = pairs[:4]  # max 4 pairs

    if not pairs:
        pairs_data = "<p>Data selisih grosir vs eceran belum cukup untuk analisis hari ini. Harga eceran umumnya 15-25% lebih tinggi dari harga grosir/peternakan.</p>"
    else:
        rows = ""
        for gn, gp, en, ep, margin, pct in pairs:
            rows += f"<tr><td>{gn}</td><td>{fmt(gp)}</td><td>{en}</td><td>{fmt(ep)}</td><td><strong>{fmt(margin)}</strong></td><td>{pct:.0f}%</td></tr>\n"
        pairs_data = f"""<table style="width:100%;border-collapse:collapse;font-size:14px;margin:10px 0">
<tr style="background:#0073aa;color:#fff"><th style="padding:6px">Grosir</th><th style="padding:6px">Harga Grosir</th><th style="padding:6px">Eceran</th><th style="padding:6px">Harga Ecer</th><th style="padding:6px">Selisih</th><th style="padding:6px">Margin %</th></tr>
{rows}</table>"""

    body = f"""<p>Salah satu peluang terbesar bagi peternak adalah menjual langsung ke konsumen atau retail, bukan hanya ke bandar. Berikut analisis selisih harga grosir vs eceran per <strong>{ds}</strong>.</p>

{pairs_data}

<h4>Mengapa Selisih Ini Ada?</h4>
<ul>
<li><strong>Biaya distribusi</strong> — transportasi, cold chain, penanganan</li>
<li><strong>Biaya ritel</strong> — sewa tempat, listrik, pegawai</li>
<li><strong>Margin pedagang</strong> — keuntungan untuk rantai pasok</li>
<li><strong>Resiko kerusakan</strong> — produk segar punya shelf life pendek</li>
</ul>

<h4>Bagaimana Peternak Bisa Memanfaatkan?</h4>
<ol>
<li><strong>Jual langsung di pasar tradisional</strong> — margin lebih tinggi, tapi perlu waktu dan tenaga.</li>
<li><strong>Kerja sama dengan warung/katering</strong> — harga di atas grosir, di bawah eceran. Win-win.</li>
<li><strong>olah sendiri</strong> — nugget, sosis, abon dari daging/sisa. Margin jauh lebih besar.</li>
<li><strong>Branding sederhana</strong> — kemasan rapi + label = bisa jual lebih mahal dari pasar.</li>
</ol>

<h4>Contoh Potensi</h4>
<p>Jika kamu menjual ayam potong Rp{fmt(38000)}/kg ke bandar, tapi bisa jual Rp{fmt(44000)}/kg ke warung — selisih Rp{fmt(6000)}/kg. Untuk 100 kg/hari = Rp{fmt(600000)}/hari = Rp{fmt(18000000)}/bulan tambahan. Tanpa tambah ternak.</p>"""

    return {
        "title": f"Selisih Harga Grosir vs Eceran ({ds}): Peluang untuk Peternak",
        "category": "Analisis Pasar",
        "body": body,
    }


def art_3_biaya_produksi(cats, ds):
    """Breakdown biaya produksi dari data jasa + packaging."""
    jasa = cats["jasa"]
    pak = cats["packaging"]

    body_sections = ""

    if jasa:
        body_sections += make_table(jasa, "Biaya Jasa & Logistik")
    else:
        body_sections += '<p>Data biaya jasa belum tersedia.</p>'

    if pak:
        body_sections += make_table(pak, "Biaya Kemasan")
    else:
        body_sections += '<p>Data biaya kemasan belum tersedia.</p>'

    # Find slaughter cost
    sapi_cut = next((p for n, p, _ in jasa if "sapi" in n.lower() and "besar" not in n.lower()), None)
    kambing_cut = next((p for n, p, _ in jasa if "kambing" in n.lower()), None)

    body = f"""<p>Biaya produksi peternakan bukan hanya soal pakan dan bibit. Banyak komponen tersembunyi yang sering terlupakan. Berikut rincian berdasarkan data terkini.</p>

{body_sections}

<h4>Contoh Rincian Biaya Produksi Ayam Broiler (per ekor)</h4>
<table style="width:100%;border-collapse:collapse;font-size:14px;margin:10px 0">
<tr style="background:#0073aa;color:#fff"><th style="padding:6px;text-align:left">Komponen</th><th style="padding:6px;text-align:right">Estimasi</th></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">DOC (anak ayam)</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">Rp4.500-5.500</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Pakan (35-40 hari)</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">Rp25.000-30.000</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Obat & vaksin</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">Rp1.500-2.000</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Energi (listrik air)</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">Rp1.000-1.500</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Kemasan & label</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:right">Rp500-1.000</td></tr>
<tr style="background:#f0f0f0;font-weight:bold"><td style="padding:6px">Total biaya</td><td style="padding:6px;text-align:right">Rp32.500-40.000</td></tr>
</table>

<p>Jika harga jual Rp{fmt(38000)}/kg dan berat akhir 2 kg = Rp76.000/ekor. Laba bersih: Rp{fmt(76000-40000)}-{fmt(76000-32500)}/ekor. Untuk 1.000 ekor: Rp{fmt(36000000)}-{fmt(43500000)}/siklus.</p>

<h4>Yang Sering Terlupakan</h4>
<ul>
<li><strong>Susu formula anak</strong> — kalau ternak sapi perah, ini komponen besar.</li>
<li><strong>Kerusakan/kematian</strong> — budget 3-5% dari total biaya sebagai cadangan.</li>
<li><strong>Kerusakan peralatan</strong> — kipas, lampu, waterer. Siapkan dana perbaikan.</li>
<li><strong>Biaya tenaga kerja</strong> — kalau ada karyawan, hitung UMR lokal.</li>
</ul>"""

    return {
        "title": f"Rincian Biaya Produksi Peternakan ({ds}): Jasa, Kemasan & Logistik",
        "category": "Optimasi Biaya",
        "body": body,
    }


def art_4_olahan_ayam(cats, ds):
    """Fokus produk olahan ayam — nugget, sosis, fillet."""
    daging_ayam = [(n, p, s) for n, p, s in cats["daging"] if "ayam" in n.lower()]
    olah = cats["olah"]
    supermarket = [(n, p, s) for n, p, s in cats["supermarket"] if "ayam" in n.lower() or "sosis" in n.lower() or "nugget" in n.lower()]

    body = f"""<p>Produk olahan ayam punya margin yang jauh lebih tinggi dibanding daging mentah. Berikut peluang yang bisa dimanfaatkan peternak.</p>

<h4>Harga Bahan Baku (Ayam)</h4>
{make_table(daging_ayam, "Harga Ayam Mentah")}

<h4>Harga Produk Olahan</h4>
{make_table(olah, "Produk Olahan")}

<h4>Harga di Supermarket</h4>
{make_table(supermarket, "Harga Supermarket")}

<h4>Analisis Margin</h4>"""

    # Calculate margin if data available
    if daging_ayam and olah:
        avg_raw = sum(p for _, p, _ in daging_ayam) / len(daging_ayam)
        for name, price, src in olah:
            margin = price - avg_raw
            pct = (margin / avg_raw * 100) if avg_raw else 0
            body += f"<p><strong>{name}</strong>: bahan baku ~{fmt(avg_raw)}/kg → harga jual {fmt(price)}/kg → margin {fmt(margin)}/kg ({pct:.0f}%)</p>\n"
    else:
        body += "<p>Data bahan baku belum cukup untuk kalkulasi margin.</p>"

    body += f"""
<h4>Mulai Produksi Olahan Sendiri</h4>
<ol>
<li><strong>Nugget ayam</strong> — bahan: ayam giling, tepung roti, telur, bumbu. Modal kecil, nilai tambah besar.</li>
<li><strong>Sosis ayam</strong> — bahan: ayam giling, tapioka, bumbu, kulit sosis. Butuh cetakan sosis.</li>
<li><strong>Ayam fillet</strong> — potong tanpa tulang. Butuh keterampilan, tapi harga jual 2-3x lipat daging ayam biasa.</li>
<li><strong>Abon ayam</strong> — olahan dari ayam rebus + bumbu. Shelf life panjang, cocok untuk oleh-oleh.</li>
</ol>

<h4>Tips Penting</h4>
<ul>
<li>Gunakan bahan segar — kualitas rasa menentukan repeat order.</li>
<li>Kemasan rapi dan bersih — kesan pertama penting.</li>
<li>Mulai dari skala kecil (10-20 kg/hari), test market dulu.</li>
<li>Daftarkan ke PIRT (Pangan Industri Rumah Tangga) untuk legalitas.</li>
</ul>"""

    return {
        "title": f"Produk Olahan Ayam ({ds}): Peluang Margin Tinggi untuk Peternak",
        "category": "Peluang Bisnis",
        "body": body,
    }


def art_5_hewan_ternak(cats, ds):
    """Fokus hewan ternak hidup — ayam, kambing, sapi, itik."""
    hidup = cats["hewan_hidup"]

    body = f"""<p>Harga hewan ternak hidup adalah titik awal sebelum masuk ke rantai pasok. Memahami perbandingan harga antar jenis ternak membantu peternak memilih mana yang paling menguntungkan.</p>

<h4>Harga Ternak Hidup</h4>
{make_table(hidup, "Harga Hewan Hidup (Basis Peternak)")}

<h4>Perbandingan per Jenis</h4>"""

    # Group by type
    types = {}
    for name, price, src in hidup:
        key = "Sapi" if "sapi" in name.lower() else "Kambing" if "kambing" in name.lower() else "Ayam" if "ayam" in name.lower() else "Itik" if "itik" in name.lower() else "Lain"
        types.setdefault(key, []).append((name, price))

    for tipe in ["Ayam", "Kambing", "Sapi", "Itik"]:
        items = types.get(tipe, [])
        if items:
            avg = sum(p for _, p in items) / len(items)
            body += f"<p><strong>{tipe}</strong>: rata-rata {fmt(avg)}/kg. Range: {fmt(min(p for _, p in items))} - {fmt(max(p for _, p in items))}/kg</p>\n"

    body += f"""
<h4>Pertimbangan Memilih Ternak</h4>
<table style="width:100%;border-collapse:collapse;font-size:14px;margin:10px 0">
<tr style="background:#0073aa;color:#fff"><th style="padding:6px;text-align:left">Jenis</th><th style="padding:6px">Modal Awal</th><th style="padding:6px">Siklus</th><th style="padding:6px">Resiko</th></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Ayam Broiler</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Kecil</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">35-40 hari</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Rendah</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Ayam Kampung</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Kecil</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">3-4 bulan</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Rendah</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Kambing</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Sedang</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">6-8 bulan</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Sedang</td></tr>
<tr><td style="padding:5px;border-bottom:1px solid #eee">Sapi</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Besar</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">8-12 bulan</td><td style="padding:5px;border-bottom:1px solid #eee;text-align:center">Tinggi</td></tr>
</table>

<h4>Tips Memilih Bibit/Bakalan</h4>
<ul>
<li><strong>Cek kondisi fisik</strong> — mata cerah, nafsu makan baik, tidak lesu.</li>
<li><strong>Tanya asal usul</strong> — peternak terpercaya = riwayat kesehatan lebih jelas.</li>
<li><strong>Jangan tergiur murah</strong> — bibit murah tapi sakat = rugi di akhir.</li>
<li><strong>Pertimbangkan lokasi</strong> — ayam lebih cocok di dekat kota, sapi/kambing di lahan luas.</li>
</ul>"""

    return {
        "title": f"Harga Ternak Hidup ({ds}): Perbandingan Ayam, Kambing, Sapi & Itik",
        "category": "Panduan Ternak",
        "body": body,
    }


def art_6_supermarket_harga(cats, ds):
    """Analisis harga supermarket vs pasar tradisional."""
    sm = cats["supermarket"][:8]
    trad = [(n, p, s) for n, p, s in cats["daging"] + cats["telur"] if "superindo" not in s and "hypermart" not in s and "carrefour" not in s and "tokopedia" not in s and "shopee" not in s][:8]

    body = f"""<p>Harga di supermarket biasanya lebih mahal dari pasar tradisional. Tapi berapa sebenarnya selisihnya? Berikut perbandingan data terkini.</p>

<h4>Harga Supermarket</h4>
{make_table(sm, "Harga Supermarket (SM)")}

<h4>Harga Pasar Tradisional / Peternakan</h4>
{make_table(trad, "Harga Pasar Tradisional")}

<h4>Peluang untuk Peternak</h4>
<p>Supermarket membayar lebih mahal karena menuntut kualitas, konsistensi, dan kemasan yang rapi. Peternak bisa masuk ke rantai supermarket dengan:</p>
<ol>
<li><strong>Kualitas konsisten</strong> — ukuran, berat, dan tampilan yang seragam.</li>
<li><strong>Kemasan profesional</strong> — vakum, label, tanggal produksi jelas.</li>
<li><strong>Sertifikasi</strong> — HALAL, PIRT, atau sertifikat kesehatan hewan.</li>
<li><strong>Pengiriman terjadwal</strong> — supermarket butuh suplai harian/mingguan.</li>
</ol>

<h4>Alternatif: Jual Langsung Online</h4>
<ul>
<li><strong>Tokopedia/Shopee</strong> — harga di platform ini lebih mendekati harga pasar, bukan supermarket.</li>
<li><strong>Instagram/WhatsApp</strong> — jual langsung ke konsumen akhir, margin terbesar.</li>
<li><strong>Katering/Restoran</strong> — harga di atas grosir, below supermarket. Volume besar.</li>
</ul>"""

    return {
        "title": f"Harga Supermarket vs Pasar Tradisional ({ds}): Analisis untuk Peternak",
        "category": "Analisis Pasar",
        "body": body,
    }


def art_7_sentimen_pasar(cats, sentimen, ds):
    """Analisis sentimen pasar peternakan."""
    entries = sentimen[:10]
    items_html = ""
    for s in entries:
        headline = s.get("headline") or s.get("komoditas") or s.get("produk") or "Berita"
        sent = s.get("sentimen", "Netral")
        skor = s.get("score", s.get("skor", "-"))
        source = s.get("source", s.get("sumber", ""))
        tanggal = s.get("tanggal", "")
        warna = "green" if str(sent).upper() == "POSITIF" else "red" if str(sent).upper() == "NEGATIF" else "#666"
        items_html += f'<li><strong>{headline[:80]}</strong> <span style="color:{warna};font-weight:bold">({sent})</span> — {source}, {tanggal}</li>\n'

    # Sentiment summary
    pos = sum(1 for s in entries if "positif" in str(s.get("sentimen", "")).lower())
    neg = sum(1 for s in entries if "negatif" in str(s.get("sentimen", "")).lower())
    neu = len(entries) - pos - neg

    body = f"""<p>Sentimen pasar mencerminkan kondisi psikologis pelaku pasar terhadap suatu komoditas. Berikut data terkini per <strong>{ds}</strong>.</p>

<h4>Data Sentimen</h4>
<ul>{items_html}</ul>

<h4>Ringkasan</h4>
<table style="width:100%;border-collapse:collapse;font-size:14px;margin:10px 0">
<tr style="background:#0073aa;color:#fff"><th style="padding:6px">Positif</th><th style="padding:6px">Netral</th><th style="padding:6px">Negatif</th></tr>
<tr><td style="padding:8px;text-align:center;color:green;font-weight:bold;font-size:18px">{pos}</td><td style="padding:8px;text-align:center;font-size:18px">{neu}</td><td style="padding:8px;text-align:center;color:red;font-weight:bold;font-size:18px">{neg}</td></tr>
</table>

<h4>Artinya untuk Peternak</h4>
<ul>
<li><strong>Sentimen positif</strong> → permintaan kuat atau pasokan menipis. Harga berpotensi naik. Pertahankan stok, jangan buru-buru jual.</li>
<li><strong>Sentimen negatif</strong> → oversupply atau permintaan turun. Harga berpotensi turun. Jual lebih awal, kurangi stok.</li>
<li><strong>Sentimen netral</strong> → kondisi stabil. Fokus efisiensi biaya produksi.</li>
</ul>

<h4>Tindakan yang Bisa Diambil</h4>
<ol>
<li>Pantau sentimen minimal 2-3x seminggu — jangan tunggu data bulanan.</li>
<li>Gunakan data sentimen + harga bersamaan untuk keputusan beli/jual.</li>
<li>Manfaatkan sentimen negatif komoditas A untuk diversifikasi ke komoditas B.</li>
</ol>

<h4>Disclaimer</h4>
<p>Data sentimen dikumpulkan dari berbagai sumber berita dan analisis pasar. Bukan rekomendasi investasi. Selalu konsultasi dengan peternak berpengalaman di daerah Anda.</p>"""

    return {
        "title": f"Sentimen Pasar Peternakan ({ds}): {pos} Positif, {neg} Negatif, {neu} Netral",
        "category": "Analisis Pasar",
        "body": body,
    }


# ================================================================
# MAIN
# ================================================================

ALL_ARTICLES = [
    (art_1_harga_hari_ini, "prices"),
    (art_2_selisih_grosir_eceran, "prices"),
    (art_3_biaya_produksi, "prices"),
    (art_4_olahan_ayam, "prices"),
    (art_5_hewan_ternak, "prices"),
    (art_6_supermarket_harga, "prices"),
    (art_7_sentimen_pasar, "prices+sentimen"),
]


def main():
    now = datetime.now()
    ds = now.strftime("%d %B %Y")

    print("=" * 60)
    print("WordPress Article Generator v3")
    print("=" * 60)

    pet = fetch_api("peternakan")
    sent = fetch_api("sentimen")
    cats = categorize_prices(pet)

    print(f"  Peternakan: {len(pet)} items")
    print(f"  Sentimen: {len(sent)} items")
    print(f"  Hewan hidup: {len(cats['hewan_hidup'])}, Daging: {len(cats['daging'])}, Telur: {len(cats['telur'])}")

    # Pick article (rotate daily)
    random.seed(now.timetuple().tm_yday)
    art_fn, _ = random.choice(ALL_ARTICLES)

    import inspect
    params = inspect.signature(art_fn).parameters
    kwargs = {}
    if "cats" in params:
        kwargs["cats"] = cats
    if "sentimen" in params:
        kwargs["sentimen"] = sent
    if "ds" in params:
        kwargs["ds"] = ds

    article = art_fn(**kwargs)

    print(f"\n{'=' * 60}")
    print(f"Title:    {article['title']}")
    print(f"Category: {article['category']}")
    print(f"{'=' * 60}")

    # Save
    html_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.html"
    meta_path = WP_DIR / f"{now.strftime('%Y-%m-%d')}.json"

    html_path.write_text(article["body"], encoding="utf-8")
    meta_path.write_text(json.dumps({
        "title": article["title"],
        "category": article["category"],
        "content": article["body"],
        "date": ds,
        "generated_at": now.isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nFiles saved:")
    print(f"  HTML: {html_path}")
    print(f"  Meta: {meta_path}")
    print(f"\nOpen http://43.153.196.161:5000/article to copy.")


if __name__ == "__main__":
    main()
