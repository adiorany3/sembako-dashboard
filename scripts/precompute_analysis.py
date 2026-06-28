#!/usr/bin/env python3
"""
Precompute AI Market Analysis — V4 COMPREHENSIVE
================================================
Reads ALL data → calculates technical indicators, correlations, anomaly detection,
seasonal patterns, confidence scoring → generates deep analysis.

Two modes:
  1. Groq API (VPS) — AI-enhanced with full context
  2. Rule-based (fallback) — algorithmic with all indicators

Flow: Excel files → indicators.py → prompt → Groq/rule → daily_analysis.json
"""
import os, json, sys, traceback, re
from pathlib import Path
from datetime import datetime
import openpyxl

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from indicators import (
    moving_average, ema, rate_of_change, volatility,
    find_support_resistance, trend_direction, momentum_score,
    detect_anomalies, pearson_correlation, confidence_score,
    get_seasonal_context, full_analysis
)

DATA_DIR = Path.home() / "sembako" / "data"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def ts():
    return datetime.now().strftime("[%H:%M:%S]")


def read_sheet(fn, sheet=None):
    """Read Excel → list of dicts."""
    p = DATA_DIR / fn
    if not p.exists(): return []
    try:
        wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
        ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if len(rows) < 2: return []
        h = [re.sub(r'\s+', ' ', str(c).strip()) if c else f'c{i}' for i,c in enumerate(rows[0])]
        return [dict(zip(h, row)) for row in rows[1:]]
    except: return []


def last_row(fn, sheet=None, n=0):
    d = read_sheet(fn, sheet)
    return d[-(n+1)] if len(d) > n else {}


