#!/usr/bin/env python3
"""
WordPress Article Generator — Generate + Copy-Paste
====================================================
Generate SEO peternakan articles, save as HTML files
that Adi can copy-paste into WordPress admin.
"""
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / "sembako" / "data"
ARTICLES_DIR = DATA_DIR / "wp_articles"
ARTICLES_DIR.mkdir(exist_ok=True)

DASHBOARD_URL = "http://43.153.196.161:5000"

# ═══════════════════════════════════════
# TOPIC ROTATION (14 hari = 2 minggu)
# ═══════════════════════════════════════
TOPICS = [
    {"tpl": "Harga {komoditas} Hari Ini {date}: {tren}, Peluang Peternakan Makin Cerah",
     "cat": "Harga & Pasar"},
    {"tpl": "Tips Optimasi Pakan {ternak}: Hemat Biaya Hasil Maksimal",
     "cat": "Nutrisi & Pakan"},
    {"tpl": "Prediksi Pasar {komoditas} {month}: Analisis Mendalam untuk Peternak",
     "cat": "Analisis Pasar"},
    {"tpl": "Panduan Lengkap Ternak {ternak} untuk Pemula: Dari Nol hingga Panen",
     "cat": "Panduan Ternak"},
    {"tpl": "Teknologi Modern dalam {ternak}: Inovasi Produktivitas Tinggi",
     "cat": "Teknologi Ternak"},
    {"tpl": "Kesehatan Ternak {ternak}: Pencegahan Penyakit Musim {season}",
     "cat": "Kesehatan Ternak"},
    {"tpl": "Limbah Ternak jadi Pupuk Organik: Bisnis Sampingan Menguntungkan",
     "cat": "Limbah & Pupuk"},
    {"tpl": "Peluang Bisnis {ternak} Modal Kecil Untung Besar di {year}",
     "cat": "Peluang Usaha"},
    {"tpl": "Memahami Kebutuhan Nutrisi {ternak} untuk Hasil Panen Optimal",
     "cat": "Nutrisi & Pakan"},
    {"tpl": "Budidaya {ternak} di Lahan Sempit: Strategi Urban Farming",
     "cat": "Panduan Ternak"},
    {"tpl": "Analisis Harga {komoditas} Bulanan: Tren dan Strategi Penjualan",
     "cat": "Analisis Pasar"},
    {"tpl": "Pakan Fermentasi untuk {ternak}: Cara Membuat dan Keunggulannya",
     "cat": "Nutrisi & Pakan"},
    {"tpl": "Mengenal Jenis Pakan {ternak} yang Baik untuk Pertumbuhan",
     "cat": "Nutrisi & Pakan"},
    {"tpl": "Suhu Ekstrem dan Dampaknya pada {ternak}: Tips Adaptasi",
     "cat": "Kesehatan Ternak"},
]

TERNAK_OPTIONS = ["Ayam Broiler", "Ayam Petelur", "Bebek", "Sapi Potong",
                  "Sapi Perah", "Kambing", "Domba", "Kelinci", "Babi"]
KOMODITAS_OPTIONS = ["Ayam Potong", "Telur Ayem", "Daging Sapi", "Daging Kambing",
                     "Daging Bebek", "Susu Segar", "Ikan Lele", "Daging Kelinci"]


