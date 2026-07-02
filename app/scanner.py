import asyncio
from app.alerts import send_telegram
from app.binance import BinanceFuturesClient
from app.config import Settings
from app.db import SessionLocal
from app.market import classify_market
from app.models import Signal, Snapshot
from app.scoring import build_features, score_short, trade_plan


class Scanner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = BinanceFuturesClient(settings.binance_fapi_base_url)

    async def scan_once(self) -> list[dict]:
        tickers, market = await asyncio.gather(self.client.ticker_24h(), self._market_context())
        usdt = [t for t in tickers if t.get("symbol", "").endswith("USDT")]
        liquid = [t for t in usdt if float(t.get("quoteVolume", 0)) >= self.settings.min_quote_volume_24h]
        top = sorted(liquid, key=lambda t: float(t.get("priceChangePercent", 0)), reverse=True)[: self.settings.top_n]
        by_symbol = {t["symbol"]: t for t in usdt}
        symbols = list(dict.fromkeys([t["symbol"] for t in top] + self.settings.manual_symbol_list))
        results = await asyncio.gather(
            *(self._scan_symbol(s, by_symbol.get(s, {}), market) for s in symbols),
            return_exceptions=True,
        )
        return [r for r in results if isinstance(r, dict)]

    async def _market_context(self) -> dict:
        try:
            btc_15m, btc_1h, eth_1h = await asyncio.gather(
                self.client.klines("BTCUSDT", "15m"),
                self.client.klines("BTCUSDT", "1h"),
                self.client.klines("ETHUSDT", "1h"),
            )
            return classify_market(btc_15m, btc_1h, eth_1h)
        except Exception:
            return {"state": "neutral", "penalty": 0, "reason": "大盘数据获取失败，按中性处理"}

    async def _scan_symbol(self, symbol: str, ticker: dict, market: dict) -> dict:
        k5, k15, k1h, premium, oi, oi_hist, long_short, taker_ratio = await asyncio.gather(
            self.client.klines(symbol, "5m"),
            self.client.klines(symbol, "15m"),
            self.client.klines(symbol, "1h"),
            self.client.premium_index(symbol),
            self.client.open_interest(symbol),
            self._safe(self.client.open_interest_hist(symbol)),
            self._safe(self.client.global_long_short_ratio(symbol)),
            self._safe(self.client.taker_long_short_ratio(symbol)),
        )
        features = build_features(symbol, ticker, k5, k15, k1h, premium, oi, oi_hist, long_short, taker_ratio, market)
        score, level, reasons = score_short(features)
        plan = trade_plan(features)
        reason = "；".join(reasons)

        async with SessionLocal() as session:
            snapshot = Snapshot(score=score, level=level, reason=reason, **{k: features[k] for k in [
                "symbol", "price", "change_1h", "change_4h", "change_24h", "quote_volume_24h",
                "rsi_15m", "ema20_15m", "atr_15m", "volume_zscore", "funding_rate", "open_interest",
                "oi_change_15m", "long_short_ratio", "taker_buy_ratio", "structure_signal", "market_state",
            ]})
            session.add(snapshot)
            if level >= 3:
                signal = Signal(symbol=symbol, level=level, score=score, reason=reason, **plan)
                session.add(signal)
            await session.commit()

        if level >= 2:
            await send_telegram(self.settings, symbol, level, self._alert_text(features, score, level, reason, plan))
        return {**features, "score": score, "level": level, "reason": reason, **plan}

    async def _safe(self, coro):
        try:
            return await coro
        except Exception:
            return []

    def _alert_text(self, f: dict, score: float, level: int, reason: str, plan: dict) -> str:
        return (
            f"🚨 {f['symbol']} 高位开空监控 Level {level}\n"
            f"价格: {f['price']} 分数: {score:.1f}\n"
            f"1h/4h/24h: {f['change_1h']:.2f}% / {f['change_4h']:.2f}% / {f['change_24h']:.2f}%\n"
            f"RSI15m: {f['rsi_15m']:.1f} Funding: {f['funding_rate']:.4%} OI15m: {f['oi_change_15m']:.2f}%\n"
            f"结构: {f['structure_signal']} 大盘: {f['market_state']}\n"
            f"原因: {reason}\n"
            f"参考计划: 入场 {plan['entry_min']}~{plan['entry_max']} 止损 {plan['stop_loss']} TP {plan['take_profit_1']}/{plan['take_profit_2']}"
        )
