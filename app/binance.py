import httpx


class BinanceFuturesClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    async def ticker_24h(self) -> list[dict]:
        return await self._get("/fapi/v1/ticker/24hr")

    async def klines(self, symbol: str, interval: str, limit: int = 120) -> list[dict]:
        rows = await self._get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        return [
            {
                "open_time": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "quote_volume": float(row[7]),
                "taker_buy_volume": float(row[9]),
            }
            for row in rows
        ]

    async def premium_index(self, symbol: str) -> dict:
        return await self._get("/fapi/v1/premiumIndex", {"symbol": symbol})

    async def open_interest(self, symbol: str) -> dict:
        return await self._get("/fapi/v1/openInterest", {"symbol": symbol})

    async def open_interest_hist(self, symbol: str, period: str = "15m", limit: int = 8) -> list[dict]:
        rows = await self._get(
            "/futures/data/openInterestHist",
            {"symbol": symbol, "period": period, "limit": limit},
        )
        return [{"sum_open_interest": float(row["sumOpenInterest"]), "timestamp": row["timestamp"]} for row in rows]

    async def global_long_short_ratio(self, symbol: str, period: str = "15m", limit: int = 4) -> list[dict]:
        rows = await self._get(
            "/futures/data/globalLongShortAccountRatio",
            {"symbol": symbol, "period": period, "limit": limit},
        )
        return [{"long_short_ratio": float(row["longShortRatio"]), "timestamp": row["timestamp"]} for row in rows]

    async def taker_long_short_ratio(self, symbol: str, period: str = "15m", limit: int = 4) -> list[dict]:
        rows = await self._get(
            "/futures/data/takerlongshortRatio",
            {"symbol": symbol, "period": period, "limit": limit},
        )
        return [
            {
                "buy_sell_ratio": float(row["buySellRatio"]),
                "buy_vol": float(row["buyVol"]),
                "sell_vol": float(row["sellVol"]),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
