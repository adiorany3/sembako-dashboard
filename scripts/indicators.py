#!/usr/bin/env python3
"""
Technical Indicators Library
============================
Shared calculations for Market Analysis.
All functions operate on lists of numbers. No external deps.
"""
import math
from datetime import datetime, timedelta
from collections import OrderedDict


# ════════════════════════════════════════════
# 1. BASIC INDICATORS
# ════════════════════════════════════════════

def moving_average(data, period):
    """Simple Moving Average. Returns list (same length, first period-1 are None)."""
    if len(data) < period:
        return [None] * len(data)
    result = [None] * (period - 1)
    for i in range(period - 1, len(data)):
        avg = sum(data[i - period + 1:i + 1]) / period
        result.append(round(avg, 2))
    return result


def ema(data, period):
    """Exponential Moving Average."""
    if len(data) < period:
        return [None] * len(data)
    k = 2 / (period + 1)
    result = [None] * (period - 1)
    result.append(sum(data[:period]) / period)
    for i in range(period, len(data)):
        val = data[i] * k + result[-1] * (1 - k)
        result.append(round(val, 2))
    return result


def rate_of_change(data, period=5):
    """Percentage change over N periods."""
    if len(data) <= period:
        return [None] * len(data)
    result = [None] * period
    for i in range(period, len(data)):
        if data[i - period] > 0:
            roc = ((data[i] - data[i - period]) / data[i - period]) * 100
            result.append(round(roc, 2))
        else:
            result.append(None)
    return result


def volatility(data, period=10):
    """Standard deviation of returns over period."""
    if len(data) < period + 1:
        return [None] * len(data)
    returns = []
    for i in range(1, len(data)):
        if data[i - 1] > 0:
            returns.append((data[i] - data[i - 1]) / data[i - 1])
        else:
            returns.append(0)
    result = [None] * period
    for i in range(period, len(returns)):
        window = returns[i - period:i]
        mean = sum(window) / len(window)
        var = sum((r - mean) ** 2 for r in window) / len(window)
        result.append(round(math.sqrt(var) * 100, 3))
    return result


# ════════════════════════════════════════════
# 2. SUPPORT & RESISTANCE
# ════════════════════════════════════════════

def find_support_resistance(data, lookback=None):
    """Find support/resistance levels via swing points."""
    if len(data) < 5:
        return {"support": [], "resistance": [], "current": data[-1] if data else 0}
    lb = min(lookback or len(data), len(data))
    window = data[-lb:]
    current = window[-1]
    supports = []
    resistances = []
    for i in range(2, len(window) - 2):
        if window[i] <= window[i-1] and window[i] <= window[i+1] and \
           window[i] <= window[i-2] and window[i] <= window[i+2]:
            supports.append(window[i])
        if window[i] >= window[i-1] and window[i] >= window[i+1] and \
           window[i] >= window[i-2] and window[i] >= window[i+2]:
            resistances.append(window[i])

    def cluster(levels, threshold_pct=0.02):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for lv in levels[1:]:
            if (lv - clusters[-1][-1]) / max(clusters[-1][-1], 1) < threshold_pct:
                clusters[-1].append(lv)
            else:
                clusters.append([lv])
        return [round(sum(c) / len(c), 2) for c in clusters]

    supports = cluster(supports)
    resistances = cluster(resistances)
    supports = sorted([s for s in supports if s < current], reverse=True)[:3]
    resistances = sorted([r for r in resistances if r > current])[:3]
    return {"support": supports, "resistance": resistances, "current": current}


# ════════════════════════════════════════════
# 3. TREND ANALYSIS
# ════════════════════════════════════════════

def trend_direction(data, short=5, long=20):
    """Trend via MA crossover."""
    ma_s = moving_average(data, short)
    ma_l = moving_average(data, long)
    if not ma_s[-1] or not ma_l[-1]:
        return "insufficient_data"
    diff_pct = (ma_s[-1] - ma_l[-1]) / ma_l[-1] * 100
    if diff_pct > 2:
        return "uptrend"
    elif diff_pct < -2:
        return "downtrend"
    else:
        return "sideways"