def load_all_history():
    """Load ALL historical data for technical analysis."""
    print(f"{ts()} 📂 Loading historical data...")

    data = {}

    # Sembako (31 rows)
    rows = read_sheet("harga_sembako.xlsx", "Harga")
    if rows:
        keys = ["Ber","Telur Ras","Gula Pasir","Cabai Merah","Minyak Goreng","Bawang Merah","Daging Sapi"]
        for k in keys:
            vals = [float(r.get(k, 0)) for r in rows if r.get(k) and float(str(r.get(k,0) or 0)) > 0]
            if len(vals) >= 2:
                data[f"sembako_{k}"] = vals
        print(f"  Sembako: {len(rows)} rows, {len([k for k in data if k.startswith('sembako')])} series")

    # Crypto (2 rows)
    rows = read_sheet("crypto_monitor.xlsx")
    if rows:
        for col in ["btc_usd","eth_usd","sol_usd"]:
            vals = [float(r.get(col, 0)) for r in rows if r.get(col)]
            if len(vals) >= 2:
                data[f"crypto_{col}"] = vals
        print(f"  Crypto: {len(rows)} rows")

    # Pertanian (1 row only)
    rows = read_sheet("harga_pertanian_ternak.xlsx", "Harga Komoditas")
    if rows:
        r = rows[-1]
        for k in ["Jagung Kering Pipil (Rp/kg)", "Kedelai Impor (Rp/kg)", "Pakan Broiler BR1 (Rp/kg)"]:
            v = r.get(k)
            if v:
                data[f"pertanian_{k.split()[0]}"] = [float(v)]  # single point
        print(f"  Pertanian: {len(rows)} rows")

    # Peternakan (3784 rows — rich!)
    rows = read_sheet("harga_peternakan_lengkap.xlsx")
    if rows:
        # Group by product, take latest price per day
        from collections import defaultdict
        prod_daily = defaultdict(dict)
        for r in rows:
            n = r.get("Produk","").strip()
            p = r.get("Harga (Rp)", 0)
            t = str(r.get("Tanggal", ""))[:10]
            if n and p and t:
                try: prod_daily[n][t] = float(p)
                except: pass
        # Get last 30 days per key product
        key_products = ["Telur Ayam Ras (Grosir)", "Ayam Broiler Hidup", "Daging Sapi Eceran",
                        "Daging Kambing Eceran", "Telur Ayam Kampung"]
        for pk in key_products:
            if pk in prod_daily:
                daily = sorted(prod_daily[pk].items())[-30:]
                vals = [v for _, v in daily]
                if len(vals) >= 2:
                    data[f"pet_{pk.split()[0]}_{pk.split()[-1]}"] = vals
        print(f"  Peternakan: {len(rows)} rows, {len([k for k in data if k.startswith('pet_')])} product series")

    # Kurs (1 row — but history from Excel)
    rows = read_sheet("kurs_valuta.xlsx", "Harian")
    if rows:
        for col in ["USD_IDR","EUR_IDR","SGD_IDR"]:
            vals = [float(r.get(col, 0)) for r in rows if r.get(col) and float(str(r.get(col,0) or 0)) > 1000]
            if len(vals) >= 2:
                data[f"kurs_{col}"] = vals
        print(f"  Kurs: {len(rows)} rows")

    # Minyak (1 row)
    rows = read_sheet("harga_minyak.xlsx", "Harian")
    if rows:
        b = [float(r.get("Brent_USD",0)) for r in rows if r.get("Brent_USD")]
        w = [float(r.get("WTI_USD",0)) for r in rows if r.get("WTI_USD")]
        if len(b) >= 2: data["oil_brent"] = b
        if len(w) >= 2: data["oil_wti"] = w
        print(f"  Minyak: {len(rows)} rows")

    # BI Rate (1 row)
    bi = last_row("bi_rate_inflasi.xlsx", "Harian")
    if bi:
        for k in ["BI_Rate","Inflasi_YoY","IHK"]:
            v = bi.get(k)
            if v: data[f"bi_{k}"] = [float(v)]
        print(f"  BI Rate: 1 snapshot")

    # CPO (1 row)
    cpo = last_row("harga_cpo.xlsx", "Harian")
    if cpo:
        myr = cpo.get("Harga_MYR")
        if myr: data["cpo_myr"] = [float(myr)]
        print(f"  CPO: 1 snapshot")

    # Sentimen (301 rows)
    rows = read_sheet("sentimen_berita.xlsx", "Detail")
    if rows:
        # Daily sentiment aggregate
        from collections import defaultdict
        daily_sent = defaultdict(lambda: {"pos":0,"neg":0,"neu":0,"total":0})
        for r in rows:
            t = str(r.get("Tanggal",""))[:10]
            s = str(r.get("Sentimen","")).upper()
            if t:
                daily_sent[t]["total"] += 1
                if s == "POSITIF": daily_sent[t]["pos"] += 1
                elif s == "NEGATIF": daily_sent[t]["neg"] += 1
                else: daily_sent[t]["neu"] += 1
        # Convert to score series
        dates_sorted = sorted(daily_sent.keys())
        scores = []
        for d in dates_sorted:
            ds = daily_sent[d]
            if ds["total"] > 0:
                score = (ds["pos"] - ds["neg"]) / ds["total"]
                scores.append(score)
        if scores:
            data["sentimen_score"] = scores
        print(f"  Sentimen: {len(rows)} articles, {len(scores)} daily scores")

    # Saham (31 rows)
    rows = read_sheet("harga_saham_ihsg.xlsx", "IHSG")
    if rows:
        vals = []
        for r in rows:
            v = r.get("IHSG") or r.get("Close")
            if v:
                try: vals.append(float(v))
                except: pass
        if len(vals) >= 2:
            data["saham_ihsg"] = vals
        print(f"  Saham: {len(rows)} rows")

    # Pakan (61 rows)
    rows = read_sheet("harga_pakan_ternak.xlsx", "Harga Pakan")
    if rows:
        for k in rows[-1].keys():
            if k and k != "Tanggal":
                vals = []
                for r in rows:
                    v = r.get(k)
                    if v:
                        try:
                            fv = float(v)
                            if fv > 0: vals.append(fv)
                        except (ValueError, TypeError):
                            pass
                if len(vals) >= 2:
                    data[f"pakan_{k[:20]}"] = vals
        print(f"  Pakan: {len(rows)} rows, {len([k for k in data if k.startswith('pakan')])} series")

    # Emas (from JSON)
    jp = DATA_DIR / "emas_history.json"
    if jp.exists():
        try:
            d = json.loads(jp.read_text())
            if isinstance(d, list) and len(d) > 1:
                vals = [float(e.get("antam_beli", 0)) for e in d if e.get("antam_beli")]
                if len(vals) >= 2:
                    data["emas_antam"] = vals
                print(f"  Emas: {len(d)} days history")
        except: pass

    total = sum(len(v) for v in data.values())
    print(f"{ts()} ✅ {len(data)} series, {total} data points total")
    return data


