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
    """Deep rule-based analysis — reads Excel directly for cross-sector insights."""
    import re, os, json
    from datetime import datetime
    from pathlib import Path
    import openpyxl

    DATA_DIR = Path.home() / "sembako" / "data"
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    lines = []

    def _read(fn, sheet=None):
        p = DATA_DIR / fn
        if not p.exists(): return []
        try:
            wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
            ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.active
            rows = list(ws.iter_rows(values_only=True))
            wb.close()
            if len(rows) < 2: return []
            hdrs = [re.sub(r'\s+', ' ', str(h).strip()) if h else f'c{i}' for i,h in enumerate(rows[0])]
            return [dict(zip(hdrs, row)) for row in rows[1:]]
        except: return []

    def _last(fn, sheet=None, n=0):
        d = _read(fn, sheet)
        return d[-(n+1)] if len(d) > n else {}

    def _prev(fn, sheet=None):
        return _last(fn, sheet, 1)

    # ════════════════════════════════════════════
    # 1. COLLECT ALL DATA
    # ════════════════════════════════════════════

    # Sembako
    sembako_items = {
        'Beras Premium': 'Pangan Pokok', 'Beras Medium': 'Pangan Pokok',
        'Minyak Goreng': 'Minyak', 'Gula Pasir': 'Pangan Pokok',
        'Garam': 'Pangan Pokok', 'Telur Ras': 'Protein Hewani',
        'Telur Kampung': 'Protein Hewani', 'Ayam Ras': 'Protein Hewani',
        'Daging Sapi': 'Protein Hewani', 'Cabai Merah': 'Sayuran',
        'Cabai Rawit': 'Sayuran', 'Bawang Merah': 'Sayuran',
        'Bawang Putih': 'Sayuran', 'Ikan Tongkol': 'Protein Laut',
        'Ikan Teri': 'Protein Laut',
    }
    sembako_data = []
    s_now = _last("harga_sembako.xlsx", "Harga")
    s_prev = _prev("harga_sembako.xlsx", "Harga")
    for key, kategori in sembako_items.items():
        v = s_now.get(key)
        pv = s_prev.get(key)
        if v:
            try:
                vf = float(v)
                chg = ((vf - float(pv)) / float(pv) * 100) if pv else 0
                sembako_data.append({'name': key, 'price': vf, 'chg': chg, 'kategori': kategori})
            except: pass

    # Crypto
    c_now = _last("crypto_monitor.xlsx")
    crypto_data = {}
    if c_now:
        for sym, key in [('BTC','BTC (USD)'),('ETH','ETH (USD)'),('SOL','SOL (USD)'),('ADA','ADA (USD)'),('DOGE','DOGE (USD)'),('XRP','XRP (USD)')]:
            v = c_now.get(key)
            if v: crypto_data[sym] = float(v)
        crypto_data['MCap'] = c_now.get('Total Market Cap (T)', 0)
        crypto_data['Sentimen'] = c_now.get('Sentimen', '-')

    # Emas
    emas = {}
    e_now = _last("emas_harian.xlsx", "Harian")
    if e_now:
        for k in ["Antam Beli","Antam Buyback","Pegadaian","Galeri24","UBS"]:
            v = e_now.get(k)
            if v: emas[k] = float(v)
    else:
        jp = DATA_DIR / "emas_history.json"
        if jp.exists():
            try:
                d = json.loads(jp.read_text())
                if d:
                    last_e = d[-1] if isinstance(d, list) else d
                    if last_e.get('antam_beli'): emas['Antam Beli'] = float(last_e['antam_beli'])
            except: pass

    # Pertanian
    p_now = _last("harga_pertanian_ternak.xlsx", "Harga Komoditas")
    pertanian = {}
    if p_now:
        for k, label in [("Jagung Kering Pipil (Rp/kg)", "Jagung"),
                         ("Kedelai Impor (Rp/kg)", "Kedelai Impor"),
                         ("Pakan Broiler BR1 (Rp/kg)", "Pakan Broiler")]:
            v = p_now.get(k)
            if v: pertanian[label] = float(v)

    # Peternakan
    pet_rows = _read("harga_peternakan_lengkap.xlsx")
    pet_products = {}
    for r in pet_rows:
        n = r.get('Produk','')
        p = r.get('Harga (Rp)',0)
        c = r.get('Kategori','')
        s = r.get('Satuan','Kg')
        if n and p:
            try: pet_products[n.strip()] = {'harga': float(p), 'kategori': c, 'satuan': s}
            except: pass

    # Kurs
    kurs = {}
    k_now = _last("kurs_valuta.xlsx", "Harian")
    if k_now:
        for k, label in [("USD_IDR","USD"),("EUR_IDR","EUR"),("SGD_IDR","SGD"),("MYR_IDR","MYR")]:
            v = k_now.get(k)
            if v: kurs[label] = float(v)

    # Minyak
    m_now = _last("harga_minyak.xlsx", "Harian")
    oil = {}
    if m_now:
        b = m_now.get("Brent_USD")
        w = m_now.get("WTI_USD")
        if b: oil['Brent'] = float(b)
        if w: oil['WTI'] = float(w)
        if b and w: oil['Spread'] = float(b) - float(w)

    # BI Rate
    bi = _last("bi_rate_inflasi.xlsx", "Harian")
    bi_data = {}
    if bi:
        for k in ["BI_Rate","Inflasi_YoY","Inflasi_MoM","IHK"]:
            v = bi.get(k)
            if v is not None: bi_data[k] = float(v)

    # CPO
    cpo = _last("harga_cpo.xlsx", "Harian")
    cpo_data = {}
    if cpo:
        myr = cpo.get("Harga_MYR")
        idr = cpo.get("Harga_IDR")
        chg = cpo.get("Perubahan_Persen")
        if myr: cpo_data['MYR'] = float(myr)
        if idr: cpo_data['IDR'] = float(idr)
        if chg: cpo_data['Chg'] = float(chg)

    # Sentimen
    sent_rows = _read("sentimen_berita.xlsx", "Detail")
    pos = sum(1 for r in sent_rows if str(r.get('Sentimen','')).upper()=='POSITIF')
    neg = sum(1 for r in sent_rows if str(r.get('Sentimen','')).upper()=='NEGATIF')
    neu = sum(1 for r in sent_rows if str(r.get('Sentimen','')).upper()=='NETRAL')
    sent_total = max(len(sent_rows), 1)

    # Pakan
    pak_now = _last("harga_pakan_ternak.xlsx", "Harga Pakan")
    pakan_items = []
    if pak_now:
        for k, v in pak_now.items():
            if v and k != 'Tanggal':
                try:
                    fv = float(v)
                    if fv > 0:
                        name = re.sub(r'\s+', ' ', k).strip().replace(' (Rp/kg)', '')
                        pakan_items.append((name, fv))
                except: pass
    pakan_items.sort(key=lambda x: x[1])

    # ════════════════════════════════════════════
    # 2. BUILD ANALYSIS
    # ════════════════════════════════════════════

    # ── MARKET OVERVIEW ──
    lines.append("## 📊 Market Overview")
    avg_sembako_chg = sum(d['chg'] for d in sembako_data) / max(len(sembako_data), 1)
    risiko_naik = sum(1 for d in sembako_data if d['chg'] > 3)
    risiko_turun = sum(1 for d in sembako_data if d['chg'] < -2)

    overview_parts = []
    overview_parts.append(f"Per {date_str}, indeks komposit menunjukkan.")
    if risiko_naik >= 3:
        overview_parts.append(f"**{risiko_naik} komoditas sembako naik tajam (>3%)** — tekanan inflasi pangan meningkat.")
    if avg_sembako_chg > 1.5:
        overview_parts.append(f"Tren umum sembako **cenderung naik** (rata-rata {avg_sembako_chg:+.1f}%).")
    elif avg_sembako_chg < -1:
        overview_parts.append(f"Tren umum sembako **cenderung turun** (rata-rata {avg_sembako_chg:+.1f}%).")
    else:
        overview_parts.append(f"Sembako relatif **stabil** (rata-rata {avg_sembako_chg:+.1f}%).")

    btc_val = crypto_data.get('BTC', 0)
    if btc_val:
        if btc_val > 65000: overview_parts.append(f"Bitcoin ${btc_val:,.0f} dalam zona **bullish**.")
        elif btc_val > 55000: overview_parts.append(f"Bitcoin ${btc_val:,.0f} **konsolidasi** di atas support.")
        else: overview_parts.append(f"Bitcoin ${btc_val:,.0f} di zona **hati-hati**.")

    if bi_data.get('BI_Rate', 0) >= 6:
        overview_parts.append(f"BI Rate {bi_data['BI_Rate']}% — kebijakan **moneter ketat**.")
    if bi_data.get('Inflasi_YoY', 0) < 3:
        overview_parts.append(f"Inflasi {bi_data['Inflasi_YoY']}% masih **terkendali**.")

    lines.append(" ".join(overview_parts))
    lines.append("")

    # ── TREND NAIK ──
    lines.append("## 📈 Tren Naik ↑")
    naik = sorted([d for d in sembako_data if d['chg'] > 1], key=lambda x: x['chg'], reverse=True)
    if naik:
        for d in naik[:8]:
            lines.append(f"- **{d['name']}**: Rp{d['price']:,.0f}/kg — ↑{d['chg']:+.1f}% ({d['kategori']})")
    else:
        lines.append("- Tidak ada komoditas dengan tren naik signifikan")
    lines.append("")

    # ── TREND TURUN ──
    lines.append("## 📉 Tren Turun ↓")
    turun = sorted([d for d in sembako_data if d['chg'] < -1], key=lambda x: x['chg'])
    if turun:
        for d in turun[:5]:
            lines.append(f"- **{d['name']}**: Rp{d['price']:,.0f}/kg — ↓{d['chg']:.1f}% ({d['kategori']})")
    else:
        lines.append("- Tidak ada komoditas dengan tren turun signifikan")
    lines.append("")

    # ── ANALISIS SAHAM & IHSG ──
    lines.append("## 🏛️ Saham & IHSG")
    s_rows = _read("harga_saham_ihsg.xlsx", "IHSG")
    if s_rows:
        last_s = s_rows[-1]
        ihsg_val = last_s.get("IHSG") or last_s.get("Close")
        chg_s = last_s.get("Chg_%") or last_s.get("Change_%")
        if ihsg_val:
            ihsg_f = float(ihsg_val)
            status = "🟢 Uptrend" if ihsg_f > 6200 else "🟡 Sideways" if ihsg_f > 5600 else "🔴 Downtrend"
            lines.append(f"- IHSG: **{ihsg_val}** — {status}")
            if chg_s: lines.append(f"- Perubahan: {chg_s}%")
    else:
        lines.append("- Data IHSG belum tersedia")
    lines.append("")

    # ── ANALISIS CRYPTO ──
    lines.append("## ₿ Crypto")
    if crypto_data:
        for sym in ['BTC','ETH','SOL','ADA','DOGE','XRP']:
            v = crypto_data.get(sym)
            if v:
                if sym == 'BTC':
                    trend = "🟢 Bullish" if v > 65000 else "🟡 Konsolidasi" if v > 50000 else "🔴 Bearish"
                    lines.append(f"- **BTC**: ${v:,.2f} — {trend}")
                elif sym == 'ETH':
                    ratio = v / crypto_data.get('BTC', 1) * 10000
                    lines.append(f"- **ETH**: ${v:,.2f} (ETH/BTC ratio: {ratio:.1f})")
                else:
                    lines.append(f"- **{sym}**: ${v:,.4f}" if v < 1 else f"- **{sym}**: ${v:,.2f}")
        mcap = crypto_data.get('MCap', 0)
        if mcap: lines.append(f"- Total Market Cap: **${mcap}T**")
        sent = crypto_data.get('Sentimen', '-')
        lines.append(f"- Sentimen pasar: {sent}")
    lines.append("")

    # ── ANALISIS EMAS ──
    lines.append("## 🥇 Emas")
    if emas:
        for k in ["Antam Beli","Antam Buyback","Pegadaian","Galeri24","UBS"]:
            v = emas.get(k)
            if v: lines.append(f"- {k}: **Rp{v:,.0f}/gram**")
        # Calculate margins
        antam = emas.get("Antam Beli", 0)
        buyback = emas.get("Antam Buyback", 0)
        if antam and buyback:
            margin = antam - buyback
            margin_pct = margin / antam * 100
            lines.append(f"- Spread beli-buyback: Rp{margin:,.0f} ({margin_pct:.1f}%)")
        peg = emas.get("Pegadaian", 0)
        if antam and peg and peg > 0:
            premium = (peg - antam) / antam * 100
            lines.append(f"- Premium Pegadaian vs Antam: {premium:+.1f}%")
    else:
        lines.append("- Data emas belum tersedia")
    lines.append("")

    # ── ANALISIS SEMBAKO DETAIL ──
    lines.append("## 🛒 Sembako — Detail")
    if sembako_data:
        # Group by kategori
        groups = {}
        for d in sembako_data:
            k = d['kategori']
            if k not in groups: groups[k] = []
            groups[k].append(d)

        for kategori in ['Pangan Pokok', 'Protein Hewani', 'Protein Laut', 'Sayuran', 'Minyak']:
            items = groups.get(kategori, [])
            if not items: continue
            avg_chg = sum(d['chg'] for d in items) / len(items)
            trend = "↑" if avg_chg > 1 else "↓" if avg_chg < -1 else "→"
            lines.append(f"\n**{kategori}** (rata-rata {trend}{avg_chg:+.1f}%):")
            for d in sorted(items, key=lambda x: abs(x['chg']), reverse=True):
                arrow = "🔴" if d['chg'] > 3 else "🟡" if d['chg'] > 1 else "🟢" if d['chg'] > -1 else "🟡" if d['chg'] > -3 else "🟢"
                lines.append(f"  {arrow} {d['name']}: Rp{d['price']:,.0f}/kg ({d['chg']:+.1f}%)")
    lines.append("")

    # ── ANALISIS PERTANIAN & PAKAN ──
    lines.append("## 🌾 Pertanian & Pakan Ternak")
    if pertanian:
        for name, price in pertanian.items():
            lines.append(f"- {name}: **Rp{price:,.0f}/kg**")
    if pakan_items:
        avg_pakan = sum(p for _, p in pakan_items) / len(pakan_items) if pakan_items else 0
        lines.append(f"\n**23 Bahan Pakan:**")
        lines.append(f"- Termahal: {pakan_items[-1][0]} Rp{pakan_items[-1][1]:,.0f}/kg")
        lines.append(f"- Termurah: {pakan_items[0][0]} Rp{pakan_items[0][1]:,.0f}/kg")
        lines.append(f"- Rata-rata: Rp{avg_pakan:,.0f}/kg")
        # Cost analysis
        if pertanian.get('Pakan Broiler'):
            bp = pertanian['Pakan Broiler']
            margin_vs_avg = (bp - avg_pakan) / avg_pakan * 100
            lines.append(f"- Harga Pakan Broiler Rp{bp:,.0f} vs rata-rata bahan Rp{avg_pakan:,.0f} ({margin_vs_avg:+.0f}% markup)")
    lines.append("")

    # ── ANALISIS PETERNAKAN ──
    lines.append("## 🐄 Peternakan — Margin Analysis")
    if pet_products:
        # Telur chain
        telur_grosir = next((d['harga'] for n,d in pet_products.items() if 'Telur Ayam Ras (Grosir)' in n), 0)
        telur_ecer = next((d['harga'] for n,d in pet_products.items() if 'Telur Ayam Ras Eceran' in n), 0)
        if telur_grosir and telur_ecer:
            margin = telur_ecer - telur_grosir
            lines.append(f"- **Telur Ayam Ras**: Grosir Rp{telur_grosir:,.0f} → Ecer Rp{telur_ecer:,.0f} (margin Rp{margin:,.0f} = {margin/telur_grosir*100:.1f}%)")

        # Ayam chain
        doc = next((d['harga'] for n,d in pet_products.items() if 'DOC Ayam Ras (Super)' in n), 0)
        broiler_hidup = next((d['harga'] for n,d in pet_products.items() if 'Ayam Broiler Hidup' in n), 0)
        ayam_potong = next((d['harga'] for n,d in pet_products.items() if 'Ayam Potong Eceran' in n), 0)
        if doc and broiler_hidup:
            lines.append(f"- **Ayam**: DOC Rp{doc:,.0f}/ekor → Hidup Rp{broiler_hidup:,.0f}/kg → Potong Rp{ayam_potong:,.0f}/kg")
            if ayam_potong:
                lines.append(f"  Margin hidup→potong: Rp{ayam_potong - broiler_hidup:,.0f}/kg ({(ayam_potong-broiler_hidup)/broiler_hidup*100:.1f}%)")

        # Sapi chain
        sapi_hidup = next((d['harga'] for n,d in pet_products.items() if 'Sapi Simental Hidup' in n), 0)
        sapi_daging = next((d['harga'] for n,d in pet_products.items() if 'Daging Sapi Eceran' in n), 0)
        if sapi_hidup and sapi_daging:
            margin = sapi_daging - sapi_hidup
            lines.append(f"- **Sapi**: Hidup Rp{sapi_hidup:,.0f}/kg → Daging Rp{sapi_daging:,.0f}/kg (margin Rp{margin:,.0f} = {margin/sapi_hidup*100:.1f}%)")

        # Kambing
        kam_hidup = next((d['harga'] for n,d in pet_products.items() if 'Kambing Kacang Hidup' in n), 0)
        kam_daging = next((d['harga'] for n,d in pet_products.items() if 'Daging Kambing Eceran' in n), 0)
        if kam_hidup and kam_daging:
            margin = kam_daging - kam_hidup
            lines.append(f"- **Kambing**: Hidup Rp{kam_hidup:,.0f}/kg → Daging Rp{kam_daging:,.0f}/kg (margin Rp{margin:,.0f} = {margin/kam_hidup*100:.1f}%)")
    lines.append("")

    # ── ANALISIS ENERGI ──
    lines.append("## ⛽ Energi & CPO")
    if oil:
        lines.append(f"- Brent: **${oil['Brent']:,.2f}/barel**")
        lines.append(f"- WTI: **${oil['WTI']:,.2f}/barel**")
        if 'Spread' in oil:
            lines.append(f"- Spread Brent-WTI: ${oil['Spread']:,.2f}")
        if oil['Brent'] > 75:
            lines.append(f"- Minyak di zona **relatif tinggi** — berpotensi dorong inflasi energi")
        elif oil['Brent'] < 65:
            lines.append(f"- Minyak di zona **rendah** — mendukung stabilitas BBM domestik")
        else:
            lines.append(f"- Minyak di zona **netral-stabil**")
    if cpo_data:
        lines.append(f"- CPO: **MYR {cpo_data.get('MYR',0):,.0f}/ton** ≈ Rp{cpo_data.get('IDR',0):,.0f}/kg")
        chg_cpo = cpo_data.get('Chg', 0)
        if chg_cpo: lines.append(f"- Perubahan: {chg_cpo:+.2f}% — {'⚠️ turun signifikan' if chg_cpo < -2 else '✅ stabil' if abs(chg_cpo) < 2 else 'naik'}")
    lines.append("")

    # ── KURS & MONETER ──
    lines.append("## 💱 Kurs & Moneter")
    if kurs:
        for k in ['USD','EUR','SGD','MYR']:
            v = kurs.get(k)
            if v:
                status = ""
                if k == 'USD':
                    if v > 16000: status = "⚠️ Rupiah melemah"
                    elif v < 15500: status = "✅ Rupiah menguat"
                    else: status = "🟡 Stabil"
                lines.append(f"- {k}/IDR: **Rp{v:,.0f}** {status}")
    if bi_data:
        bi_val = bi_data.get('BI_Rate', 0)
        lines.append(f"\n**Kebijakan Moneter:**")
        lines.append(f"- BI Rate: **{bi_val}%** {'🔴 Ketat' if bi_val > 6.5 else '🟡 Netral' if bi_val > 5 else '🟢 Akomodatif'}")
        iy = bi_data.get('Inflasi_YoY', 0)
        lines.append(f"- Inflasi YoY: **{iy}%** {'✅ Terkendali' if iy < 3 else '⚠️ Perlu waspada' if iy < 5 else '🔴 Tinggi'}")
        im = bi_data.get('Inflasi_MoM', 0)
        if im: lines.append(f"- Inflasi MoM: {im}%")
        ihk = bi_data.get('IHK', 0)
        if ihk: lines.append(f"- IHK: {ihk}")

        # Real rate analysis
        if bi_val and iy:
            real_rate = bi_val - iy
            lines.append(f"- Real rate: {real_rate:.2f}% {'✅ Positif — menarik untuk deposito' if real_rate > 2 else '🟡 Tipis' if real_rate > 0 else '🔴 Negatif — uang mengecil'}")
    lines.append("")

    # ── SENTIMEN ──
    lines.append("## 📰 Sentimen Berita")
    lines.append(f"- Total artikel: **{sent_total}**")
    lines.append(f"- 🟢 Positif: **{pos}** ({pos*100//sent_total}%)")
    lines.append(f"- ⚪ Netral: **{neu}** ({neu*100//sent_total}%)")
    lines.append(f"- 🔴 Negatif: **{neg}** ({neg*100//sent_total}%)")
    sentiment_score = (pos - neg) / sent_total
    if sentiment_score > 0.1: lines.append(f"- Skor sentimen: **{sentiment_score:+.2f}** — Cenderung positif ✅")
    elif sentiment_score < -0.1: lines.append(f"- Skor sentimen: **{sentiment_score:+.2f}** — Cenderung negatif ⚠️")
    else: lines.append(f"- Skor sentimen: **{sentiment_score:+.2f}** — Netral ⚪")
    lines.append("")

    # ════════════════════════════════════════════
    # 3. RISIKO, REKOMENDASI, PREDIKSI
    # ════════════════════════════════════════════

    lines.append("## ⚠️ Risiko & Warning")
    risks = []

    # Sembako
    hot_items = [d for d in sembako_data if d['chg'] > 5]
    if hot_items:
        names = ", ".join(d['name'] for d in hot_items)
        risks.append(f"🔴 **Inflasi pangan**: {names} naik >5% — beban konsumen meningkat")

    if bi_data.get('BI_Rate', 0) > 6:
        risks.append(f"🔴 **BI Rate {bi_data['BI_Rate']}%**: Biaya pinjaman tinggi — tekanan pelaku usaha")
    if bi_data.get('Inflasi_YoY', 0) > 4:
        risks.append(f"🔴 **Inflasi {bi_data['Inflasi_YoY']}%**: Daya beli masyarakat tergerus")
    if kurs.get('USD', 0) > 16000:
        risks.append(f"🟡 **USD/Rp {kurs['USD']:,.0f}**: Rupiah lemah — impor jadi mahal")
    if oil.get('Brent', 0) > 80:
        risks.append(f"🟡 **Minyak ${oil['Brent']}**: Berpotensi dorong BBM & inflasi")
    if neg > pos * 2 and sent_total > 50:
        risks.append(f"🟡 **Sentimen negatif** {neg} vs positif {pos}: Pasar pesimis")
    if not risks:
        risks.append("- Tidak ada risiko signifikan terdeteksi")

    for r in risks[:5]:
        lines.append(f"- {r}")
    lines.append("")

    # Rekomendasi
    lines.append("## 💡 Rekomendasi")

    # Petani
    pakan_turun = any(d['chg'] < -1 for d in sembako_data if 'Pakan' in d.get('name',''))
    lines.append("- **Petani/ternak**:")
    if pakan_turun:
        lines.append("  - Harga bahan baku pakan turun — **saatnya stok pakan**")
    else:
        lines.append("  - Pantau harga pakan secara berkala")
    if sembako_data:
        daging_up = any(d['chg'] > 3 for d in sembako_data if 'Daging' in d['name'])
        if daging_up:
            lines.append("  - Daging naik — **peluang jual ternak lebih menguntungkan**")
    lines.append("  - Variasikan pakan: gunakan bahan termurah (Onggok Rp2,386, Gaplek Rp3,202)")

    # Konsumen
    lines.append("- **Konsumen**:")
    hot = [d for d in sembako_data if d['chg'] > 3]
    cheap = [d for d in sembako_data if d['chg'] < -2]
    if hot:
        lines.append(f"  - Harga naik: {', '.join(d['name'] for d in hot[:3])} — beli seperlunya")
    if cheap:
        lines.append(f"  - Harga turun: {', '.join(d['name'] for d in cheap[:3])}")
    if bi_data.get('BI_Rate', 0) > 6:
        lines.append("  - BI Rate tinggi — tunda kredit belanja, prioritaskan kebutuhan")

    # Investor
    lines.append("- **Investor**:")
    if btc_val and btc_val > 60000:
        lines.append("  - BTC ${:,.0f} dalam range konsolidasi — DCA strategis".format(btc_val))
    if bi_data.get('Real_Rate', bi_data.get('BI_Rate',0) - bi_data.get('Inflasi_YoY',0)) > 2:
        lines.append("  - Real rate positif — deposito/government bond menarik")
    if emas.get('Antam Beli', 0) > 1500000:
        lines.append("  - Emas Rp{:.0f}/g — safe haven, alokasi 10-15% portofolio".format(emas['Antam Beli']))
    lines.append("  - Diversifikasi: 40% pasar uang, 30% saham, 20% komoditas, 10% crypto")
    lines.append("")

    # Prediksi
    lines.append("## 🎯 Prediksi 3 Hari ke Depan")

    # Based on actual data
    if avg_sembako_chg > 2:
        lines.append(f"- Sembako: **Cenderung naik** — {risiko_naik} komoditas sudah naik tajam, berpotensi lanjut")
    elif avg_sembako_chg < -1:
        lines.append(f"- Sembako: **Cenderung turun** — beberapa komoditas sudah koreksi")
    else:
        lines.append(f"- Sembako: **Stabil** — fluktuasi wajar")

    if btc_val > 65000:
        lines.append(f"- Crypto: **Positif** — BTC ${btc_val:,.0f} di atas resistance, target $65k+")
    elif btc_val > 55000:
        lines.append(f"- Crypto: **Sideways** — BTC ${btc_val:,.0f} range-bound, menunggu catalyst")
    else:
        lines.append(f"- Crypto: **Hati-hati** — BTC ${btc_val:,.0f}, support $50k kritis")

    if bi_data.get('BI_Rate', 0) > 6:
        lines.append(f"- Rupiah: **Rentan** — BI Rate {bi_data['BI_Rate']}% belum cukup defend rupiah")
    if oil.get('Brent', 0) > 75:
        lines.append("- Minyak: **Naik** — berpotensi dorong harga BBM")

    lines.append("- Pantau: Rilis data IHSG bulanan, kebijakan BI berikutnya, sentimen global")
    lines.append("")
    lines.append("---")
    lines.append(f"_Analisis otomatis | {date_str} | Data dari 12 sumber real-time_")

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
