from app.scoring import score_short, trade_plan


def test_score_short_detects_overheat():
    features = {"change_24h": 40, "change_1h": 10, "change_4h": 18, "distance_atr": 3, "rsi_15m": 85, "volume_zscore": 3, "funding_rate": 0.0005}
    score, level, reasons = score_short(features)
    assert score >= 85
    assert level == 3
    assert reasons


def test_trade_plan_uses_structure_levels():
    plan = trade_plan({"price": 100, "atr_15m": 2, "recent_low": 96, "last_high": 105, "ema20_15m": 98})
    assert plan["stop_loss"] == 106
    assert plan["take_profit_1"] == 98