def compute_all_indicators(history):
    """Compute technical indicators for all series."""
    print(f"{ts()} 📐 Computing indicators...")
    indicators = {}

    for name, values in history.items():
        if len(values) >= 2:
            result = full_analysis(name, values)
            indicators[name] = result

    # Cross-correlations
    corr_pairs = [
        ("kurs_USD_IDR", "emas_antam", "USD↔Emas"),
        ("oil_brent", "cpo_myr", "Minyak↔CPO"),
        ("sembako_Telur Ras", "sembako_Daging Sapi", "Telur↔Daging"),
        ("sembako_Gula Pasir", "sembako_Ber", "Gula↔Beras"),
    ]

    correlations = {}
    for a, b, label in corr_pairs:
        if a in history and b in history:
            corr = pearson_correlation(history[a][-min(len(history[a]),len(history[b])):],
                                       history[b][-min(len(history[a]),len(history[b])):])
            if corr is not None:
                correlations[label] = corr

    # Anomalies — only on genuine time-series (skip cross-sectional like pakan)
    anomalies = []
    time_series_prefixes = ("sembako_", "crypto_", "pet_", "saham_", "sentimen_", "kurs_", "oil_")
    for name, values in history.items():
        if not any(name.startswith(p) for p in time_series_prefixes):
            continue  # skip cross-sectional data
        if len(values) >= 3:
            detected = detect_anomalies(values, threshold_pct=8)
            for a in detected:
                anomalies.append({"series": name, **a})

    # Seasonal
    seasonal = get_seasonal_context()

    print(f"{ts()} ✅ {len(indicators)} indicator sets, {len(correlations)} correlations, {len(anomalies)} anomalies")
    return indicators, correlations, anomalies, seasonal