def momentum_score(data, period=10):
    """Momentum score: -100 to +100."""
    if len(data) < period + 1:
        return 0
    roc = rate_of_change(data, period)
    ma5 = moving_average(data, 5)
    score = 0
    if roc[-1] is not None:
        score += max(-40, min(40, roc[-1] * 4))
    if ma5[-1] is not None:
        if data[-1] > ma5[-1]:
            score += 30
        else:
            score -= 30
    td = trend_direction(data, 5, min(20, len(data) - 1))
    if td == "uptrend":
        score += 30
    elif td == "downtrend":
        score -= 30
    return max(-100, min(100, round(score)))


# ════════════════════════════════════════════
# 4. ANOMALY DETECTION
# ════════════════════════════════════════════

def detect_anomalies(data, names=None, threshold_pct=5):
    """Detect price movements > threshold_pct."""
    if len(data) < 2:
        return []
    anomalies = []
    for i in range(1, len(data)):
        if data[i - 1] > 0:
            chg = ((data[i] - data[i - 1]) / data[i - 1]) * 100
        else:
            continue
        name = names[i] if names and i < len(names) else f"Day {i}"
        if abs(chg) > threshold_pct:
            anomalies.append({
                "name": name, "from": data[i - 1], "to": data[i],
                "change_pct": round(chg, 2),
                "type": "spike" if chg > 0 else "crash"
            })
    return anomalies


# ════════════════════════════════════════════
# 5. CORRELATION
# ════════════════════════════════════════════

