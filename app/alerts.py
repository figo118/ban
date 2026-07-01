from datetime import datetime, timedelta
import httpx
from app.config import Settings

_last_alert: dict[str, datetime] = {}


async def send_telegram(settings: Settings, symbol: str, level: int, text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    key = f"{symbol}:{level}"
    now = datetime.utcnow()
    if key in _last_alert and now - _last_alert[key] < timedelta(minutes=15):
        return
    _last_alert[key] = now
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": settings.telegram_chat_id, "text": text})