def build_prompt(history, indicators, correlations, anomalies, seasonal):
    """Build comprehensive prompt for Groq API."""
    lines = []
    lines.append("ANALISA KOMPREHENSIF PASAR INDONESIA")
    lines.append(f"Tanggal: {datetime.now().strftime('%d %B %Y, %H:%M')}")
    lines.append(f"Data points: {sum(len(v) for v in history.values())}")
    lines.append("")

    # Current prices
    lines.append("=== HARGA TERKINI ===")
    snapshot_keys = {
        "Ber (Beras)": history.get("sembako_Ber", [0])[-1],
        "Telur Ras": history.get("sembako_Telur Ras", [0])[-1],
        "Gula Pasir": history.get("sembako_Gula Pasir", [0])[-1],
        "Cabai Merah": history.get("sembako_Cabai Merah", [0])[-1],
        "Minyak Goreng": history.get("sembako_Minyak Goreng", [0])[-1],
        "Daging Sapi": history.get("sembako_Daging Sapi", [0])[-1],
        "BTC (USD)": history.get("crypto_btc_usd", [0])[-1],
        "ETH (USD)": history.get("crypto_eth_usd", [0])[-1],
    }
    for k, v in snapshot_keys.items():
        if v:
            lines.append(f"  {k}: Rp{v:,.0f}" if v > 1000 else f"  {k}: ${v:,.2f}")

    lines.append("")

    # Technical indicators summary
    lines.append("=== INDIKATOR TEKNIS ===")
    for name, ind in sorted(indicators.items()):
        if ind.get("error"): continue
        trend = ind.get("trend", "n/a")
        mom = ind.get("momentum", 0)
        vol = ind.get("volatility")
        conf = ind.get("confidence", 0)
        ma5 = ind.get("ma5")
        ma20 = ind.get("ma20")
        roc = ind.get("roc_5d")
        support = ind.get("support", [])
        resistance = ind.get("resistance", [])

        trend_icon = "🟢" if trend == "uptrend" else "🔴" if trend == "downtrend" else "🟡"

        lines.append(f"  {name}:")
        lines.append(f"    Harga: Rp{ind['current']:,.0f} ({ind['change_pct']:+.1f}%) | {trend_icon} {trend}")
        if ma5: lines.append(f"    MA5: Rp{ma5:,.0f} | MA20: {'Rp'+f'{ma20:,.0f}' if ma20 else '-'}")
        if vol is not None: lines.append(f"    Volatility: {vol:.2f}% | Momentum: {mom}/100")
        if roc is not None: lines.append(f"    ROC(5): {roc:+.1f}%")
        if support: lines.append(f"    Support: {', '.join(f'Rp{s:,.0f}' for s in support[:2])}")
        if resistance: lines.append(f"    Resistance: {', '.join(f'Rp{r:,.0f}' for r in resistance[:2])}")
        lines.append(f"    Confidence: {'⭐'*conf} ({conf}/5)")

    lines.append("")

    # Correlations
    if correlations:
        lines.append("=== KORELASI LINTAS SEKTOR ===")
        for label, corr in correlations.items():
            strength = "kuat" if abs(corr) > 0.7 else "sedang" if abs(corr) > 0.4 else "lemah"
            direction = "positif" if corr > 0 else "negatif"
            lines.append(f"  {label}: {corr:+.3f} (korelasi {strength} {direction})")
        lines.append("")

    # Anomalies
    if anomalies:
        lines.append("=== ANOMALI TERDETEKSI ===")
        for a in anomalies[:10]:
            lines.append(f"  ⚠️ {a['series']}: {a['type']} {a['change_pct']:+.1f}% ({a['from']:,.0f} → {a['to']:,.0f})")
        lines.append("")

    # Seasonal
    if seasonal:
        lines.append("=== KONTEKS MUSIMAN ===")
        for s in seasonal:
            lines.append(f"  {s['pattern']}: {s['effect']} (dampak: {s['impact']})")
        lines.append("")

    return "\n".join(lines)


