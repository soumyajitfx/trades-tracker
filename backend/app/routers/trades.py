from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import SyncState, Trade, User
from app.schemas import TradeOut
from app.services.analytics import compute_metrics
from app.services.mt5_service import MT5SyncError, sync_trades

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.post("/sync")
def sync_now(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        inserted = sync_trades(db, current_user.id)
        state = db.query(SyncState).first() or SyncState()
        state.successful = True
        state.last_sync = datetime.utcnow()
        state.message = f"Synced {inserted} new trades"
        db.add(state)
        db.commit()
        return {"inserted": inserted, "message": state.message}
    except MT5SyncError as exc:
        state = db.query(SyncState).first() or SyncState()
        state.successful = False
        state.last_sync = datetime.utcnow()
        state.message = str(exc)
        db.add(state)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=list[TradeOut])
def get_trades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    symbol: str | None = Query(default=None),
    trade_type: str | None = Query(default=None),
):
    q = db.query(Trade).filter(Trade.user_id == current_user.id)
    if start:
        q = q.filter(Trade.close_time >= start)
    if end:
        q = q.filter(Trade.close_time <= end)
    if symbol:
        q = q.filter(Trade.symbol == symbol)
    if trade_type:
        q = q.filter(Trade.trade_type == trade_type)
    return q.order_by(Trade.close_time.desc()).all()


@router.get("/metrics")
def metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    symbol: str | None = Query(default=None),
    trade_type: str | None = Query(default=None),
):
    return compute_metrics(db, current_user.id, start, end, symbol, trade_type)
