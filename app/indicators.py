from statistics import mean


def ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    k = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = value * k + result * (1 - k)
    return result


def rsi(values: list[float], period: int = 14) -> float:
    if len(values) <= period:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(values[-period - 1 : -1], values[-period:]):
        delta = current - previous
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(klines: list[dict], period: int = 14) -> float:
    if len(klines) < 2:
        return 0.0
    true_ranges: list[float] = []
    for previous, current in zip(klines[-period - 1 : -1], klines[-period:]):
        high = current["high"]
        low = current["low"]
        previous_close = previous["close"]
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return mean(true_ranges) if true_ranges else 0.0


def zscore(values: list[float]) -> float:
    if len(values) < 3:
        return 0.0
    sample = values[:-1]
    avg = mean(sample)
    variance = mean([(value - avg) ** 2 for value in sample])
    std = variance**0.5
    return 0.0 if std == 0 else (values[-1] - avg) / std