def build_rule_analysis(history, indicators, correlations, anomalies, seasonal):
    """Generate comprehensive rule-based analysis from computed indicators."""
    date_str = datetime.now().strftime("%d %B %Y")
    lines = []

    # ── EXECUTIVE SUMMARY ──
    lines.append("## 📊 Executive Summary")

    # Count trends
    trends = [v.get("trend","n/a") for v in indicators.values() if v.get("trend")]
    up = trends.count("uptrend")
    down = trends.count("downtrend")
    side = trends.count("sideways")

    total_conf = [v.get("confidence", 0) for v in indicators.values() if v.get("confidence")]
    avg_conf = sum(total_conf) / max(len(total_conf), 1)

    # Overall market direction
    if up > down * 1.5:
        market_dir = "**POSITIF** 🟢 — mayoritas komoditas uptrend"
    elif down > up * 1.5:
        market_dir = "**NEGATIF** 🔴 — mayoritas komoditas downtrend"
    else:
        market_dir = "**CAMPURAN** 🟡 — tren mixed antar sektor"

    lines.append(f"Per {date_str}, kondisi pasar {market_dir}.")
    lines.append(f"- {up} komoditas uptrend, {down} downtrend, {side} sideways")
    lines.append(f"- Rata-rata confidence level: {avg_conf:.1f}/5 {'⭐' * round(avg_conf)}")

    if anomalies:
        high_anomaly = [a for a in anomalies if abs(a['change_pct']) > 10]
        if high_anomaly:
            lines.append(f"- ⚠️ **{len(high_anomaly)} anomali signifikan** terdeteksi (pergerakan >10%)")

    if seasonal:
        active = [s for s in seasonal if s['impact'] == 'high']
        if active:
            lines.append(f"- 🌙 **Konteks musiman**: {active[0]['effect']}")
    lines.append("")

    # ── SEKTOR SEMBAKO ──
    lines.append("## 🛒 Sembako — Analisa Teknis")
    sembako_keys = [k for k in indicators if k.startswith("sembako_")]
    if sembako_keys:
        lines.append("| Komoditas | Harga | MA5 | MA20 | Trend | Momentum | Volatility | Conf |")
        lines.append("|-----------|-------|-----|------|-------|----------|-----------|------|")
        for k in sorted(sembako_keys):
            ind = indicators[k]
            name = k.replace("sembako_", "")
            cur = f"Rp{ind['current']:,.0f}"
            ma5 = f"Rp{ind['ma5']:,.0f}" if ind.get('ma5') else "-"
            ma20 = f"Rp{ind['ma20']:,.0f}" if ind.get('ma20') else "-"
            t = "🟢↑" if ind['trend'] == 'uptrend' else "🔴↓" if ind['trend'] == 'downtrend' else "🟡→"
            mom = f"{ind['momentum']:+d}"
            vol = f"{ind['volatility']:.1f}%" if ind.get('volatility') else "-"
            conf = "⭐" * ind['confidence']
            lines.append(f"| {name} | {cur} | {ma5} | {ma20} | {t} | {mom} | {vol} | {conf} |")
    lines.append("")

    # ── SEKTOR CRYPTO ──
    lines.append("## ₿ Crypto — Analisa Teknis")
    crypto_keys = [k for k in indicators if k.startswith("crypto_")]
    if crypto_keys:
        for k in sorted(crypto_keys):
            ind = indicators[k]
            name = k.replace("crypto_", "").upper()
            t = "🟢 Bullish" if ind['trend'] == 'uptrend' else "🔴 Bearish" if ind['trend'] == 'downtrend' else "🟡 Sideways"
            lines.append(f"**{name}**: ${ind['current']:,.2f} ({ind['change_pct']:+.1f}%) {t}")
            if ind.get('ma5'): lines.append(f"  MA5: ${ind['ma5']:,.2f}")
            if ind.get('volatility'): lines.append(f"  Volatility: {ind['volatility']:.2f}%")
            sr = ind
            if sr.get('support'): lines.append(f"  Support: {', '.join(f'${s:,.2f}' for s in sr['support'][:2])}")
            if sr.get('resistance'): lines.append(f"  Resistance: {', '.join(f'${r:,.2f}' for r in sr['resistance'][:2])}")
            lines.append(f"  Confidence: {'⭐'*ind['confidence']} ({ind['confidence']}/5)")
            lines.append("")
    else:
        lines.append("- Data historis crypto belum cukup untuk analisa teknis")
        lines.append("")

    # ── PETERNAKAN — Margin Analysis ──
    lines.append("## 🐄 Peternakan — Margin & Chain")
    pet_keys = [k for k in indicators if k.startswith("pet_")]
    if pet_keys:
        lines.append("| Produk | Harga | Trend | Momentum | Volatility |")
        lines.append("|--------|-------|-------|----------|-----------|")
        for k in sorted(pet_keys):
            ind = indicators[k]
            name = k.replace("pet_", "")
            t = "🟢↑" if ind['trend'] == 'uptrend' else "🔴↓" if ind['trend'] == 'downtrend' else "🟡→"
            lines.append(f"| {name} | Rp{ind['current']:,.0f} | {t} | {ind['momentum']:+d} | {ind.get('volatility','-')} |")
        lines.append("")

    # ── CROSS-SECTOR CORRELATIONS ──
    if correlations:
        lines.append("## 🔗 Korelasi Lintas Sektor")
        for label, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
            strength = "🔴 Kuat" if abs(corr) > 0.7 else "🟡 Sedang" if abs(corr) > 0.4 else "⚪ Lemah"
            direction = "positif" if corr > 0 else "negatif"
            lines.append(f"- **{label}**: {corr:+.3f} — korelasi {strength} {direction}")
            if corr > 0.7:
                lines.append(f"  → Keduanya bergerak searah — jika {label.split('↔')[0]} naik, {label.split('↔')[1]} cenderung naik juga")
            elif corr < -0.7:
                lines.append(f"  → Bergerak berlawanan — diversifikasi otomatis")
        lines.append("")

    # ── ANOMALI ──
    if anomalies:
        lines.append("## ⚠️ Anomali & Alert")
        for a in sorted(anomalies, key=lambda x: abs(x['change_pct']), reverse=True)[:8]:
            icon = "🔴" if a['type'] == 'crash' else "🟢"
            lines.append(f"- {icon} **{a['series']}**: {a['change_pct']:+.1f}% ({a['from']:,.0f} → {a['to']:,.0f})")
        lines.append("")
    else:
        lines.append("## ✅ Stabilitas Harga")
        lines.append("- Tidak ada anomali signifikan terdeteksi")
        lines.append("")

    # ── SEASONAL CONTEXT ──
    if seasonal:
        lines.append("## 🌙 Konteks Musiman")
        for s in seasonal:
            impact_icon = "🔴" if s['impact'] == 'high' else "🟡" if s['impact'] == 'medium' else "⚪"
            lines.append(f"- {impact_icon} **{s['pattern'].replace('_',' ').title()}**: {s['effect']}")
        lines.append("")

    # ── RISK ASSESSMENT ──
    lines.append("## ⚠️ Risk Assessment")
    risks = []

    # Check high volatility items
    high_vol = [(k, v) for k, v in indicators.items()
                if v.get('volatility') and v['volatility'] > 5 and not v.get('error')]
    if high_vol:
        names = ", ".join(k.split("_",1)[-1] for k,_ in high_vol[:3])
        risks.append(f"🔴 **Volatil**: {names} — volatility >5%, berisiko fluktuasi tajam")

    # Check downtrend
    downtrends = [(k, v) for k, v in indicators.items()
                  if v.get('trend') == 'downtrend' and not v.get('error')]
    if len(downtrends) >= 3:
        names = ", ".join(k.split("_",1)[-1] for k,_ in downtrends[:3])
        risks.append(f"🔴 **Downtrend**: {names} — tekanan jual berkelanjutan")

    # Check anomalies
    crashes = [a for a in anomalies if a['type'] == 'crash' and abs(a['change_pct']) > 10]
    if crashes:
        risks.append(f"🔴 **Crash detected**: {len(crashes)} komoditas turun >10%")

    # Low confidence
    low_conf = [(k, v) for k, v in indicators.items()
                if v.get('confidence', 5) <= 2 and not v.get('error')]
    if low_conf:
        names = ", ".join(k.split("_",1)[-1] for k,_ in low_conf[:3])
        risks.append(f"🟡 **Confidence rendah**: {names} — data kurang, prediksi kurang reliable")

    # Strong correlation risk
    strong_neg = [(l, c) for l, c in correlations.items() if c < -0.7]
    if strong_neg:
        lines.append(f"- ⚠️ Korelasi negatif kuat: {', '.join(l for l,_ in strong_neg)}")

    if not risks:
        risks.append("- ✅ Tidak ada risiko signifikan terdeteksi")

    for r in risks:
        lines.append(f"- {r}")
    lines.append("")

    # ── REKOMENDASI with CONFIDENCE ──
    lines.append("## 💡 Rekomendasi Berbasis Data")

    # Petani/ternak
    lines.append("**🌾 Petani & Peternak:**")
    pakan_vol = indicators.get("pakan_Bungkil Kelapa", {})
    if pakan_vol.get("trend") == "downtrend":
        lines.append("- ⭐⭐⭐⭐ Pakan bahan mentah downtrend — **stok sekarang** (confidence tinggi)")
    elif pakan_vol.get("trend") == "uptrend":
        lines.append("- ⭐⭐⭐ Pakan bahan mentah uptrend — **tunda stok, beli bertahap**")

    telur_ind = indicators.get("sembako_Telur Ras", {})
    if telur_ind.get("trend") == "uptrend" and telur_ind.get("momentum", 0) > 50:
        lines.append("- ⭐⭐⭐⭐ Telur uptrend kuat — **perluasan produksi menguntungkan**")
    elif telur_ind.get("trend") == "downtrend":
        lines.append("- ⭐⭐⭐ Telur downtrend — **jaga volume, kurangi stok berlebih**")

    sapi_ind = indicators.get("sembako_Daging Sapi", {})
    if sapi_ind.get("trend") == "uptrend":
        lines.append("- ⭐⭐⭐ Daging sapi naik — **peluang jual ternak lebih menguntungkan**")

    lines.append("")

    # Konsumen
    lines.append("**🛒 Konsumen:**")
    hot_items = [(k.replace("sembako_",""), v) for k, v in indicators.items()
                 if k.startswith("sembako_") and v.get("change_pct", 0) > 3 and not v.get("error")]
    if hot_items:
        names = ", ".join(n for n,_ in hot_items[:3])
        lines.append(f"- ⭐⭐⭐ **Harga naik signifikan**: {names} — beli seperlunya")
    cold_items = [(k.replace("sembako_",""), v) for k, v in indicators.items()
                  if k.startswith("sembako_") and v.get("change_pct", 0) < -2 and not v.get("error")]
    if cold_items:
        names = ", ".join(n for n,_ in cold_items[:3])
        lines.append(f"- ⭐⭐⭐ **Harga turun**: {names} — moment tepat untuk stok")
    lines.append("")

    # Investor
    lines.append("**📈 Investor:**")
    btc_ind = indicators.get("crypto_btc_usd", {})
    if btc_ind.get("trend") == "uptrend":
        lines.append(f"- ⭐⭐⭐⭐ BTC ${btc_ind.get('current',0):,.0f} uptrend — **DCA aktif**")
    elif btc_ind.get("trend") == "downtrend":
        lines.append(f"- ⭐⭐⭐ BTC ${btc_ind.get('current',0):,.0f} downtrend — **wait & see, support: ${btc_ind.get('support',['?'])[0] if btc_ind.get('support') else '?'}**")

    if correlations.get("USD↔Emas", 0) < -0.5:
        lines.append("- ⭐⭐⭐ USD↔Emas negatif — **lindungi portofolio dengan emas saat USD lemah**")

    lines.append("- Diversifikasi: 40% pasar uang, 30% ekuitas, 20% komoditas, 10% crypto")
    lines.append("")

    # ── PREDIKSI ──
    lines.append("## 🎯 Prediksi 7 Hari ke Depan")

    for sector_name, prefix, icon in [
        ("Sembako", "sembako_", "🛒"),
        ("Crypto", "crypto_", "₿"),
    ]:
        sector_keys = [k for k in indicators if k.startswith(prefix) and not indicators[k].get("error")]
        if not sector_keys: continue

        up_count = sum(1 for k in sector_keys if indicators[k].get("trend") == "uptrend")
        down_count = sum(1 for k in sector_keys if indicators[k].get("trend") == "downtrend")
        avg_roc = sum(indicators[k].get("roc_5d", 0) or 0 for k in sector_keys) / max(len(sector_keys), 1)

        if up_count > down_count * 2:
            pred = "🟢 **Cenderung Naik**"
        elif down_count > up_count * 2:
            pred = "🔴 **Cenderung Turun**"
        else:
            pred = "🟡 **Sideways/Mixed**"

        lines.append(f"{icon} **{sector_name}**: {pred} (↑{up_count} ↓{down_count} | ROC rata-rata: {avg_roc:+.1f}%)")
    lines.append("")

    lines.append("**Faktor yang perlu dipantau:**")
    lines.append("- Kebijakan BI Rate berikutnya (apotek moneter)")
    lines.append("- Sentimen global: Fed rate decision, crypto regulation")
    lines.append("- Cuaca: potensi El Niño affect pertanian")
    if seasonal:
        lines.append(f"- Musiman: {seasonal[0]['effect']}")
    lines.append("")
    lines.append("---")
    lines.append(f"_Analisis komprehensif | {date_str} | {sum(len(v) for v in history.values())} data points | {len(indicators)} indikator | {len(correlations)} korelasi_")

    return "\n".join(lines)


