from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from app.db import Base, run_schema_migrations
from app.services import mt5_service


def test_fetch_mt5_trades_derives_open_price_from_entry(monkeypatch):
    fake_mt5 = SimpleNamespace(
        DEAL_ENTRY_IN=0,
        DEAL_ENTRY_OUT=1,
        DEAL_TYPE_BUY=0,
        DEAL_TYPE_SELL=1,
        initialize=lambda **kwargs: True,
        shutdown=lambda: None,
        last_error=lambda: (0, ""),
    )
    deals = [
        SimpleNamespace(ticket=10, position_id=501, entry=fake_mt5.DEAL_ENTRY_IN, type=fake_mt5.DEAL_TYPE_BUY, symbol="EURUSD", volume=0.4, price=1.1000, sl=1.09, tp=1.12, profit=0.0, time=100),
        SimpleNamespace(ticket=11, position_id=501, entry=fake_mt5.DEAL_ENTRY_IN, type=fake_mt5.DEAL_TYPE_BUY, symbol="EURUSD", volume=0.6, price=1.2000, sl=1.09, tp=1.12, profit=0.0, time=101),
        SimpleNamespace(ticket=12, position_id=501, entry=fake_mt5.DEAL_ENTRY_OUT, type=fake_mt5.DEAL_TYPE_BUY, symbol="EURUSD", volume=1.0, price=1.2500, sl=1.09, tp=1.28, profit=800.0, time=102),
    ]

    monkeypatch.setattr(mt5_service, "mt5", fake_mt5)
    monkeypatch.setattr(mt5_service.mt5, "history_deals_get", lambda _from, _to: deals)

    rows = mt5_service.fetch_mt5_trades()

    assert len(rows) == 1
    # weighted entry price = (0.4*1.10 + 0.6*1.20) / 1.0
    assert rows[0]["open_price"] == 1.16
    assert rows[0]["close_price"] == 1.25


def test_run_schema_migrations_backfills_user_id_on_existing_trades(monkeypatch, tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    test_engine = create_engine(f"sqlite:///{db_path}")

    with test_engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(64) UNIQUE, hashed_password VARCHAR(255) NOT NULL, created_at DATETIME)"))
        conn.execute(text("INSERT INTO users (id, username, hashed_password, created_at) VALUES (1, 'alice', 'x', CURRENT_TIMESTAMP)"))
        conn.execute(text("CREATE TABLE trades (id INTEGER PRIMARY KEY, ticket INTEGER UNIQUE, symbol VARCHAR(24), trade_type VARCHAR(8), volume FLOAT, open_price FLOAT, close_price FLOAT, stop_loss FLOAT, take_profit FLOAT, profit FLOAT, open_time DATETIME, close_time DATETIME, synced_at DATETIME, tag VARCHAR(64), notes TEXT)"))
        conn.execute(text("INSERT INTO trades (id, ticket, symbol, trade_type, volume, open_price, close_price, stop_loss, take_profit, profit, open_time, close_time, synced_at) VALUES (1, 777, 'EURUSD', 'buy', 1.0, 1.1, 1.2, 1.0, 1.3, 10.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))

    monkeypatch.setattr("app.db.engine", test_engine)
    run_schema_migrations()

    with test_engine.begin() as conn:
        user_id = conn.execute(text("SELECT user_id FROM trades WHERE ticket = 777")).scalar_one()
        legacy_user = conn.execute(text("SELECT username FROM users WHERE id = :id"), {"id": user_id}).scalar_one()

    assert legacy_user == "alice"

    # ensure user-scoped uniqueness allows same ticket for another user
    Base.metadata.create_all(test_engine)
    with test_engine.begin() as conn:
        conn.execute(text("INSERT INTO users (username, hashed_password, created_at) VALUES ('bob', 'x', CURRENT_TIMESTAMP)"))
        bob_id = conn.execute(text("SELECT id FROM users WHERE username='bob'")).scalar_one()
        conn.execute(text("INSERT INTO trades (user_id, ticket, symbol, trade_type, volume, open_price, close_price, stop_loss, take_profit, profit, open_time, close_time, synced_at) VALUES (:uid, 777, 'EURUSD', 'buy', 1.0, 1.1, 1.2, 1.0, 1.3, 5.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"), {"uid": bob_id})

    with test_engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM trades WHERE ticket = 777")).scalar_one()
    assert count == 2


def test_run_schema_migrations_non_sqlite_replaces_global_ticket_unique(monkeypatch):
    executed = []

    class FakeConn:
        def execute(self, statement, params=None):
            executed.append((str(statement), params or {}))

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        class dialect:
            name = "postgresql"

        def begin(self):
            return FakeBegin()

    class FakeInspector:
        def get_table_names(self):
            return ["trades", "users"]

        def get_columns(self, _table):
            return [{"name": "id"}, {"name": "user_id"}, {"name": "ticket"}]

        def get_unique_constraints(self, _table):
            return [
                {"name": "uq_trades_ticket", "column_names": ["ticket"]},
            ]

    monkeypatch.setattr("app.db.engine", FakeEngine())
    monkeypatch.setattr("app.db.inspect", lambda _engine: FakeInspector())
    monkeypatch.setattr("app.db._resolve_backfill_user_id", lambda _conn: 42)

    run_schema_migrations()

    sql = "\n".join(stmt for stmt, _ in executed)
    assert "UPDATE trades SET user_id = :legacy_user_id WHERE user_id IS NULL" in sql
    assert "ALTER TABLE trades DROP CONSTRAINT IF EXISTS \"uq_trades_ticket\"" in sql
    assert "ALTER TABLE trades ADD CONSTRAINT uq_trades_user_ticket UNIQUE (user_id, ticket)" in sql


def test_run_schema_migrations_requires_manual_mapping_if_multiple_users(monkeypatch, tmp_path):
    db_path = tmp_path / "legacy-multi.sqlite3"
    test_engine = create_engine(f"sqlite:///{db_path}")

    with test_engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(64) UNIQUE, hashed_password VARCHAR(255) NOT NULL, created_at DATETIME)"))
        conn.execute(text("INSERT INTO users (id, username, hashed_password, created_at) VALUES (1, 'alice', 'x', CURRENT_TIMESTAMP)"))
        conn.execute(text("INSERT INTO users (id, username, hashed_password, created_at) VALUES (2, 'bob', 'x', CURRENT_TIMESTAMP)"))
        conn.execute(text("CREATE TABLE trades (id INTEGER PRIMARY KEY, ticket INTEGER UNIQUE, symbol VARCHAR(24), trade_type VARCHAR(8), volume FLOAT, open_price FLOAT, close_price FLOAT, stop_loss FLOAT, take_profit FLOAT, profit FLOAT, open_time DATETIME, close_time DATETIME, synced_at DATETIME, tag VARCHAR(64), notes TEXT)"))
        conn.execute(text("INSERT INTO trades (id, ticket, symbol, trade_type, volume, open_price, close_price, stop_loss, take_profit, profit, open_time, close_time, synced_at) VALUES (1, 777, 'EURUSD', 'buy', 1.0, 1.1, 1.2, 1.0, 1.3, 10.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))

    monkeypatch.setattr("app.db.engine", test_engine)
    with pytest.raises(RuntimeError, match="manual migration"):
        run_schema_migrations()
