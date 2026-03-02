from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _resolve_backfill_user_id(conn) -> int:
    users = conn.execute(text("SELECT id FROM users ORDER BY id")).fetchall()
    if len(users) == 1:
        return int(users[0][0])
    if len(users) > 1:
        raise RuntimeError(
            "Cannot auto-migrate legacy trades: multiple users exist and trades have no ownership. "
            "Run a manual migration to map legacy trades to specific users before starting the app."
        )

    row = conn.execute(text("SELECT id FROM users WHERE username = :username"), {"username": "legacy_migration_user"}).first()
    if row:
        return int(row[0])

    conn.execute(
        text(
            """
            INSERT INTO users (username, hashed_password, created_at)
            VALUES (:username, :hashed_password, CURRENT_TIMESTAMP)
            """
        ),
        {"username": "legacy_migration_user", "hashed_password": "migrated-no-login"},
    )
    return int(conn.execute(text("SELECT id FROM users WHERE username = :username"), {"username": "legacy_migration_user"}).scalar_one())


def _migrate_trades_table_sqlite(conn, has_user_id: bool) -> None:
    legacy_user_id = _resolve_backfill_user_id(conn)

    if has_user_id:
        conn.execute(text("UPDATE trades SET user_id = :legacy_user_id WHERE user_id IS NULL"), {"legacy_user_id": legacy_user_id})
        source_user_id = "COALESCE(user_id, :legacy_user_id)"
    else:
        source_user_id = ":legacy_user_id"

    conn.execute(
        text(
            f"""
            CREATE TABLE trades_migrated (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                ticket INTEGER NOT NULL,
                symbol VARCHAR(24) NOT NULL,
                trade_type VARCHAR(8) NOT NULL,
                volume FLOAT NOT NULL,
                open_price FLOAT NOT NULL,
                close_price FLOAT NOT NULL,
                stop_loss FLOAT NOT NULL,
                take_profit FLOAT NOT NULL,
                profit FLOAT NOT NULL,
                open_time DATETIME NOT NULL,
                close_time DATETIME NOT NULL,
                synced_at DATETIME NOT NULL,
                tag VARCHAR(64),
                notes TEXT,
                CONSTRAINT uq_trades_user_ticket UNIQUE (user_id, ticket),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """
        )
    )

    conn.execute(
        text(
            f"""
            INSERT INTO trades_migrated (
                id, user_id, ticket, symbol, trade_type, volume, open_price, close_price,
                stop_loss, take_profit, profit, open_time, close_time, synced_at, tag, notes
            )
            SELECT
                id,
                {source_user_id},
                ticket,
                symbol,
                trade_type,
                volume,
                open_price,
                close_price,
                stop_loss,
                take_profit,
                profit,
                open_time,
                close_time,
                COALESCE(synced_at, CURRENT_TIMESTAMP),
                tag,
                notes
            FROM trades
            """
        ),
        {"legacy_user_id": legacy_user_id},
    )
    conn.execute(text("DROP TABLE trades"))
    conn.execute(text("ALTER TABLE trades_migrated RENAME TO trades"))
    conn.execute(text("CREATE INDEX ix_trades_ticket ON trades (ticket)"))
    conn.execute(text("CREATE INDEX ix_trades_symbol ON trades (symbol)"))
    conn.execute(text("CREATE INDEX ix_trades_trade_type ON trades (trade_type)"))
    conn.execute(text("CREATE INDEX ix_trades_open_time ON trades (open_time)"))
    conn.execute(text("CREATE INDEX ix_trades_close_time ON trades (close_time)"))
    conn.execute(text("CREATE INDEX ix_trades_user_id ON trades (user_id)"))


def run_schema_migrations() -> None:
    inspector = inspect(engine)
    if "trades" not in inspector.get_table_names() or "users" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("trades")}
    unique_constraints = inspector.get_unique_constraints("trades")
    has_user_id = "user_id" in columns
    needs_migration = not has_user_id
    has_scoped_unique = any(tuple(c["column_names"]) == ("user_id", "ticket") for c in unique_constraints)
    global_ticket_uniques = [c for c in unique_constraints if tuple(c["column_names"]) == ("ticket",)]

    if not needs_migration:
        has_global_ticket_unique = bool(global_ticket_uniques)
        needs_migration = has_global_ticket_unique or not has_scoped_unique

    if not needs_migration:
        return

    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            _migrate_trades_table_sqlite(conn, has_user_id=has_user_id)
            return

        if not has_user_id:
            conn.execute(text("ALTER TABLE trades ADD COLUMN user_id INTEGER"))
        legacy_user_id = _resolve_backfill_user_id(conn)
        conn.execute(text("UPDATE trades SET user_id = :legacy_user_id WHERE user_id IS NULL"), {"legacy_user_id": legacy_user_id})

        if engine.dialect.name == "postgresql":
            for constraint in global_ticket_uniques:
                if constraint.get("name"):
                    conn.execute(text(f'ALTER TABLE trades DROP CONSTRAINT IF EXISTS "{constraint["name"]}"'))
            if not has_scoped_unique:
                conn.execute(text("ALTER TABLE trades ADD CONSTRAINT uq_trades_user_ticket UNIQUE (user_id, ticket)"))
        elif engine.dialect.name in {"mysql", "mariadb"}:
            for constraint in global_ticket_uniques:
                if constraint.get("name"):
                    conn.execute(text(f"ALTER TABLE trades DROP INDEX `{constraint['name']}`"))
            if not has_scoped_unique:
                conn.execute(text("ALTER TABLE trades ADD UNIQUE INDEX uq_trades_user_ticket (user_id, ticket)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