def call_groq(prompt, data_text):
    """Call Groq API with comprehensive data context."""
    import urllib.request
    if not GROQ_API_KEY:
        return ""

    SYSTEM_PROMPT = """Anda adalah analis pasar komoditas Indonesia profesional. Analisa berdasarkan data teknis dan fundamental.

Output dalam Bahasa Indonesia dengan format Markdown:
## 📊 Executive Summary
Ringkasan kondisi pasar 2-3 kalimat. Sebutkan angka spesifik.

## 📈 Analisa Sektoral
Untuk setiap sektor (Sembako, Crypto, Emas, Pertanian, Peternakan, Energi, Kurs, Moneter):
- Sebutkan harga aktual, MA5/MA20, trend (uptrend/downtrend/sideways)
- Sebutkan momentum (skor -100 to +100)
- Sebutkan support/resistance jika ada
- Berikan confidence level ⭐ (1-5)

## 🔗 Korelasi
Jelaskan korelasi antar sektor dan implikasinya.

## ⚠️ Risiko & Anomali
Sebutkan anomali, volatilitas tinggi, atau risiko yang terdeteksi.

## 💡 Rekomendasi
Rekomendasi SPESIFIK dengan confidence score:
- Petani/Peternak: kapan stok pakan, kapan jual ternak
- Konsumen: kapan beli, komoditas mana yang perlu diwaspadai
- Investor: strategi DCA, diversifikasi, hedging

## 🎯 Prediksi 7 Hari
Berdasarkan momentum dan trend, prediksi arah pasar.

Penting: Gunakan angka spesifik dari data. Jangan generalisasi."""

    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DATA PASAR:\n{data_text}\n\n{prompt}"}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    })

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload.encode(),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]


