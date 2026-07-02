from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    price: Mapped[float] = mapped_column(Float)
    change_1h: Mapped[float] = mapped_column(Float)
    change_4h: Mapped[float] = mapped_column(Float)
    change_24h: Mapped[float] = mapped_column(Float)
    quote_volume_24h: Mapped[float] = mapped_column(Float)
    rsi_15m: Mapped[float] = mapped_column(Float)
    ema20_15m: Mapped[float] = mapped_column(Float)
    atr_15m: Mapped[float] = mapped_column(Float)
    volume_zscore: Mapped[float] = mapped_column(Float)
    funding_rate: Mapped[float] = mapped_column(Float)
    open_interest: Mapped[float] = mapped_column(Float)
    oi_change_15m: Mapped[float] = mapped_column(Float, default=0)
    long_short_ratio: Mapped[float] = mapped_column(Float, default=0)
    taker_buy_ratio: Mapped[float] = mapped_column(Float, default=0)
    structure_signal: Mapped[str] = mapped_column(String(64), default="none")
    market_state: Mapped[str] = mapped_column(String(64), default="neutral")
    score: Mapped[float] = mapped_column(Float)
    level: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    level: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    entry_min: Mapped[float] = mapped_column(Float)
    entry_max: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit_1: Mapped[float] = mapped_column(Float)
    take_profit_2: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
