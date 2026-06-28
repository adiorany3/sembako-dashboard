#!/usr/bin/env python3
"""
Technical Indicators Library
=============================
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
    """
    Find support and resistance levels using swing points.
    Returns dict: {support: [levels], resistance: [levels], current: price}
    """
    if len(data) < 5:
        return {"support": [], "resistance": [], "current": data[-1] if data else 0}

    lb = min(lookback or len(data), len(data))
    window = data[-lb:]
    current = window[-1]

    # Find local minima (support) and maxima (resistance)
    supports = []
    resistances = []

    for i in range(2, len(window) - 2):
        if window[i] <= window[i-1] and window[i] <= window[i+1] and \
           window[i] <= window[i-2] and window[i] <= window[i+2]:
            supports.append(window[i])
        if window[i] >= window[i-1] and window[i] >= window[i+1] and \
           window[i] >= window[i-2] and window[i] >= window[i+2]:
            resistances.append(window[i])

    # Cluster nearby levels (within 2%)
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

    # Keep only levels below/above current price
    supports = sorted([s for s in supports if s < current], reverse=True)[:3]
    resistances = sorted([r for r in resistances if r > current])[:3]

    return {
        "support": supports,
        "resistance": resistances,
        "current": current
    }


# ════════════════════════════════════════════
# 3. TREND ANALYSIS
# ════════════════════════════════════════════

def trend_direction(data, short=5, long=20):
    """
    Trend via MA crossover.
    Returns: 'uptrend', 'downtrend', 'sideways', or 'insufficient_data'
    """
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
    """
    Momentum score: -100 to +100.
    Based on ROC + MA position.
    """
    if len(data) < period + 1:
        return 0

    roc = rate_of_change(data, period)
    ma5 = moving_average(data, 5)

    score = 0

    # ROC component (±40)
    if roc[-1] is not None:
        score += max(-40, min(40, roc[-1] * 4))

    # MA position (±30)
    if ma5[-1] is not None:
        if data[-1] > ma5[-1]:
            score += 30
        else:
            score -= 30

    # Trend direction (±30)
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
    """
    Detect price movements > threshold_pct.
    Returns list of {name, change_pct, type: 'spike'|'crash'}
    """
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
                "name": name,
                "from": data[i - 1],
                "to": data[i],
                "change_pct": round(chg, 2),
                "type": "spike" if chg > 0 else "crash"
            })

    return anomalies


# ════════════════════════════════════════════
# 5. CORRELATION
# ════════════════════════════════════════════

def pearson_correlation(x, y):
    """Pearson correlation between two lists. Returns -1 to +1."""
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


def correlation_matrix(series_dict):
    """
    Compute correlation matrix for multiple time series.
    Input: {name: [values]}
    Returns: {(name1, name2): correlation}
    """
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
    """
    Confidence score 1-5 based on data quality factors.
    """
    score = 1  # base

    # Data depth
    if data_length >= 30: score += 1
    if data_length >= 60: score += 1

    # Trend agreement
    if trend_agreement: score += 0.5

    # Volatility
    if volume_stable: score += 0.5

    # Correlation support
    if correlation_support: score += 0.5

    return min(5, max(1, round(score)))


# ════════════════════════════════════════════
# 7. SEASONAL PATTERNS
# ════════════════════════════════════════════

# Known Indonesian economic calendar patterns
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

    # Ramadhan estimation (Islamic calendar ~11 days earlier each year)
    # Approximate for 2026: Ramadan ~Feb-Mar
    if month in [2, 3, 4]:
        active.append({
            "pattern": "ramadan",
            "months": [2, 3, 4],
            "effect": "Harga sembako cenderung naik (telur, daging, beras)",
            "impact": "high"
        })

    return active


# ════════════════════════════════════════════
# 8. COMPREHENSIVE ANALYSIS BUILDER
# ════════════════════════════════════════════

def full_analysis(name, values, dates=None):
    """
    Run all indicators on a single series.
    Returns comprehensive dict.
    """
    if not values or len(values) < 2:
        return {"name": name, "error": "insufficient_data"}

    current = values[-1]
    prev = values[-2] if len(values) > 1 else current
    change_pct = round((current - prev) / prev * 100, 2) if prev > 0 else 0

    result = {
        "name": name,
        "current": current,
        "previous": prev,
        "change_pct": change_pct,
        "data_points": len(values),
    }

    # Moving averages
    ma5 = moving_average(values, 5)
    ma10 = moving_average(values, 10)
    ma20 = moving_average(values, 20) if len(values) >= 20 else None

    result["ma5"] = ma5[-1] if ma5[-1] else None
    result["ma10"] = ma10[-1] if ma10[-1] else None
    result["ma20"] = ma20[-1] if ma20 and ma20[-1] else None

    # Trend
    result["trend"] = trend_direction(values, 5, min(20, len(values) - 1))

    # Momentum
    result["momentum"] = momentum_score(values)

    # Volatility
    vol = volatility(values, min(10, len(values) - 1))
    result["volatility"] = vol[-1] if vol[-1] else None

    # Rate of change
    roc = rate_of_change(values, min(5, len(values) - 1))
    result["roc_5d"] = roc[-1] if roc[-1] else None

    # Support/Resistance
    sr = find_support_resistance(values)
    result["support"] = sr["support"]
    result["resistance"] = sr["resistance"]

    # Confidence
    result["confidence"] = confidence_score(
        len(values),
        trend_agreement=(result["trend"] != "insufficient_data"),
        volume_stable=(result["volatility"] is not None and result["volatility"] < 5),
    )

    return result
