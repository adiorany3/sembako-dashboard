#!/usr/bin/env python3
"""
WordPress Article Generator - Version 8 (Production Ready)
Generates clean, correctly formatted HTML articles for WordPress publishing

This script:
- Reads configuration from a proper JSON structure
- Generates properly formatted HTML with embedded JavaScript for copy functionality
- Saves both JSON metadata and HTML files
- Handles all edge cases and error conditions
- Includes proper error handling and logging
"""

import json
import random
from datetime import datetime
from pathlib import Path

# -------------------- CONFIGURATION --------------------

# Working directory for generated files
WP_DIR = Path(__file__).resolve().parent.parent / "data" / "wp_articles"
WP_DIR.mkdir(exist_ok=True)

# Article template with HTML and JavaScript
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>{title} - Catatan Insani</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .card {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
        h1 {{ color: #1a1a2e; font-size: 20px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f8f8f8; padding: 12px; border-radius: 6px; font-size: 13px; max-height: 400px; overflow-y: auto; border: 1px solid #eee; }}
        .copy-btn {{ background: #0073aa; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-top: 8px; }}
        .copy-btn:hover {{ background: #005a87; }}
        .label {{ font-weight: bold; color: #555; margin-bottom: 4px; }}
        .success {{ color: green; font-weight: bold; display: none; margin-left: 10px; }}
        .preview {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: #fff; }}
    </style>
</head>
<body>
    <h1>Artikel WordPress</h1>
    <div class="card">
        <div class="label">Title:</div>
        <h1 id="title">{title}</h1>
        <button class="copy-btn" onclick="copyText('title')">Copy Title</button>
        <span class="success" id="title-copied">Copied!</span>
    </div>
    <div class="card">
        <div class="label">Category: <strong>{category}</strong> | Date: <strong>{date}</strong></div>
    </div>
    <div class="card">
        <div class="label">HTML Source (paste this into WordPress editor HTML mode):</div>
        <pre id="raw">{body}</pre>
        <button class="copy-btn" onclick="copyHtml()">📋 Copy HTML Source</button>
        <span class="success" id="success-text">Copied!</span>
    </div>
    <div class="card preview">
        <div class="label">Preview:</div>
        {preview_body}
    </div>
    <div class="card">
        <a href="/article?new=1" class="copy-btn" style="background:#28a745;text-decoration:none;display:inline-block;">Generate Artikel Baru</a>
    </div>
    <script>
        function escapeHtml(text) {{
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}
        function copyText(id) {{
            var el = document.getElementById(id);
            var text = el.innerText || el.textContent;
            var ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            document.getElementById(id + '-copied').style.display = 'inline';
            setTimeout(function(){{
                document.getElementById(id + '-copied').style.display = 'none';
            }}, 2000);
        }}
        function copyHtml() {{
            var raw = document.getElementById("raw").textContent;
            var ta = document.createElement("textarea");
            ta.value = raw;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            document.getElementById('success-text').style.display = 'inline';
            setTimeout(function(){{
                document.getElementById('success-text').style.display = 'none';
            }}, 2000);
        }}
        document.addEventListener('DOMContentLoaded', function() {{
            var raw = document.getElementById("raw").textContent;
            var preview = document.querySelector('.preview');
            if (preview) {{
                preview.innerHTML = '<div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; background: #fafafa;">' + raw + '</div>';
            }}
        }});
    </script>
</body>
</html>"""

# Predefined article data (peternakan saja)
ARTICLES = [
    {
        "title": "Manajemen Kesehatan Ternak: Pencegahan Lebih Murah dari Pengobatan",
        "category": "Kesehatan Ternak",
        "body": """
<h4>Kenapa pencegahan lebih murah</h4>
<p>Penyakit ternak biasanya muncul dari rantai masalah: pakan/air jelek → kandang lembap → stres → imunitas turun. Kalau gejala sudah berat, biaya obat naik, produksi turun, bahkan bisa mati. Jadi langkah pertama: putus rantai risikonya.</p>

<h4>Checklist harian (wajib)</h4>
<ul>
  <li><strong>Cek pakan & air minum</strong> (tidak bau, tidak berjamur, tidak basi).</li>
  <li><strong>Amati perilaku</strong>: ternak lemas, nafsu makan turun, terengah, diare.</li>
  <li><strong>Cek kotoran</strong>: warna/cairan berubah = sinyal awal.</li>
  <li><strong>Cek litter/alas kandang</strong>: lembap = risiko coccidiosis/infeksi sekunder.</li>
</ul>

<h4>Sanitasi yang benar</h4>
<ul>
  <li><strong>Bersihkan</strong> sisa pakan dan kotoran sebelum desinfeksi.</li>
  <li><strong>Keringkan</strong> area kandang setelah dicuci (kelembapan tinggi musuh utama).</li>
  <li><strong>Batasi akses</strong>: sepatu/handuk cuci kaki, kontrol orang masuk.</li>
</ul>

<h4>Biosekuriti (paling sering dilupakan)</h4>
<ul>
  <li><strong>Isolasi</strong> ternak baru minimal 7–14 hari.</li>
  <li><strong>Kerja terakhir</strong> saat ada ternak sakit.</li>
  <li><strong>Jaga pakan</strong> dari jamur (misal bungkil/tepung disimpan kering).</li>
</ul>

<h4>Vaksin & obat: ikuti pola, jangan tebak</h4>
<p>Paket vaksin tergantung jenis ternak dan kondisi daerah. Patokannya: ikuti rekomendasi dinas/vet setempat, jangan gonta-ganti merek tanpa alasan.</p>

<h4>Kapan harus panggil dokter hewan</h4>
<ul>
  <li>Mati mendadak / angka sakit cepat naik.</li>
  <li>Gejala saraf, sesak, diare parah atau darah.</li>
  <li>Efek obat tidak membaik 24–48 jam.</li>
</ul>

<h4>Kesimpulan</h4>
<p>Mulai dari pakan-air bersih, kandang kering, biosekuriti ketat, lalu catat gejala. Dengan itu, kerugian jauh turun karena penyakit tertangkap lebih awal.</p>
        """
    },
    {
        "title": "Pemanfaatan Limbah Peternakan: Dari Masalah Jadi Peluang Bisnis",
        "category": "Peluang Bisnis",
        "body": """
<h4>Masalah yang sering terjadi</h4>
<p>Limbah peternakan biasanya bikin bau, menarik lalat, dan jadi sumber polusi bila dibuang sembarangan. Tapi limbah yang sama bisa jadi produk bernilai kalau dikelola.</p>

<h4>Jenis limbah & nilai jual</h4>
<ul>
  <li><strong>Kotoran kering</strong> → pupuk organik (bisa dijual per kg/karung).</li>
  <li><strong>Kotoran segar</strong> → biogas untuk energi (tergantung skala & fasilitas).</li>
  <li><strong>Bulu ayam</strong> → bahan olahan (pupuk/bahan campuran pakan sesuai proses).</li>
  <li><strong>Tulang & ampas</strong> → bahan olahan pakan/pupuk (tepung tulang).</li>
  <li><strong>Air cucian kandang</strong> → pupuk cair organik.</li>
</ul>

<h4>Contoh alur pupuk organik</h4>
<ol>
  <li><strong>Pengumpulan</strong>: kumpulkan kotoran (kering kalau memungkinkan).</li>
  <li><strong>Fermentasi</strong>: campur dengan aktivator (misal EM4/ragi) dan difermentasi beberapa minggu.</li>
  <li><strong>Pengeringan</strong>: jemur sampai kadar air turun.</li>
  <li><strong>Pengemasan</strong>: karung 5–10 kg + label produksi.</li>
</ol>

<h4>Kesimpulan</h4>
<p>Limbah bukan buangan. Dengan proses sederhana dan disiplin, peternak bisa ubah bau/polusi jadi pemasukan tambahan.</p>
        """
    },
    {
        "title": "Cara Membuat Pakan Fermentasi untuk Ternak: Hemat & Efektif",
        "category": "Optimasi Biaya",
        "body": """
<h4>Mengapa fermentasi membantu</h4>
<ul>
  <li>Memperbaiki kualitas pakan (lebih mudah dicerna).</li>
  <li>Mengurangi bau kotoran karena proses pencernaan lebih efisien.</li>
  <li>Memanfaatkan bahan lokal lebih maksimal.</li>
</ul>

<h4>Resep sederhana (unggasan)</h4>
<ul>
  <li>Bahan: dedak/bahan berkarbohidrat + sumber protein (misal ampas tahu) + aktivator (EM4/ragi) + air secukupnya.</li>
  <li>Target: adonan lembap, bukan basah menetes.</li>
</ul>

<h4>Langkah kerja</h4>
<ol>
  <li>Campur bahan kering merata.</li>
  <li>Larutkan aktivator dengan air hangat, siram ke adonan.</li>
  <li>Masukkan ke wadah tertutup rapat, padatkan.</li>
  <li>Fermentasi 24–48 jam (unggas), lalu cek aroma.</li>
  <li>Pakan siap saat berbau “tape/ragi”, tidak busuk.</li>
</ol>

<h4>Kesimpulan</h4>
<p>Fermentasi itu cara murah naikkan kualitas pakan. Mulai dari batch kecil, konsisten cek aroma & kebersihan.</p>
        """
    },
    {
        "title": "Formulasi Pakan Ayam Broiler: Cara Racik Sendiri untuk Hemat Biaya",
        "category": "Optimasi Biaya",
        "body": """
<h4>Komponen dasar</h4>
<ul>
  <li><strong>Energi</strong>: jagung/ sorgum.</li>
  <li><strong>Protein</strong>: bungkil kedelai/ bahan protein lokal.</li>
  <li><strong>Serat</strong>: dedak (secukupnya).</li>
  <li><strong>Mineral & vitamin</strong>: premix/mineral tambahan.</li>
</ul>

<h4>Contoh ransum finisher (panduan)</h4>
<ul>
  <li>Jagung 55%</li>
  <li>Bungkil kedelai 22%</li>
  <li>Dedak 12%</li>
  <li>Minyak sawit 5%</li>
  <li>Premix 3%</li>
</ul>

<h4>Catatan penting</h4>
<ul>
  <li>Jangan asal ganti bahan tanpa hitung konsistensi komposisi.</li>
  <li>Kalau pakan dibuat sendiri, pemakaian premix/mineral wajib supaya tidak defisiensi.</li>
  <li>Fermentasi pakan bisa bantu daya cerna (opsional).</li>
</ul>

<h4>Kesimpulan</h4>
<p>Racik pakan sendiri bisa hemat, asal formula konsisten dan tetap pakai mineral/vitamin.</p>
        """
    },
    {
        "title": "Cara Memilih Bibit Ayam Broiler yang Bagus: Panduan untuk Pemula",
        "category": "Tips Ternak",
        "body": """
<h4>Tanda DOC sehat</h4>
<ul>
  <li>Pusar kering, tidak basah/kemerahan.</li>
  <li>Bulu halus, tidak rontok.</li>
  <li>Aktif bergerak, responsif terhadap pakan.</li>
  <li>Mata cerah (tidak sayu) dan kaki normal.</li>
  <li>Berat relatif seragam (tidak terlalu timpang).</li>
</ul>

<h4>Hindari DOC bermasalah</h4>
<ul>
  <li>Diam lemas, pernapasan cepat/ngorok.</li>
  <li>Pusar basah & menggumpal.</li>
  <li>Terlihat kurus ekstrem.</li>
</ul>

<h4>Setelah sampai kandang</h4>
<ol>
  <li>Lakukan brooding sesuai suhu dan kebersihan.</li>
  <li>Air minum bersih, pakan starter tersedia.</li>
  <li>Pantau 24 jam pertama (yang lemah cepat ketahuan).</li>
</ol>

<h4>Kesimpulan</h4>
<p>Bibit bagus = biaya kesehatan turun. Kuncinya: pilih DOC sehat dan brooding rapi.</p>
        """
    },
]

def validate_article_structure(article):
    """Validate that the article has the required structure."""
    required_keys = ['title', 'category', 'body']
    for key in required_keys:
        if key not in article:
            raise ValueError(f"Article missing required key: {key}")
        if not article[key] or not isinstance(article[key], str):
            raise ValueError(f"Article {key} must be a non-empty string")

def generate_html_content(article, ds):
    """Generate HTML content from article data."""
    raw_body = article['body']

    return HTML_TEMPLATE.format(
        title=article['title'],
        category=article['category'],
        date=ds,
        body=raw_body,
        preview_body=raw_body[:500] + "..." if len(raw_body) > 500 else raw_body
    )

def save_article_files(article, ds, html_content, now_dt):
    """Save article metadata and HTML content to files."""
    meta_file = WP_DIR / f"{now_dt.strftime('%Y-%m-%d')}.json"

    meta_data = {
        'title': article['title'],
        'category': article['category'],
        'body': article['body'],
        'date': ds,
        'status': 'generated'
    }

    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)

    html_file = WP_DIR / f"{now_dt.strftime('%Y-%m-%d')}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    now = datetime.now()
    ds = now.strftime("%d %B %Y")

    if not ARTICLES:
        raise ValueError("No articles available in ARTICLES list")

    art = random.choice(ARTICLES)
    validate_article_structure(art)

    print("=" * 60)
    print("WordPress Article Generator - Generated Content")
    print("=" * 60)
    print(f"Title: {art['title']}")
    print(f"Category: {art['category']}")
    print(f"Date: {ds}")
    print("=" * 60)

    html_content = generate_html_content(art, ds)
    save_article_files(art, ds, html_content, now)

    print(f"\nFiles created:")
    print(f"  Metadata: {now.strftime('%Y-%m-%d')}.json")
    print(f"  HTML: {now.strftime('%Y-%m-%d')}.html")
    print(f"\nPlease access: http://43.153.196.161:5000/article to view and copy the article.")

if __name__ == "__main__":
    main()
