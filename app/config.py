from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./monitor.db"
    binance_fapi_base_url: str = "https://fapi.binance.com"
    scan_interval_seconds: int = 30
    top_n: int = 10
    manual_symbols: str = ""
    min_quote_volume_24h: float = 50_000_000
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def manual_symbol_list(self) -> list[str]:
        return [s.strip().upper() for s in self.manual_symbols.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
