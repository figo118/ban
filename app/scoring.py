from app.indicators import atr, ema, rsi, zscore


def pct_change(klines: list[dict], bars: int) -> float:
    if len(klines) <= bars:
        return 0.0
    old = klines[-bars - 1]["close"]
    new = klines[-1]["close"]
    return (new / old - 1) * 100 if old else 0.0


def build_features(symbol: str, ticker: dict, k5: list[dict], k15: list[dict], k1h: list[dict], premium: dict, oi: dict) -> dict:
    closes15 = [k["close"] for k in k15]
    price = closes15[-1]
    ema20 = ema(closes15[-40:], 20)
    atr15 = atr(k15)
    distance_atr = (price - ema20) / atr15 if atr15 else 0.0
    return {
        "symbol": symbol,
        "price": price,
        "change_1h": pct_change(k5, 12),
        "change_4h": pct_change(k15, 16),
        "change_24h": float(ticker.get("priceChangePercent", 0)),
        "quote_volume_24h": float(ticker.get("quoteVolume", 0)),
        "rsi_15m": rsi(closes15),
        "ema20_15m": ema20,
        "atr_15m": atr15,
        "distance_atr": distance_atr,
        "volume_zscore": zscore([k["quote_volume"] for k in k15[-49:]]),
        "funding_rate": float(premium.get("lastFundingRate", 0) or 0),
        "open_interest": float(oi.get("openInterest", 0) or 0),
        "last_high": max(k["high"] for k in k15[-8:]),
        "recent_low": min(k["low"] for k in k15[-8:]),
    }


def score_short(features: dict) -> tuple[float, int, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if features["change_24h"] > 30:
        score += 18
        reasons.append("24h涨幅超过30%")
    elif features["change_24h"] > 15:
        score += 10
        reasons.append("24h涨幅超过15%")
    if features["change_1h"] > 8:
        score += 12
        reasons.append("1h短线急涨")
    if features["change_4h"] > 15:
        score += 12
        reasons.append("4h涨幅过热")
    if features["distance_atr"] > 2.5:
        score += 15
        reasons.append("价格显著偏离15m EMA20")
    if features["rsi_15m"] > 80:
        score += 15
        reasons.append("15m RSI极度超买")
    elif features["rsi_15m"] > 72:
        score += 9
        reasons.append("15m RSI超买")
    if features["volume_zscore"] > 2:
        score += 10
        reasons.append("成交量异常放大")
    if features["funding_rate"] > 0.0003:
        score += 8
        reasons.append("资金费率偏高")

    level = 0
    if score >= 85:
        level = 3
    elif score >= 70:
        level = 2
    elif score >= 45:
        level = 1
    return min(score, 100), level, reasons or ["未触发明显过热条件"]


def trade_plan(features: dict) -> dict:
    price = features["price"]
    atr15 = features["atr_15m"] or price * 0.01
    return {
        "entry_min": round(max(features["recent_low"], price - 0.5 * atr15), 8),
        "entry_max": round(price + 0.2 * atr15, 8),
        "stop_loss": round(features["last_high"] + 0.5 * atr15, 8),
        "take_profit_1": round(features["ema20_15m"], 8),
        "take_profit_2": round(price - 2 * atr15, 8),
    }
