#!/usr/bin/env python3
"""
Precompute AI Market Analysis (Groq) — V3
All data sources → prompt → Groq → JSON.
API reads JSON = zero calls at request time.
"""
import os, json, sys, traceback, re
from datetime import datetime
import openpyxl
from pathlib import Path

DATA_DIR = Path.home() / "sembako" / "data"

# Groq key
sys.path.insert(0, str(Path.home() / "sembako" / "core"))
try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def read_sheet(filename, sheet=None):
    """Read xlsx → list of dicts. Strips whitespace from keys."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if len(rows) < 2:
            return []
        # Clean headers: strip, replace \n with space
        headers = []
        for i, h in enumerate(rows[0]):
            if h is None:
                headers.append(f"col{i}")
            else:
                headers.append(re.sub(r'\s+', ' ', str(h).strip()))
        return [dict(zip(headers, row)) for row in rows[1:] if any(v is not None for v in row)]
    except Exception as e:
        print(f"  ⚠️ Error reading {filename}: {e}")
        return []


def last(sheet, n=0):
    """Get row n from end."""
    data = read_sheet(sheet[0], sheet[1] if len(sheet) > 1 else None)
    return data[-(n+1)] if len(data) > n else {}


def F(val, prefix="", suffix=""):
    """Safe float format."""
    if val is None or val == "":
        return None
    try:
        return f"{prefix}{float(val):,.0f}{suffix}"
    except (ValueError, TypeError):
        return None


def load_all_data():
    """Build prompt from ALL 12 data sources with CORRECT column names."""
    now = datetime.now().strftime("%d %B %Y, %H:%M WIB")
    sections = []

    # ── 1. SEMBAKO ──
    r = last(("harga_sembako.xlsx", "Harga"))
    p = last(("harga_sembako.xlsx", "Harga"), 1)
    if r:
        lines = []
        items = [
            ("Beras Premium", "Beras Premium"), ("Beras Medium", "Beras Medium"),
            ("Minyak Goreng", "Minyak Goreng"), ("Gula Pasir", "Gula Pasir"),
            ("Garam", "Garam"), ("Telur Ras", "Telur Ras"), ("Telur Kampung", "Telur Kampung"),
            ("Ayam Ras", "Ayam Ras"), ("Daging Sapi", "Daging Sapi"),
            ("Cabai Merah", "Cabai Merah"), ("Cabai Rawit", "Cabai Rawit"),
            ("Bawang Merah", "Bawang Merah"), ("Bawang Putih", "Bawang Putih"),
            ("Ikan Tongkol", "Ikan Tongkol"), ("Ikan Teri", "Ikan Teri"),
        ]
        for key, name in items:
            v = F(r.get(key), prefix="Rp")
            if v and p and p.get(key):
                pv = float(p[key])
                cv = float(r[key])
                if pv > 0:
                    chg = ((cv - pv) / pv) * 100
                    arrow = "↑" if chg > 1 else "↓" if chg < -1 else "→"
                    lines.append(f"- {name}: {v}/kg ({arrow}{chg:+.1f}%)")
                    continue
            if v:
                lines.append(f"- {name}: {v}/kg")
        sections.append("## SEMBAKO\n" + "\n".join(lines))

    # ── 2. CRYPTO ──
    r = last(("crypto_monitor.xlsx",))
    if r:
        lines = []
        for key, name in [("BTC (USD)", "Bitcoin"), ("ETH (USD)", "Ethereum"),
                          ("SOL (USD)", "Solana"), ("ADA (USD)", "Cardano"),
                          ("DOGE (USD)", "Dogecoin"), ("XRP (USD)", "XRP")]:
            v = r.get(key)
            if v: lines.append(f"- {name}: ${float(v):,.2f}")
        mcap = r.get("Total Market Cap (T)")
        if mcap: lines.append(f"- Market Cap: ${mcap}T")
        sent = r.get("Sentimen")
        if sent: lines.append(f"- Sentimen: {sent}")
        sections.append("## CRYPTO\n" + "\n".join(lines))

    # ── 3. EMAS ──
    emas_path = DATA_DIR / "emas_harian.xlsx"
    if emas_path.exists():
        for sn in ["Harian", "Harga"]:
            r = last(("emas_harian.xlsx", sn))
            if r and any(r.get(k) for k in ["Antam Beli", "Antam_Beli"]):
                lines = []
                for key, label in [("Antam Beli", "Antam Beli"), ("Antam_Beli", "Antam Beli"),
                                   ("Antam Buyback", "Buyback"), ("Antam_Buyback", "Buyback"),
                                   ("Pegadaian", "Pegadaian"), ("Galeri24", "Galeri24"), ("UBS", "UBS")]:
                    v = F(r.get(key), prefix="Rp")
                    if v: lines.append(f"- {label}: {v}/gram")
                sections.append("## EMAS\n" + "\n".join(lines))
                break
    else:
        # JSON fallback
        jp = DATA_DIR / "emas_history.json"
        if jp.exists():
            try:
                d = json.loads(jp.read_text())
                if d:
                    last_emas = d[-1] if isinstance(d, list) else d
                    lines = [f"- Antam Beli: Rp{int(last_emas.get('antam_beli', 0)):,}/gram"]
                    sections.append("## EMAS\n" + "\n".join(lines))
            except: pass

    # ── 4. PERTANIAN ──
    r = last(("harga_pertanian_ternak.xlsx", "Harga Komoditas"))
    if r:
        lines = []
        for key, name in [
            ("Jagung Kering Pipil (Rp/kg)", "Jagung Kering"),
            ("Jagung Pakan Ternak (Rp/kg)", "Jagung Pakan"),
            ("Kedelai Impor (Rp/kg)", "Kedelai Impor"),
            ("Kedelai Lokal (Rp/kg)", "Kedelai Lokal"),
            ("Pakan Broiler BR1 (Rp/kg)", "Pakan Broiler"),
            ("Pakan Layer (Rp/kg)", "Pakan Layer"),
        ]:
            v = F(r.get(key), prefix="Rp")
            if v: lines.append(f"- {name}: {v}/kg")
        sections.append("## PERTANIAN\n" + "\n".join(lines))

    # ── 5. PETERNAKAN ──
    rows = read_sheet("harga_peternakan_lengkap.xlsx")
    if rows:
        # Aggregate: take latest price per unique product
        products = {}
        for r in rows:
            name = r.get("Produk") or r.get("produk")
            price = r.get("Harga (Rp)") or r.get("Harga")
            cat = r.get("Kategori") or ""
            satuan = r.get("Satuan") or "kg"
            if name and price:
                try:
                    products[str(name).strip()] = {'harga': float(price), 'satuan': satuan, 'kategori': cat}
                except (ValueError, TypeError): pass
        if products:
            lines = []
            # Group by kategori
            for kategori in ["HILIR", "HULU", "INDUSTRI"]:
                items = [(n, d) for n, d in products.items() if d['kategori'] == kategori]
                if items:
                    lines.append(f"**{kategori}:**")
                    for name, info in sorted(items, key=lambda x: x[1]['harga'], reverse=True)[:8]:
                        lines.append(f"- {name}: Rp{info['harga']:,.0f}/{info['satuan']}")
            sections.append("## PETERNAKAN\n" + "\n".join(lines))

    # ── 6. SAHAM ──
    r = last(("harga_saham_ihsg.xlsx", "IHSG"))
    if r:
        lines = []
        # Try various possible column names
        for key in ["IHSG", "Close", "IHSG_Close"]:
            v = r.get(key)
            if v: lines.append(f"- IHSG: {v}"); break
        for key in ["Chg_%", "Change_%", "Perubahan"]:
            v = r.get(key)
            if v: lines.append(f"- Change: {v}%"); break
        sections.append("## SAHAM / IHSG\n" + "\n".join(lines))

    # ── 7. KURS ──
    r = last(("kurs_valuta.xlsx", "Harian"))
    if r:
        lines = []
        for key, name in [("USD_IDR", "USD→IDR"), ("EUR_IDR", "EUR→IDR"),
                          ("SGD_IDR", "SGD→IDR"), ("MYR_IDR", "MYR→IDR")]:
            v = F(r.get(key), prefix="Rp")
            if v: lines.append(f"- {name}: {v}")
        sections.append("## KURS\n" + "\n".join(lines))

    # ── 8. MINYAK ──
    r = last(("harga_minyak.xlsx", "Harian"))
    if r:
        lines = []
        for key, name in [("Brent_USD", "Brent"), ("WTI_USD", "WTI")]:
            v = r.get(key)
            if v: lines.append(f"- {name}: ${float(v):,.2f}/barel")
        sections.append("## MINYAK MENTAH\n" + "\n".join(lines))

    # ── 9. BI RATE ──
    r = last(("bi_rate_inflasi.xlsx", "Harian"))
    if r:
        lines = []
        for key, label in [("BI_Rate", "BI Rate"), ("Inflasi_YoY", "Inflasi YoY"),
                           ("Inflasi_MoM", "Inflasi MoM"), ("IHK", "IHK")]:
            v = r.get(key)
            if v is not None:
                lines.append(f"- {label}: {v}%")
        sections.append("## BI RATE & INFLASI\n" + "\n".join(lines))

    # ── 10. CPO ──
    r = last(("harga_cpo.xlsx", "Harian"))
    if r:
        lines = []
        myr = r.get("Harga_MYR")
        idr = r.get("Harga_IDR")
        if myr: lines.append(f"- CPO: MYR {myr}/ton")
        if idr: lines.append(f"- Est: Rp{float(idr):,.0f}/kg")
        sections.append("## CPO (KELAPA SAWIT)\n" + "\n".join(lines))

    # ── 11. SENTIMEN ──
    rows = read_sheet("sentimen_berita.xlsx", "Summary")
    if rows:
        r = rows[-1]
        lines = []
        for key, label in [("Positif", "Positif"), ("Netral", "Netral"),
                           ("Negatif", "Negatif")]:
            v = r.get(key)
            if v is not None: lines.append(f"- {label}: {v}")
        sections.append("## SENTIMEN BERITA\n" + "\n".join(lines))
    else:
        # Try Detail sheet
        rows = read_sheet("sentimen_berita.xlsx", "Detail")
        if rows:
            pos = sum(1 for r in rows if r.get("Sentimen") == "positif")
            neg = sum(1 for r in rows if r.get("Sentimen") == "negatif")
            neu = sum(1 for r in rows if r.get("Sentimen") == "netral")
            total = len(rows)
            if total:
                sections.append(f"## SENTIMEN BERITA\n- Positif: {pos} ({pos*100//total}%)\n- Netral: {neu} ({neu*100//total}%)\n- Negatif: {neg} ({neg*100//total}%)")

    # ── 12. PAKAN ──
    r = last(("harga_pakan_ternak.xlsx", "Harga Pakan"))
    if r:
        lines = []
        items = []
        for k, v in r.items():
            if v and k != "Tanggal":
                try:
                    fv = float(v)
                    if fv > 0:
                        name_clean = re.sub(r'\s+', ' ', k).strip()
                        items.append((name_clean, fv))
                except: pass
        items.sort(key=lambda x: x[1], reverse=True)
        lines.append("**Top 5 Termahal:**")
        for name, price in items[:5]:
            lines.append(f"- {name}: Rp{price:,.0f}/kg")
        lines.append("**Top 5 Termurah:**")
        for name, price in items[-5:]:
            lines.append(f"- {name}: Rp{price:,.0f}/kg")
        sections.append("## PAKAN TERNAK\n" + "\n".join(lines))

    return f"# DATA MARKET INDONESIA — {now}\n\n" + "\n\n".join(sections)


SYSTEM_PROMPT = """Kamu adalah analis keuangan komoditas Indonesia berpengalaman.
Analisis data market real-time dari 12 sumber berikut.