def pearson_correlation(x, y):
    """Pearson correlation. Returns -1 to +1."""
    n = min(len(x), len(y))
    if n < 3:
        return None
    x, y = x[-n:], y[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if dx == 0 or dy == 0:
        return 0
    return round(num / (dx * dy), 3)


# ════════════════════════════════════════════
# 5b. MULTI-PERIOD TREND + % CHANGE
# ════════════════════════════════════════════

def multi_period_trend(data, periods=(3, 7, 14)):
    """Trend direction per period (3, 7, 14 days)."""
    if not data or len(data) < 2:
        return {}
    current = data[-1]
    result = {}
    for p in periods:
        if len(data) > p:
            baseline = data[-(p+1)]
            change_pct = round((current - baseline) / baseline * 100, 2) if baseline > 0 else 0
            if change_pct > 2:
                direction = "uptrend"
            elif change_pct < -2:
                direction = "downtrend"
            else:
                direction = "sideways"
            result[p] = {"direction": direction, "change_pct": change_pct,
                         "baseline": baseline, "current": current}
        else:
            result[p] = {"direction": "insufficient_data", "change_pct": 0,
                         "baseline": 0, "current": current}
    return result


def price_forecast(data, horizon=7, alpha=0.3):
    """Exponential smoothing forecast for N days ahead."""
    if not data or len(data) < 5:
        return []
    level = data[0]
    trend_val = data[1] - data[0] if len(data) > 1 else 0
    for i in range(1, len(data)):
        prev_level = level
        level = alpha * data[i] + (1 - alpha) * (level + trend_val)
        trend_val = alpha * (level - prev_level) + (1 - alpha) * trend_val
    return [round(level + trend_val * h, 2) for h in range(1, horizon + 1)]


def change_from_baseline(data, baselines=(1, 7, 14, 30)):
    """% change from various baselines."""
    if not data or len(data) < 2:
        return {}
    current = data[-1]
    result = {}
    for b in baselines:
        if len(data) > b:
            base_val = data[-(b+1)]
            result[b] = round((current - base_val) / base_val * 100, 2) if base_val > 0 else None
        else:
            result[b] = None
    return result


def enhanced_confidence(data, trend=None, volatility_val=None, forecast=None):
    """Enhanced confidence score 1-5."""
    if not data or len(data) < 3:
        return 1
    score = 0
    if len(data) >= 10:
        score += 1
    if len(data) >= 30:
        score += 1
    if trend and trend not in ("insufficient_data", "sideways"):
        score += 1.5
    elif trend == "sideways":
        score += 0.5
    if volatility_val is not None:
        if volatility_val < 3:
            score += 1.0
        elif volatility_val < 5:
            score += 0.5
    if forecast and len(forecast) >= 7:
        score += 0.5
    return min(5, max(1, round(score)))


# ════════════════════════════════════════════
# 5c. CORRELATION MATRIX
# ════════════════════════════════════════════

def correlation_matrix(series_dict):
    """Compute correlation matrix for multiple time series."""
    names = list(series_dict.keys())
    matrix = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            corr = pearson_correlation(series_dict[names[i]], series_dict[names[j]])
            if corr is not None:
                matrix[(names[i], names[j])] = corr
    return matrix


# ════════════════════════════════════════════
# 6. CONFIDENCE SCORING
# ════════════════════════════════════════════

def confidence_score(data_length, trend_agreement=True, volume_stable=True,
                     correlation_support=True):
    """Confidence score 1-5 based on data quality."""
    score = 1
    if data_length >= 30:
        score += 1
    if data_length >= 60:
        score += 1
    if trend_agreement:
        score += 0.5
    if volume_stable:
        score += 0.5
    if correlation_support:
        score += 0.5
    return min(5, max(1, round(score)))


# ════════════════════════════════════════════
# 7. SEASONAL PATTERNS
# ════════════════════════════════════════════

SEASONAL_PATTERNS = {
    "ramadan_prep": {"months": [3, 4], "effect": "sembako naik 5-15%", "impact": "high"},
    "harvest": {"months": [5, 6, 7], "effect": "komoditas pertanian turun", "impact": "medium"},
    "year_end": {"months": [11, 12], "effect": "konsumsi naik, inflasi naik", "impact": "medium"},
    "new_year": {"months": [1], "effect": "daya beli menurun pasca libur", "impact": "low"},
    "school_start": {"months": [7], "effect": "pengeluaran keluarga naik", "impact": "low"},
}


def get_seasonal_context(date=None):
    """Return relevant seasonal patterns for given date."""
    dt = date or datetime.now()
    month = dt.month
    active = []
    for key, pat in SEASONAL_PATTERNS.items():
        if month in pat["months"]:
            active.append({"pattern": key, **pat})
    if month in [2, 3, 4]:
        active.append({
            "pattern": "ramadan", "months": [2, 3, 4],
            "effect": "Harga sembako cenderung naik (telur, daging, beras)",
            "impact": "high"
        })
    return active


# ════════════════════════════════════════════
# 8. MACRO ECONOMIC INDICATORS
# ════════════════════════════════════════════

def real_interest_rate(bi_rate, inflation_yoy):
    """Real Interest Rate = BI Rate - Inflation."""
    if bi_rate is None or inflation_yoy is None:
        return None
    val = round(bi_rate - inflation_yoy, 2)
    if val > 2:
        interp = "Ketat — restriktif, jaga inflasi tapi tekan investasi"
        signal = "hawkish"
    elif val > 0:
        interp = "Positif — policy sehat"
        signal = "neutral"
    elif val > -1:
        interp = "Negatif ringan — inflasi mulai menggerus daya beli"
        signal = "dovish"
    else:
        interp = "Negatif dalam — terlalu longgar, risiko inflasi"
        signal = "danger"
    return {"value": val, "interpretation": interp, "signal": signal}


def currency_pressure_index(usd_idr_series):
    """Currency Pressure Index (0-100) from USD/IDR trend + volatility."""
    if not usd_idr_series or len(usd_idr_series) < 5:
        return None
    chg_5d = (usd_idr_series[-1] - usd_idr_series[-5]) / usd_idr_series[-5] * 100
    trend_score = min(50, max(0, 25 + chg_5d * 5))
    returns = [
        (usd_idr_series[i] - usd_idr_series[i-1]) / usd_idr_series[i-1]
        for i in range(max(1, len(usd_idr_series)-10), len(usd_idr_series))
    ]
    if returns:
        mean_r = sum(returns) / len(returns)
        vol = (sum((r - mean_r)**2 for r in returns) / len(returns))**0.5 * 100
    else:
        vol = 0
    score = round(trend_score + min(50, max(0, vol * 10)))
    if score > 75:
        signal, desc = "danger", "KRITIS — tekanan pelemahan IDR sangat kuat"
    elif score > 50:
        signal, desc = "warning", "WASPADA — IDR melemah, potensi capital outflow"
    elif score > 25:
        signal, desc = "cautious", "Sedikit tekanan, cukup stabil"
    else:
        signal, desc = "stable", "Stabil — tidak ada tekanan signifikan"
    return {"score": score, "trend_5d_pct": round(chg_5d, 2), "volatility": round(vol, 3),
            "signal": signal, "interpretation": desc}


def import_cost_pressure(oil_price, usd_idr):
    """Import Cost Pressure = Oil x USD/IDR proxy for energy import costs."""
    if oil_price is None or usd_idr is None:
        return None
    cost = oil_price * usd_idr
    ratio = cost / (80 * 15500)
    if ratio > 1.15:
        signal, interp = "danger", "TEKANAN TINGGI — biaya impor energi melonjak"
    elif ratio > 1.05:
        signal, interp = "warning", "Di atas normal — biaya impor naik"
    elif ratio > 0.95:
        signal, interp = "neutral", "Normal — biaya impor stabil"
    else:
        signal, interp = "favorable", "Di bawah normal — biaya impor murah"
    return {"cost_index": round(cost), "ratio_vs_baseline": round(ratio, 3),
            "signal": signal, "interpretation": interp}


def food_inflation_proxy(sembako_series):
    """Food Inflation Proxy — sembako basket 30d vs 7d rate of change."""
    if not sembako_series or len(sembako_series) < 5:
        return None
    current = sembako_series[-1]
    base_30 = sembako_series[-30] if len(sembako_series) > 30 else sembako_series[0]
    base_7 = sembako_series[-7] if len(sembako_series) > 7 else sembako_series[0]
    chg_30d = round((current - base_30) / base_30 * 100, 2) if base_30 > 0 else 0
    chg_7d = round((current - base_7) / base_7 * 100, 2) if base_7 > 0 else 0
    if chg_30d > 5:
        signal = "high_inflation"
        interp = "Inflasi pangan TINGGI — daya beli tergerus"
    elif chg_30d > 2:
        signal = "moderate"
        interp = "Inflasi pangan moderat"
    elif chg_30d > -2:
        signal = "stable"
        interp = "Harga pangan stabil"
    else:
        signal = "deflation"
        interp = "Harga pangan turun — buruk untuk petani"
    return {"change_30d": chg_30d, "change_7d": chg_7d, "signal": signal, "interpretation": interp}


def stagflation_risk(bi_rate, inflation_yoy, ihsg_trend, food_signal):
    """Stagflation Risk Score (0-100)."""
    score = 0
    factors = []
    if bi_rate is not None and inflation_yoy is not None:
        real = bi_rate - inflation_yoy
        if real < -1:
            score += 25
            factors.append(f"Real rate negatif ({real:+.1f}%)")
        elif real < 0:
            score += 10
            factors.append(f"Real rate mendekati nol ({real:+.1f}%)")
    if inflation_yoy is not None:
        if inflation_yoy > 4:
            score += 25
            factors.append(f"Inflasi tinggi ({inflation_yoy}%)")
        elif inflation_yoy > 3:
            score += 10
            factors.append(f"Inflasi moderat ({inflation_yoy}%)")
    if ihsg_trend == "downtrend":
        score += 25
        factors.append("IHSG downtrend")
    elif ihsg_trend == "sideways":
        score += 5
    if food_signal == "high_inflation":
        score += 25
        factors.append("Inflasi pangan tinggi")
    elif food_signal == "moderate":
        score += 10
    score = min(100, score)
    if score > 60:
        signal, interp = "high_risk", "RISIKO STAGFLASI TINGGI"
    elif score > 35:
        signal, interp = "moderate", "RISIKO STAGFLASI MODERAT"
    elif score > 15:
        signal, interp = "low", "Risiko stagflasi rendah"
    else:
        signal, interp = "minimal", "Ekonomi sehat"
    return {"score": score, "factors": factors, "signal": signal, "interpretation": interp}


def risk_on_off_index(btc_chg, gold_chg, ihsg_chg):
    """Risk-On/Off Index (-100 to +100)."""
    vals = []
    if btc_chg is not None:
        vals.append(("BTC", btc_chg, 0.4))
    if gold_chg is not None:
        vals.append(("Gold", -gold_chg, 0.3))
    if ihsg_chg is not None:
        vals.append(("IHSG", ihsg_chg, 0.3))
    if not vals:
        return None
    total_w = sum(w for _, _, w in vals)
    score = round(max(-100, min(100, sum(v * w for _, v, w in vals) / total_w * 10)))
    if score > 50:
        signal, interp = "risk_on", "Risk-On — pasar agresif, cari yield tinggi"
    elif score > 10:
        signal, interp = "mild_on", "Risk-On ringan"
    elif score > -10:
        signal, interp = "neutral", "Netral — hati-hati"
    elif score > -50:
        signal, interp = "mild_off", "Risk-Off ringan — defensive"
    else:
        signal, interp = "risk_off", "Risk-Off KUAT — kejar safe haven"
    return {"score": score, "signal": signal, "interpretation": interp}


def commodity_terms_of_trade(cpo_myr, oil_usd):
    """Commodity Terms of Trade — CPO/Oil ratio. Higher = Indonesia benefits."""
    if cpo_myr is None or oil_usd is None or oil_usd == 0:
        return None
    cpo_usd = cpo_myr * 0.22
    ratio = cpo_usd / oil_usd
    pct = (ratio - 5.5) / 5.5 * 100
    if pct > 15:
        signal = "favorable"
        interp = "SANGAT MENGUNTUNGKAN — surplus neraca berjalan"
    elif pct > 5:
        signal = "positive"
        interp = "Menguntungkan — ekspor sawit lebih bernilai"
    elif pct > -5:
        signal = "neutral"
        interp = "Netral — terms of trade stabil"
    elif pct > -15:
        signal = "warning"
        interp = "Kurang menguntungkan — tekanan neraca"
    else:
        signal = "danger"
        interp = "MERUGIKAN — biaya impor jauh lebih tinggi"
    return {"ratio": round(ratio, 2), "cpo_usd_ton": round(cpo_usd),
            "pct_vs_baseline": round(pct, 1), "signal": signal, "interpretation": interp}


# ════════════════════════════════════════════
# 9. FULL ANALYSIS BUILDER
# ════════════════════════════════════════════

def full_analysis(name, values, dates=None):
    """Run all indicators on a single series."""
    if not values or len(values) < 2:
        return {"name": name, "error": "insufficient_data"}
    current = values[-1]
    prev = values[-2] if len(values) > 1 else current
    change_pct = round((current - prev) / prev * 100, 2) if prev > 0 else 0
    result = {
        "name": name, "current": current, "previous": prev,
        "change_pct": change_pct, "data_points": len(values),
    }
    ma5 = moving_average(values, 5)
    ma10 = moving_average(values, 10)
    ma20 = moving_average(values, 20) if len(values) >= 20 else None
    result["ma5"] = ma5[-1] if ma5[-1] else None
    result["ma10"] = ma10[-1] if ma10[-1] else None
    result["ma20"] = ma20[-1] if ma20 and ma20[-1] else None
    result["trend"] = trend_direction(values, 5, min(20, len(values) - 1))
    result["momentum"] = momentum_score(values)
    vol = volatility(values, min(10, len(values) - 1))
    result["volatility"] = vol[-1] if vol[-1] else None
    roc = rate_of_change(values, min(5, len(values) - 1))
    result["roc_5d"] = roc[-1] if roc[-1] else None
    sr = find_support_resistance(values)
    result["support"] = sr["support"]
    result["resistance"] = sr["resistance"]
    result["confidence"] = confidence_score(
        len(values),
        trend_agreement=(result["trend"] != "insufficient_data"),
        volume_stable=(result["volatility"] is not None and result["volatility"] < 5),
    )
    return result