def fetch_peternakan():
    """Fetch peternakan data from dashboard."""
    try:
        req = urllib.request.Request(
            f"{DASHBOARD_URL}/api/peternakan",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {"data": []}


def fetch_sentimen():
    """Fetch sentiment data."""
    try:
        req = urllib.request.Request(
            f"{DASHBOARD_URL}/api/sentimen",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {"data": []}


def get_topic_idx():
    """Get current topic index (rotates daily)."""
    state_file = DATA_DIR / "wp_topic_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        if state.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return state["idx"]
        return (state.get("idx", 0) + 1) % len(TOPICS)
    return 0


def save_topic_state(idx):
    state_file = DATA_DIR / "wp_topic_state.json"
    state_file.write_text(json.dumps({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "idx": idx
    }))


def generate_article(pet_data=None, topic_idx=None):
    """Generate article content from real data."""
    now = datetime.now()
    ds = now.strftime("%d %B %Y")
    month = now.strftime("%B %Y")
    year = now.strftime("%Y")
    season = "kemarau" if now.month in [4,5,6,7,8,9] else "hujan"

    if topic_idx is None:
        topic_idx = get_topic_idx()
    topic = TOPICS[topic_idx % len(TOPICS)]
    ternak = TERNAK_OPTIONS[topic_idx % len(TERNAK_OPTIONS)]
    komoditas = KOMODITAS_OPTIONS[topic_idx % len(KOMODITAS_OPTIONS)]
    tren_options = ["stabil", "naik", "berkembang", "positif", "menjanjikan"]
    tren = tren_options[topic_idx % len(tren_options)]

    title = topic["tpl"].format(
        komoditas=komoditas, ternak=ternak,
        date=ds, month=month, season=season,
        year=year, tren=tren
    )

    # Build prices from real data
    prices_html = ""
    if pet_data and "data" in pet_data and pet_data["data"]:
        items = pet_data["data"][-8:]
        for item in items:
            name = item.get("produk", item.get("komoditas", item.get("nama", "")))
            price = item.get("harga_rata", item.get("harga", ""))
            if isinstance(price, (int, float)) and price > 0:
                prices_html += f"<li><strong>{name}</strong>: Rp{price:,.0f}/kg</li>\n"
    if not prices_html:
        prices_html = "<li>Data harga terkini sedang diperbarui</li>"

    # Sentiment
    sent = "positif"
    try:
        req = urllib.request.Request(
            f"{DASHBOARD_URL}/api/sentimen",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            sd = json.loads(resp.read())
            if sd.get("data"):
                pos = sum(1 for d in sd["data"][:5]
                         if "positif" in str(d.get("sentimen", "")).lower())
                if pos > 0:
                    sent = "positif"
    except Exception:
        pass

    # Article sections
    sections = []

    # Section 1: Harga
    sections.append(f"""<h4>📊 Update Harga Bahan Pakan & Ternak Terkini</h4>
<p>Kondisi pasar peternakan Indonesia periode <strong>{ds}</strong> menunjukkan tren <strong>{sent}</strong>.
Bagi para peternak, memahami pergerakan harga adalah kunci optimasi biaya produksi.</p>

<h4>Harga Bahan Pakan & Komoditas Hari Ini:</h4>
<ul>
{prices_html}
</ul>""")

    # Section 2: Strategi
    sections.append(f"""<h4>🎯 Strategi Hemat untuk Peternak {ternak}</h4>
<ol>
<li><strong>Formulasi Pakan Mandiri</strong> — Racik pakan sendiri lebih hemat 20-30% dari pakan komersial. Gunakan bahan lokal seperti jagung, dedak, bungkil kedelai.</li>
<li><strong>Diversifikasi Bahan Lokal</strong> — Manfaatkan limbah industri: ampas tahu, molases, onggok. Sumber nutrisi terjangkau yang melimpah di Indonesia.</li>
<li><strong>Pencatatan Harga Berkala</strong> — Pantau harga bahan pakan untuk menentukan waktu pembelian terbaik.</li>
<li><strong>Manajemen Kesehatan Ternak</strong> — Pencegahan selalu lebih murah dari pengobatan. Terapkan protokol biosekuriti.</li>
</ol>""")

    # Section 3: Prospek
    sections.append(f"""<h4>📈 Prospek Cerah Peternakan Indonesia</h4>
<p>Konsumsi protein hewani masyarakat Indonesia terus meningkat seiring pertumbuhan ekonomi. Ini menjadi <strong>peluang emas</strong> bagi peternak yang menerapkan manajemen modern dan efisien.</p>
<p>Teknologi informasi memudahkan pemantauan harga pasar real-time. Dengan data yang akurat, keputusan bisnis menjadi lebih tepat sasaran.</p>""")

    # Section 4: Tips
    sections.append(f"""<h4>💡 Tips Praktis Minggu Ini</h4>
<ul>
<li>Periksa kualitas pakan yang tersedia — pastikan tidak basi atau lembap</li>
<li>Catat seluruh biaya produksi untuk analisis profitabilitas bulanan</li>
<li>Evaluasi konversi pakan ternak — targetkan FCR yang optimal</li>
<li>Manfaatkan cuaca baik untuk menjemur pakan atau membersihkan kandang</li>
</ul>""")

    # Section 5: CTA
    sections.append(f"""<p><strong>Semangat peternak Indonesia! Terus tingkatkan produktivitas dengan data dan strategi yang tepat! 🐔🐄🐑</strong></p>

<hr>
<p><em>Diperbarui {ds}. Data bersumber dari dashboard monitoring komoditas nasional.
Pantau terus perkembangan harga di <a href="https://catataninsani.wordpress.com/" target="_blank" rel="noopener">Catatan Insani</a>.</em></p>""")

    content = "\n\n".join(sections)

    # Save files
    save_topic_state((topic_idx + 1) % len(TOPICS))

    # Save HTML
    safe_name = now.strftime("%Y-%m-%d")
    html_path = ARTICLES_DIR / f"{safe_name}.html"
    html_path.write_text(content)

    # Save title + content JSON
    meta_path = ARTICLES_DIR / f"{safe_name}.json"
    meta_path.write_text(json.dumps({
        "title": title,
        "content": content,
        "category": topic["cat"],
        "date": ds,
        "topic_idx": topic_idx,
    }, ensure_ascii=False, indent=2))

    return title, content, topic["cat"], ds


def main():
    print("=" * 60)
    print("🐾 WordPress Article Generator — Catatan Insani")
    print("=" * 60)

    # Fetch data
    print("\n📡 Fetching dashboard data...")
    pet = fetch_peternakan()
    has_data = bool(pet.get("data"))
    print(f"   Peternakan: {'✅' if has_data else '❌'}")

    # Generate
    print("\n✍️  Generating article...")
    title, content, category, ds = generate_article(pet)

    safe_name = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'=' * 60}")
    print(f"✅ Article generated!")
    print(f"   Title: {title}")
    print(f"   Category: {category}")
    print(f"   Date: {ds}")
    print(f"\n📁 Files saved:")
    print(f"   HTML: data/wp_articles/{safe_name}.html")
    print(f"   Meta: data/wp_articles/{safe_name}.json")
    print(f"\n📋 How to publish:")
    print(f"   1. Buka http://43.153.196.161:5000/article")
    print(f"   2. Copy title & content")
    print(f"   3. Paste ke WordPress admin")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