FORMAT OUTPUT (Bahasa Indonesia, markdown):

## 📊 Market Overview
2-3 kalimat ringkasan kondisi market hari ini.

## 📈 Tren Naik ↑
Komoditas/aset yang naik + alasannya singkat.

## 📉 Tren Turun ↓
Komoditas/aset yang turun + alasannya singkat.

## 🔮 Analisis Sektoral
- **IHSG & Saham**
- **Crypto**
- **Emas**
- **Sembako & Harga Pokok**
- **Pertanian & Peternakan**
- **Energi (Minyak, CPO)**
- **Kurs & Moneter (BI Rate)**

## ⚠️ Risiko & Warning
Maks 3 poin.

## 💡 Rekomendasi
- Untuk petani/ternak
- Untuk konsumen
- Untuk investor

## 🎯 Prediksi 3 Hari ke Depan

RULES:
- Hanya gunakan data yang ada, JANGAN mengarang angka.
- Jika data tidak ada, tulis "Data belum tersedia".
- 500-800 kata total.
- Gunakan emoji."""

def generate_rule_analysis(data_text: str) -> str:
    """Rule-based analysis fallback — zero API calls, runs anywhere."""
    from datetime import datetime
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")

    lines = []

    # ── Market Overview ──
    lines.append("## 📊 Market Overview")
    lines.append(f"Analisis otomatis berdasarkan data real-time {date_str}.")
    lines.append("")

    # ── Parse numeric values from data ──
    import re
    def find_val(text, pattern):
        m = re.search(pattern, text)
        return m.group(1).replace(",","") if m else None

    btc = find_val(data_text, r"Bitcoin:\s*\$([\d,.]+)")
    ihsg = find_val(data_text, r"IHSG:\s*([\d,.]+)")
    usd = find_val(data_text, r"USD→IDR:\s*Rp([\d,.]+)")
    bi_rate = find_val(data_text, r"BI Rate:\s*([\d,.]+)")
    inflasi = find_val(data_text, r"Inflasi YoY:\s*([\d,.]+)")
    brent = find_val(data_text, r"Brent:\s*\$([\d,.]+)")
    cpo_myr = find_val(data_text, r"CPO:\s*MYR\s*([\d,.]+)")

    # ── Tren Naik ↑ ──
    lines.append("## 📈 Tren Naik ↑")
    naik = []
    for m in re.finditer(r"- (.+?): Rp([\d,]+)/kg \(([↑+])([+\-\d.]+)%\)", data_text):
        name, price, arrow, chg = m.groups()
        if arrow == "↑" and float(chg) > 1:
            naik.append((name, price, float(chg)))
    for m in re.finditer(r"- (.+?): Rp([\d,]+)/kg \(([↑+])([+\-\d.]+)%\)", data_text):
        name, price, arrow, chg = m.groups()
        if arrow == "↑" and float(chg) > 0.5:
            naik.append((name, price, float(chg)))
    # Deduplicate
    seen = set()
    unique_naik = []
    for n, p, c in naik:
        if n not in seen:
            seen.add(n)
            unique_naik.append((n,p,c))
    if unique_naik:
        for name, price, chg in sorted(unique_naik, key=lambda x: x[2], reverse=True)[:8]:
            lines.append(f"- {name}: Rp{price}/kg ↑{chg:.1f}%")
    else:
        lines.append("- Tidak ada tren naik signifikan")
    lines.append("")

    # ── Tren Turun ↓ ──
    lines.append("## 📉 Tren Turun ↓")
    turun = []
    for m in re.finditer(r"- (.+?): Rp([\d,]+)/kg \(([↓\-])([+\-\d.]+)%\)", data_text):
        name, price, arrow, chg = m.groups()
        turun.append((name, price, float(chg)))
    if turun:
        for name, price, chg in sorted(turun, key=lambda x: x[2])[:5]:
            lines.append(f"- {name}: Rp{price}/kg ↓{abs(chg):.1f}%")
    else:
        lines.append("- Tidak ada tren turun signifikan")
    lines.append("")

    # ── Analisis Sektoral ──
    lines.append("## 🔮 Analisis Sektoral")
    lines.append("")

    # IHSG
    if ihsg:
        val = float(ihsg.replace(",",""))
        status = "stabil" if 5500 < val < 6000 else "lemah" if val < 5500 else "cukup kuat"
        lines.append(f"- **IHSG**: {ihsg} — pasar {status}")
    if btc:
        val = float(btc.replace(",",""))
        if val > 65000: trend = "menguat"
        elif val > 55000: trend = "stabil-positif"
        elif val > 45000: trend = "konsolidasi"
        else: trend = "melemah"
        lines.append(f"- **BTC**: ${btc} — {trend}")
    if usd:
        lines.append(f"- **Kurs USD**: Rp{usd} {'stabil' if 15800 < float(usd.replace(',','')) < 16200 else 'perlu dipantau'}")
    lines.append("")

    # ── Kurs & Moneter ──
    lines.append("### Kurs & Moneter")
    if bi_rate:
        lines.append(f"- **BI Rate**: {bi_rate}% {'ekspansif' if float(bi_rate) < 5.5 else 'ketat' if float(bi_rate) > 6.5 else 'netral'}")
    if inflasi:
        val = float(inflasi)
        status = "terkendali" if val < 3 else "tinggi" if val > 5 else "wajar"
        lines.append(f"- **Inflasi YoY**: {inflasi}% — {status}")
    lines.append("")

    # ── Energi ──
    lines.append("### Energi & CPO")
    if brent:
        val = float(brent.replace(",",""))
        lines.append(f"- **Minyak Brent**: ${brent}/barel {'naik' if val > 75 else 'stabil' if val > 65 else 'turun'}")
    if cpo_myr:
        lines.append(f"- **CPO**: MYR {cpo_myr}/ton")
    lines.append("")

    # ── Pakan ──
    pakan_lines = [l for l in data_text.split('\n') if 'Rp/kg)' in l and 'Rp' in l]
    if pakan_lines:
        lines.append("### Pakan Ternak")
        lines.append(f"- {len(pakan_lines)} bahan pakan terpantau")
        lines.append("")

    # ── Risiko ──
    lines.append("## ⚠️ Risiko & Warning")
    risks = []
    if ihsg and float(ihsg.replace(",","")) < 5800:
        risks.append("⚠️ IHSG di bawah 5800 — tekanan jual")
    if btc and float(btc.replace(",","")) < 55000:
        risks.append("⚠️ BTC di bawah $55k — risiko koreksi kripto")
    if bi_rate and float(bi_rate) > 6:
        risks.append("⚠️ BI Rate tinggi — biaya pinjaman mahal")
    if inflasi and float(inflasi) > 4:
        risks.append("⚠️ Inflasi tinggi — daya beli menurun")
    for r in risks[:3]:
        lines.append(f"- {r}")
    if not risks:
        lines.append("- Tidak ada risiko signifikan terdeteksi")
    lines.append("")

    # ── Rekomendasi ──
    lines.append("## 💡 Rekomendasi")
    lines.append("- **Petani/ternak**: Pantau harga pakan — stok saat harga turun")
    lines.append("- **Konsumen**: Harga sembako relatif stabil, beli sesuai kebutuhan")
    lines.append("- **Investor**: Diversifikasi portofolio, jangan all-in satu aset")
    lines.append("")

    # ── Prediksi ──
    lines.append("## 🎯 Prediksi 3 Hari ke Depan")
    lines.append("- Market cenderung sideways minggu ini")
    lines.append("- Pantau rilis data inflasi & kebijakan BI")
    lines.append("- Crypto menunggu sentimen global (Fed, ETF flow)")
    lines.append("")
    lines.append("---")
    lines.append(f"_Analisis otomatis. {date_str} — Data dari 12 sumber_")

    return "\n".join(lines)


def call_groq(prompt: str) -> str:
    """Call Groq API — tries main endpoint first."""
    import urllib.request
    if not GROQ_API_KEY:
        return ""

    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"]


def main():
    ts = lambda: f"[{datetime.now():%H:%M:%S}]"
    print(f"{ts()} 🧠 AI Market Analysis V3 — Precompute")
    print(f"{ts()} {'='*50}")

    data = load_all_data()
    n_sections = data.count("## ")
    print(f"{ts()} 📂 {n_sections} sections, {len(data)} chars loaded")

    print(f"{ts()} 🤖 Calling Groq (llama-3.1-8b-instant)...")
    analysis = ""
    source = "groq_llama3.1_v3"
    try:
        analysis = call_groq(data)
        if analysis and len(analysis) > 100:
            print(f"{ts()} ✅ Groq response: {len(analysis)} chars")
        else:
            raise Exception("Empty response from Groq")
    except Exception as e:
        print(f"{ts()} ⚠️ Groq failed: {e}")
        print(f"{ts()} 🔄 Generating rule-based analysis...")
        analysis = generate_rule_analysis(data)
        source = "rule_based_fallback"
        print(f"{ts()} ✅ Rule-based: {len(analysis)} chars")

    output = {
        "analysis": analysis,
        "generated_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "next_update": datetime.now().timestamp() + 28800,
        "source": source,
    }
    out_path = DATA_DIR / "daily_analysis.json"
    with open(str(out_path), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"{ts()} 💾 Saved to {out_path}")
    print(f"{ts()} Preview: {analysis[:150]}...")


if __name__ == "__main__":
    main()
