from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(24), index=True)
    trade_type: Mapped[str] = mapped_column(String(8), index=True)
    volume: Mapped[float] = mapped_column(Float)
    open_price: Mapped[float] = mapped_column(Float)
    close_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    profit: Mapped[float] = mapped_column(Float)
    open_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    successful: Mapped[bool] = mapped_column(Boolean, default=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
