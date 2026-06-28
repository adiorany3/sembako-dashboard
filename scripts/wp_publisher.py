#!/usr/bin/env python3
"""
WordPress Auto-Publisher untuk Catatan Insani
=============================================
Generate artikel peternakan dari data real-time dashboard + berita terkini,
lalu publish via WordPress.com REST API.
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import base64
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
WP_SITE = "catataninsani.wordpress.com"
WP_USER = "chickaholic"
WP_APP_PASSWORD = "mnllwqyxwxp7mly6"
WP_API = f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}"
DASHBOARD_URL = "http://43.153.196.161:5000"
DATA_DIR = Path.home() / "sembako" / "data"
SESH_DIR = Path.home() / "sembako" / "data" / "wp_published.json"

# ═══════════════════════════════════════
# TOPIC TEMPLATES
# ═══════════════════════════════════════
TOPICS = [
    {
        "title_tpl": "Harga {komoditas} Hari Ini {date}: {tren}, Peluang Usaha Peternakan Makin Cerah",
        "tags": ["harga ternak", "peluang usaha", "peternakan"],
        "category": "Harga & Pasar",
    },
    {
        "title_tpl": "Tips Optimasi Pakan {ternak}: Hemat Biaya, Hasil Maksimal",
        "tags": ["pakan ternak", "optimasi", "nutrisi"],
        "category": "Nutrisi & Pakan",
    },
    {
        "title_tpl": "Prediksi Pasar {komoditas} {month}: Analisis Mendalam untuk Peternak",
        "tags": ["prediksi pasar", "analisis", "strategi"],
        "category": "Analisis Pasar",
    },
    {
        "title_tpl": "Panduan Lengkap {ternak} untuk Pemula: Dari Nol hingga Panen",
        "tags": ["panduan pemula", "ternak", "tutorial"],
        "category": "Panduan Ternak",
    },
    {
        "title_tpl": "Teknologi Modern dalam {ternak}: Inovasi untuk Produktivitas Tinggi",
        "tags": ["teknologi", "inovasi", "modern"],
        "category": "Teknologi Ternak",
    },
    {
        "title_tpl": "Kesehatan Ternak {ternak}: Pencegahan Penyakit Musim {season}",
        "tags": ["kesehatan ternak", "biosekuriti", "penyakit"],
        "category": "Kesehatan Ternak",
    },
    {
        "title_tpl": "Potensi Limbah Ternak sebagai Pupuk Organik: Bisnis Sampingan Menguntungkan",
        "tags": ["limbah ternak", "pupuk organik", "bisnis"],
        "category": "Limbah & Pupuk",
    },
]


# ═══════════════════════════════════════
# WORDPRESS API CLIENT
# ═══════════════════════════════════════
def wp_request(endpoint, method="GET", data=None):
    """Make authenticated request to WordPress.com REST API."""
    url = f"{WP_API}/{endpoint}"
    auth_str = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    if data:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ API Error {e.code}: {body[:300]}")
        return None


def wp_create_post(title, content, tags=None, categories=None, status="draft"):
    """Create a WordPress post via REST API."""
    post_data = {
        "title": title,
        "content": content,
        "status": status,
        "format": "standard",
    }
    # Tags & categories need IDs — resolve slugs first
    if tags:
        tag_ids = resolve_tags(tags)
        if tag_ids:
            post_data["tags"] = tag_ids
    if categories:
        cat_ids = resolve_categories(categories)
        if cat_ids:
            post_data["categories"] = cat_ids

    print(f"📝 Creating post: {title}")
    print(f"   Status: {status} | Tags: {len(tags or [])} | Cats: {len(categories or [])}")
    result = wp_request("posts", method="POST", data=post_data)
    if result and "ID" in result:
        post_id = result["ID"]
        link = result.get("URL", result.get("link", f"https://{WP_SITE}/?p={post_id}"))
        print(f"✅ Published! ID={post_id}")
        print(f"   Link: {link}")
        return result
    else:
        print(f"❌ Failed to create post")
        return None


def resolve_tags(tag_names):
    """Get or create tag IDs from names."""
    ids = []
    for name in tag_names:
        slug = name.lower().replace(" ", "-").replace("&", "dan")
        # Try to find existing
        existing = wp_request(f"tags?search={urllib.parse.quote(name)}&_fields=ID,slug")
        if existing and len(existing) > 0:
            ids.append(existing[0]["ID"])
        else:
            # Create new
            result = wp_request("tags", method="POST", data={"name": name, "slug": slug})
            if result and "ID" in result:
                ids.append(result["ID"])
    return ids


def resolve_categories(cat_names):
    """Get or create category IDs from names."""
    ids = []
    for name in cat_names:
        slug = name.lower().replace(" ", "-").replace("&", "dan")
        existing = wp_request(f"categories?search={urllib.parse.quote(name)}&_fields=ID,slug")
        if existing and len(existing) > 0:
            ids.append(existing[0]["ID"])
        else:
            result = wp_request("categories", method="POST", data={"name": name, "slug": slug})
            if result and "ID" in result:
                ids.append(result["ID"])
    return ids


# ═══════════════════════════════════════
# DATA FETCHER
# ═══════════════════════════════════════
def fetch_dashboard_data():
    """Fetch live data from dashboard API."""
    data = {}
    endpoints = {
        "sembako": "/api/sembako",
        "crypto": "/api/crypto",
        "emas": "/api/emas",
        "pertanian": "/api/pertanian",
        "peternakan": "/api/peternakan",
        "kurs": "/api/kurs",
        "sentimen": "/api/sentimen",
    }
    for key, ep in endpoints.items():
        try:
            req = urllib.request.Request(f"{DASHBOARD_URL}{ep}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data[key] = json.loads(resp.read().decode("utf-8"))
        except Exception:
            data[key] = None
    return data


def fetch_live_prices():
    """Get current prices from various sources."""
    prices = {}
    # Try Jina for peternakan prices
    urls = {
        "kambing": "https://r.jina.ai/https://www.hargapeternakan.com/harga-kambing",
        "ayam": "https://r.jina.ai/https://www.hargapeternakan.com/harga-ayam",
        "sapi": "https://r.jina.ai/https://www.hargapeternakan.com/harga-sapi",
        "bebek": "https://r.jina.ai/https://www.hargapeternakan.com/harga-bebek",
    }
    for key, url in urls.items():
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/plain",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="replace")[:5000]
                prices[key] = text
        except Exception:
            prices[key] = None
    return prices


def read_published_log():
    """Read published posts log."""
    if SESH_DIR.exists():
        return json.loads(SESH_DIR.read_text())
    return {"published": [], "topic_idx": 0}


def save_published_log(log):
    """Save published posts log."""
    SESH_DIR.write_text(json.dumps(log, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════
# ARTICLE GENERATOR
# ═══════════════════════════════════════
def generate_article(data, topic_idx, price_data):
    """Generate SEO-optimized article about peternakan."""
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    month = now.strftime("%B %Y")
    season = "kemarau" if now.month in [4, 5, 6, 7, 8, 9] else "hujan"

    # Pick topic
    topic = TOPICS[topic_idx % len(TOPICS)]

    # Prepare context
    ternak_options = ["Ayam Broiler", "Ayam Petelur", "Bebek", "Sapi Potong", "Sapi Perah", "Kambing", "Domba", "Babi"]
    komoditas_options = ["Ayam Potong", "Telur Ayam", "Daging Sapi", "Daging Kambing", "Daging Bebek", "Susu Segar", "Daging Babi"]
    ternak = ternak_options[topic_idx % len(ternak_options)]
    komoditas = komoditas_options[topic_idx % len(komoditas_options)]

    # Get real data context
    pet_data = data.get("peternakan", {})
    sent_data = data.get("sentimen", {})
    pakan_data = data.get("pertanian", {})

    # Extract prices from dashboard
    pet_prices = []
    if pet_data and "data" in pet_data:
        for item in pet_data["data"][-5:]:
            name = item.get("komoditas", item.get("nama", ""))
            price = item.get("harga", item.get("harga_rata", ""))
            pet_prices.append(f"- {name}: Rp{price:,}" if isinstance(price, (int, float)) else f"- {name}: Rp{price}")

    pet_prices_text = "\n".join(pet_prices[:10]) if pet_prices else "- Data harga sedang diperbarui"

    # Sentiment context
    sent = "positif" if sent_data and sent_data.get("data") and len(sent_data["data"]) > 0 and any(
        "positif" in str(d.get("sentimen", "")).lower() for d in sent_data["data"][:3]
    ) else "netral"

    # Title
    tren_options = ["stabil","naik","berkembang","positif","menjanjikan"]
    tren = tren_options[topic_idx % len(tren_options)]
    title = topic["title_tpl"].format(
        komoditas=komoditas, ternak=ternak,
        date=date_str, month=month, season=season, tren=tren,
    )

    # Generate SEO content (HTML with H4 headings)
    content = f"""<h4>📊 Update Harga Ternak Terkini {date_str}</h4>