def main():
    print(f"{ts()} 🧠 AI Market Analysis V4 — COMPREHENSIVE")
    print(f"{'=' * 50}")

    # 1. Load all historical data
    history = load_all_history()
    if not history:
        print(f"{ts()} ❌ No data available")
        return

    # 2. Compute indicators
    indicators, correlations, anomalies, seasonal = compute_all_indicators(history)

    # 3. Build prompt
    prompt = build_prompt(history, indicators, correlations, anomalies, seasonal)
    print(f"{ts()} 📝 Prompt: {len(prompt)} chars")

    # 4. Try Groq first
    analysis = ""
    source = "groq_v4"
    try:
        print(f"{ts()} 🤖 Calling Groq (llama-3.1-8b-instant)...")
        analysis = call_groq(
            "Buat analisa komprehensif berdasarkan data di atas. "
            "Sertakan angka spesifik, support/resistance, confidence score.",
            prompt
        )
        if analysis and len(analysis) > 200:
            print(f"{ts()} ✅ Groq response: {len(analysis)} chars")
        else:
            analysis = ""
            source = "rule_based_v4"
    except Exception as e:
        print(f"{ts()} ⚠️ Groq failed: {e}")
        source = "rule_based_v4"

    # 5. Fallback to rule-based
    if not analysis:
        print(f"{ts()} 🔄 Generating comprehensive rule-based analysis...")
        analysis = build_rule_analysis(history, indicators, correlations, anomalies, seasonal)
        source = "rule_based_v4"

    print(f"{ts()} ✅ Analysis: {len(analysis)} chars ({source})")
    print(f"{ts()} Preview: {analysis[:200]}...")

    # 6. Save
    output = {
        "analysis": analysis,
        "source": source,
        "model": "llama-3.1-8b-instant" if "groq" in source else "rule_based_v4",
        "generated_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "timestamp": datetime.now().isoformat(),
        "cached": False,
        "refresh_in_seconds": 28800,
        "indicators_count": len(indicators),
        "correlations_count": len(correlations),
        "anomalies_count": len(anomalies),
        "data_points": sum(len(v) for v in history.values()),
    }

    out_path = DATA_DIR / "daily_analysis.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"{ts()} 💾 Saved to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{ts()} ❌ Error: {e}")
        traceback.print_exc()
