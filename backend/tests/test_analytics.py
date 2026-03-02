from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import Trade, User
from app.services.analytics import compute_metrics


def test_compute_metrics():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()
    now = datetime.utcnow()
    user = User(username="alice", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add_all(
        [
            Trade(user_id=user.id, ticket=1, symbol="EURUSD", trade_type="buy", volume=1, open_price=1.1, close_price=1.2, stop_loss=1.05, take_profit=1.2, profit=100, open_time=now, close_time=now),
            Trade(user_id=user.id, ticket=2, symbol="EURUSD", trade_type="sell", volume=1, open_price=1.2, close_price=1.25, stop_loss=1.26, take_profit=1.15, profit=-50, open_time=now + timedelta(minutes=2), close_time=now + timedelta(minutes=2)),
        ]
    )
    db.commit()

    result = compute_metrics(db, user.id, None, None, None, None)
    assert result["total_trades"] == 2
    assert result["total_pnl"] == 50
    assert result["max_drawdown"] >= 0
