from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Trade

try:
    import MetaTrader5 as mt5
except Exception:  # pragma: no cover
    mt5 = None


class MT5SyncError(Exception):
    pass


def _entry_prices_by_position(deals) -> dict[int, float]:
    entry_prices: dict[int, float] = {}
    weighted_sum: dict[int, float] = {}
    total_volume: dict[int, float] = {}

    for d in sorted(deals, key=lambda x: (x.time, x.ticket)):
        position_id = int(getattr(d, "position_id", 0) or 0)
        if position_id == 0:
            continue
        if d.entry != mt5.DEAL_ENTRY_IN:
            continue
        volume = float(d.volume or 0)
        if volume <= 0:
            continue
        weighted_sum[position_id] = weighted_sum.get(position_id, 0.0) + float(d.price) * volume
        total_volume[position_id] = total_volume.get(position_id, 0.0) + volume
        entry_prices[position_id] = weighted_sum[position_id] / total_volume[position_id]

    return entry_prices


def _mock_trades() -> list[dict]:
    now = datetime.utcnow()
    return [
        {
            "ticket": 1001,
            "symbol": "EURUSD",
            "trade_type": "buy",
            "volume": 1.0,
            "open_price": 1.08,
            "close_price": 1.085,
            "stop_loss": 1.077,
            "take_profit": 1.086,
            "profit": 500.0,
            "open_time": now - timedelta(days=3),
            "close_time": now - timedelta(days=3, hours=-2),
        },
        {
            "ticket": 1002,
            "symbol": "XAUUSD",
            "trade_type": "sell",
            "volume": 0.5,
            "open_price": 2400,
            "close_price": 2410,
            "stop_loss": 2412,
            "take_profit": 2385,
            "profit": -300.0,
            "open_time": now - timedelta(days=2),
            "close_time": now - timedelta(days=2, hours=-1),
        },
    ]


def fetch_mt5_trades() -> list[dict]:
    if mt5 is None:
        return _mock_trades()
    if not all([settings.mt5_login, settings.mt5_password, settings.mt5_server]):
        raise MT5SyncError("MT5 credentials are not configured")

    initialized = mt5.initialize(path=settings.mt5_path, login=settings.mt5_login, password=settings.mt5_password, server=settings.mt5_server)
    if not initialized:
        raise MT5SyncError(f"MT5 initialize failed: {mt5.last_error()}")

    deals = mt5.history_deals_get(datetime(2000, 1, 1), datetime.utcnow())
    mt5.shutdown()
    if deals is None:
        raise MT5SyncError("Failed to fetch MT5 history")

    output = []
    entry_prices = _entry_prices_by_position(deals)
    for d in deals:
        if d.entry != mt5.DEAL_ENTRY_OUT:
            continue
        position_id = int(getattr(d, "position_id", 0) or 0)
        open_price = entry_prices.get(position_id, float(d.price))
        output.append(
            {
                "ticket": int(d.ticket),
                "symbol": d.symbol,
                "trade_type": "buy" if d.type == mt5.DEAL_TYPE_BUY else "sell",
                "volume": float(d.volume),
                "open_price": float(open_price),
                "close_price": float(d.price),
                "stop_loss": float(d.sl or d.price),
                "take_profit": float(d.tp or d.price),
                "profit": float(d.profit),
                "open_time": datetime.utcfromtimestamp(d.time),
                "close_time": datetime.utcfromtimestamp(d.time),
            }
        )
    return output


def sync_trades(db: Session, user_id: int) -> int:
    trades = fetch_mt5_trades()
    inserted = 0
    for row in trades:
        exists = db.query(Trade).filter(Trade.user_id == user_id, Trade.ticket == row["ticket"]).first()
        if exists:
            continue
        db.add(Trade(user_id=user_id, **row))
        inserted += 1
    db.commit()
    return inserted
