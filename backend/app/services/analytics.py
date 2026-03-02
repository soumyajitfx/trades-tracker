from collections import defaultdict
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from app.models import Trade


def _rr(trade: Trade) -> float:
    risk = abs(trade.open_price - trade.stop_loss) * trade.volume
    reward = abs((trade.take_profit if trade.take_profit else trade.close_price) - trade.open_price) * trade.volume
    if risk == 0:
        return 0.0
    realized = abs(trade.close_price - trade.open_price) * trade.volume
    signed = realized / risk
    return signed if trade.profit >= 0 else -signed


def compute_metrics(
    db: Session,
    user_id: int,
    start: datetime | None,
    end: datetime | None,
    symbol: str | None,
    trade_type: str | None,
):
    q = db.query(Trade).filter(Trade.user_id == user_id)
    if start:
        q = q.filter(Trade.close_time >= start)
    if end:
        q = q.filter(Trade.close_time <= end)
    if symbol:
        q = q.filter(Trade.symbol == symbol)
    if trade_type:
        q = q.filter(Trade.trade_type == trade_type)
    trades = q.order_by(Trade.close_time.asc()).all()
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_rr": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "equity_curve": [],
            "breakdown": {"daily": {}, "weekly": {}, "monthly": {}},
        }

    profits = np.array([t.profit for t in trades], dtype=float)
    wins = (profits > 0).sum()
    rrs = np.array([_rr(t) for t in trades], dtype=float)
    equity = profits.cumsum()
    peak = np.maximum.accumulate(equity)
    drawdown = peak - equity

    returns = np.diff(np.insert(equity, 0, 0.0))
    sharpe = 0.0
    if returns.std() > 0:
        sharpe = float((returns.mean() / returns.std()) * np.sqrt(252))

    daily = defaultdict(float)
    weekly = defaultdict(float)
    monthly = defaultdict(float)
    for t in trades:
        daily[t.close_time.strftime("%Y-%m-%d")] += t.profit
        weekly[t.close_time.strftime("%Y-W%U")] += t.profit
        monthly[t.close_time.strftime("%Y-%m")] += t.profit

    curve = [{"time": t.close_time.isoformat(), "equity": float(v)} for t, v in zip(trades, equity)]

    return {
        "total_trades": len(trades),
        "win_rate": round((wins / len(trades)) * 100, 2),
        "total_pnl": round(float(profits.sum()), 2),
        "avg_rr": round(float(rrs.mean()), 2),
        "max_drawdown": round(float(drawdown.max()), 2),
        "sharpe_ratio": round(sharpe, 2),
        "equity_curve": curve,
        "breakdown": {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
        },
    }
