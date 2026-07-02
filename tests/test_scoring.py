from app.market import classify_market
from app.scoring import detect_structure, score_short, trade_plan


def test_score_short_detects_confirmed_overheat():
    features = {
        "change_24h": 20,
        "change_1h": 10,
        "change_4h": 18,
        "distance_atr": 3,
        "rsi_15m": 85,
        "volume_zscore": 3,
        "funding_rate": 0.0005,
        "oi_change_15m": 12,
        "long_short_ratio": 1.8,
        "taker_buy_ratio": 0.8,
        "structure_score": 18,
        "structure_signal": "failed_breakout",
        "structure_reason": "假突破前高后跌回",
        "market_penalty": 0,
    }
    score, level, reasons = score_short(features)
    assert score >= 85
    assert level == 3
    assert "假突破前高后跌回" in reasons


def test_risk_on_market_downgrades_score():
    base = {
        "change_24h": 20,
        "change_1h": 10,
        "change_4h": 18,
        "distance_atr": 3,
        "rsi_15m": 85,
        "volume_zscore": 3,
        "funding_rate": 0.0005,
        "oi_change_15m": 12,
        "long_short_ratio": 1.8,
        "taker_buy_ratio": 0.8,
        "structure_score": 18,
        "structure_signal": "failed_breakout",
        "structure_reason": "假突破前高后跌回",
    }
    score_neutral, _, _ = score_short({**base, "market_penalty": 0})
    score_risk_on, _, _ = score_short({**base, "market_penalty": 18, "market_reason": "BTC/ETH同步强势"})
    assert score_risk_on < score_neutral


def test_detect_structure_failed_breakout():
    klines = [{"open": 10, "high": 11, "low": 9, "close": 10, "quote_volume": 100} for _ in range(20)]
    klines[-3]["high"] = 12
    klines[-1] = {"open": 11.9, "high": 12.5, "low": 11.2, "close": 11.8, "quote_volume": 300}
    structure = detect_structure(klines)
    assert structure["signal"] == "failed_breakout"


def test_trade_plan_uses_structure_levels():
    plan = trade_plan({"price": 100, "atr_15m": 2, "recent_low": 96, "last_high": 105, "ema20_15m": 98})
    assert plan["stop_loss"] == 106
    assert plan["take_profit_1"] == 98


def test_classify_market_risk_on():
    btc_15m = [{"close": 100 + i} for i in range(100)]
    btc_1h = [{"close": 100 + i} for i in range(20)]
    eth_1h = [{"close": 100 + i} for i in range(20)]
    market = classify_market(btc_15m, btc_1h, eth_1h)
    assert market["state"] == "risk_on_breakout"
    assert market["penalty"] > 0