<p>Kondisi pasar peternakan Indonesia menunjukkan tren yang <strong>menjanjikan</strong> untuk para peternak. Dengan data terkini dari dashboard komoditas nasional, berikut perkembangan harga yang perlu diperhatikan:</p>

<h4>💹 Harga Bahan Pakan & Nutrisi</h4>
{pet_prices_text}
<p>Ketersediaan bahan pakan lokal yang berlimpah menjadi <strong>keunggulan kompetitif</strong> bagi peternak Indonesia. Dengan strategi formulasi pakan yang tepat, biaya produksi bisa dioptimalkan hingga <strong>20-40%</strong> lebih hemat dibanding pakan jadi komersial.</p>

<h4>📈 Analisis Pasar & Peluang</h4>
<p>Sentimen pasar terhadap komoditas peternakan saat ini cenderung <strong>{sent}</strong>. Beberapa faktor pendukung:</p>
<ul>
<li><strong>Konsumsi protein hewani</strong> terus meningkat seiring pertumbuhan populasi dan daya beli masyarakat</li>
<li><strong>Pemerintah</strong> aktif mendukung swasembada pangan melalui program-program subsidi dan pelatihan</li>
<li><strong>Teknologi peternakan</strong> modern membuka peluang efisiensi yang signifikan</li>
<li><strong>Pasar ekspor</strong> ke negara tetangga menunjukkan potensi yang menggembirakan</li>
</ul>

