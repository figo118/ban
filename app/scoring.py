from app.indicators import atr, ema, rsi, zscore


def pct_change(klines: list[dict], bars: int) -> float:
    if len(klines) <= bars:
        return 0.0
    old = klines[-bars - 1]["close"]
    new = klines[-1]["close"]
    return (new / old - 1) * 100 if old else 0.0


def build_features(
    symbol: str,
    ticker: dict,
    k5: list[dict],
    k15: list[dict],
    k1h: list[dict],
    premium: dict,
    oi: dict,
    oi_hist: list[dict] | None = None,
    long_short: list[dict] | None = None,
    taker_ratio: list[dict] | None = None,
    market: dict | None = None,
) -> dict:
    closes15 = [k["close"] for k in k15]
    price = closes15[-1]
    ema20 = ema(closes15[-40:], 20)
    atr15 = atr(k15)
    distance_atr = (price - ema20) / atr15 if atr15 else 0.0
    taker_buy_volume = k15[-1].get("taker_buy_volume", 0)
    taker_buy_ratio = taker_buy_volume / k15[-1]["volume"] if k15[-1]["volume"] else 0.0
    oi_change = _oi_change(oi_hist or [])
    structure = detect_structure(k15)
    market = market or {"state": "neutral", "penalty": 0, "reason": "大盘环境中性"}
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
        "oi_change_15m": oi_change,
        "long_short_ratio": _latest_ratio(long_short or [], "long_short_ratio"),
        "taker_buy_ratio": _latest_ratio(taker_ratio or [], "buy_sell_ratio") or taker_buy_ratio,
        "structure_signal": structure["signal"],
        "structure_score": structure["score"],
        "structure_reason": structure["reason"],
        "market_state": market["state"],
        "market_penalty": market["penalty"],
        "market_reason": market["reason"],
        "last_high": max(k["high"] for k in k15[-8:]),
        "recent_low": min(k["low"] for k in k15[-8:]),
    }


def detect_structure(k15: list[dict]) -> dict:
    if len(k15) < 20:
        return {"signal": "none", "score": 0, "reason": "K线不足"}
    current = k15[-1]
    previous = k15[-2]
    prior_high = max(k["high"] for k in k15[-12:-2])
    prior_low = min(k["low"] for k in k15[-12:-2])
    body = abs(current["close"] - current["open"])
    candle_range = max(current["high"] - current["low"], 1e-12)
    upper_shadow_ratio = (current["high"] - max(current["open"], current["close"])) / candle_range

    if current["high"] > prior_high and current["close"] < prior_high:
        return {"signal": "failed_breakout", "score": 18, "reason": "假突破前高后跌回"}
    if current["close"] < prior_low and previous["close"] > prior_low:
        return {"signal": "support_break", "score": 16, "reason": "跌破近端结构支撑"}
    if upper_shadow_ratio > 0.45 and body / candle_range < 0.45:
        return {"signal": "upper_wick_stall", "score": 10, "reason": "高位长上影滞涨"}
    return {"signal": "none", "score": 0, "reason": "等待结构确认"}


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
    if features.get("oi_change_15m", 0) > 8:
        score += 8
        reasons.append("15m OI快速上升，杠杆资金拥挤")
    if features.get("long_short_ratio", 0) > 1.5:
        score += 5
        reasons.append("账户多空比偏多")
    if features.get("taker_buy_ratio", 0) < 0.9:
        score += 4
        reasons.append("主动买盘边际转弱")
    if features.get("structure_score", 0) > 0:
        score += features["structure_score"]
        reasons.append(features["structure_reason"])
    if features.get("market_penalty", 0) > 0:
        score -= features["market_penalty"]
        reasons.append(features["market_reason"])

    score = max(0, min(score, 100))
    level = 0
    if score >= 85 and features.get("structure_signal") in {"failed_breakout", "support_break"}:
        level = 3
    elif score >= 70:
        level = 2
    elif score >= 45:
        level = 1
    return score, level, reasons or ["未触发明显过热条件"]


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


def _oi_change(rows: list[dict]) -> float:
    if len(rows) < 2 or rows[0]["sum_open_interest"] == 0:
        return 0.0
    return (rows[-1]["sum_open_interest"] / rows[0]["sum_open_interest"] - 1) * 100


def _latest_ratio(rows: list[dict], key: str) -> float:
    return float(rows[-1][key]) if rows else 0.0
