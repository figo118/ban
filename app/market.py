from app.indicators import ema


def classify_market(btc_15m: list[dict], btc_1h: list[dict], eth_1h: list[dict]) -> dict:
    btc_15_closes = [k["close"] for k in btc_15m]
    btc_1h_closes = [k["close"] for k in btc_1h]
    eth_1h_closes = [k["close"] for k in eth_1h]
    btc_1h_change = _pct_change(btc_1h_closes, 4)
    eth_1h_change = _pct_change(eth_1h_closes, 4)
    btc_above_stack = btc_15_closes[-1] > ema(btc_15_closes[-40:], 20) > ema(btc_15_closes[-80:], 50)

    if btc_above_stack and btc_1h_change > 1.2 and eth_1h_change > 1.0:
        return {"state": "risk_on_breakout", "penalty": 18, "reason": "BTC/ETH同步强势，逆势做空降级"}
    if btc_1h_change < -0.8 and eth_1h_change < -0.6:
        return {"state": "risk_off", "penalty": 0, "reason": "BTC/ETH回落，做空环境较友好"}
    return {"state": "neutral", "penalty": 0, "reason": "大盘环境中性"}


def _pct_change(values: list[float], bars: int) -> float:
    if len(values) <= bars or values[-bars - 1] == 0:
        return 0.0
    return (values[-1] / values[-bars - 1] - 1) * 100