<h4>🎯 Strategi Optimasi untuk Peternak</h4>
<p>Untuk memaksimalkan keuntungan di kondisi pasar saat ini, berikut strategi yang bisa diterapkan:</p>
<ol>
<li><strong>Formulasi Pakan Mandiri</strong> — Gunakan bahan pakan lokal seperti jagung, bungkil kedelai, dan dedak. Dengan perbandingan nutrisi yang tepat, pakan mandiri bisa menghemat biaya hingga 30%</li>
<li><strong>Manajemen Kesehatan Ternak</strong> — Pencegahan selalu lebih baik dan lebih murah dari pengobatan. Terapkan protokol biosekuriti yang ketat</li>
<li><strong>Diversifikasi Produk</strong> — Jangan hanya menjual daging/telur mentah. Pikirkan produk olahan bernilai tambah tinggi</li>
<li><strong>Pencatatan Keuangan</strong> — Pantau arus kas dan margin keuntungan secara berkala untuk pengambilan keputusan yang lebih baik</li>
</ol>

<h4>🌱 Prospek ke Depan</h4>
<p>Industri peternakan Indonesia memiliki prospek yang <strong>sangat cerah</strong>. Dengan dukungan teknologi, akses informasi harga pasar yang transparan, serta permintaan yang terus meningkat, peternak yang adaptif dan inovatif akan mendapatkan keuntungan berlipat ganda.</p>
<p>Terus pantau perkembangan harga dan tren pasar melalui dashboard monitoring untuk pengambilan keputusan yang tepat waktu. <strong>Semangat peternak Indonesia! 🐔🐄🐑</strong></p>
"""

    # Add SEO-friendly footer
    content += f"""
<hr>
<p><em>Artikel ini diperbarui pada {date_str}. Data harga bersumber dari dashboard monitoring komoditas nasional. Untuk informasi lebih lanjut, kunjungi <a href="https://catataninsani.wordpress.com/">Catatan Insani</a>.</em></p>

<p><strong>Keyword SEO:</strong> peternakan Indonesia, harga ternak hari ini, {ternak.lower()}, pakan ternak, optimasi peternakan, peluang usaha ternak 2026</p>
"""

    return title, content, topic["tags"], topic["category"]


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    print("=" * 60)
    print("🐾 WordPress Auto-Publisher — Catatan Insani")
    print("=" * 60)

    # Load state
    log = read_published_log()
    topic_idx = log.get("topic_idx", 0)

    # Fetch data
    print("\n📡 Fetching dashboard data...")
    data = fetch_dashboard_data()
    pet = data.get("peternakan")
    print(f"   Peternakan: {'✅' if pet else '❌'}")

    # Generate article
    print("\n✍️  Generating article...")
    title, content, tags, category = generate_article(data, topic_idx, None)

    # Determine status from args
    status = sys.argv[1] if len(sys.argv) > 1 else "draft"

    # Publish
    print(f"\n🚀 Publishing ({status})...")
    result = wp_create_post(title, content, tags=tags, categories=[category], status=status)

    if result:
        post_id = result.get("ID")
        link = result.get("URL", result.get("link", f"https://{WP_SITE}/?p={post_id}"))
        # Update log
        log["published"].append({
            "id": post_id,
            "title": title,
            "date": datetime.now().isoformat(),
            "link": link,
            "status": status,
            "tags": tags,
        })
        log["topic_idx"] = topic_idx + 1
        save_published_log(log)

        print(f"\n{'=' * 60}")
        print(f"✅ PUBLISHED SUCCESSFULLY!")
        print(f"   Title: {title}")
        print(f"   Link: {link}")
        print(f"   Status: {status}")
        print(f"{'=' * 60}")
        return link
    else:
        print("\n❌ PUBLISH FAILED")
        return None


if __name__ == "__main__":
    main()
