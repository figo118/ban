from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config import get_settings
from app.models import Base

settings = get_settings()
engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_missing_snapshot_columns)


def _add_missing_snapshot_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if "snapshots" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("snapshots")}
    columns = {
        "oi_change_15m": "FLOAT DEFAULT 0",
        "long_short_ratio": "FLOAT DEFAULT 0",
        "taker_buy_ratio": "FLOAT DEFAULT 0",
        "structure_signal": "VARCHAR(64) DEFAULT 'none'",
        "market_state": "VARCHAR(64) DEFAULT 'neutral'",
    }
    for name, definition in columns.items():
        if name not in existing:
            sync_conn.execute(text(f"ALTER TABLE snapshots ADD COLUMN {name} {definition}"))
