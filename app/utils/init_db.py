from sqlalchemy import text
from datetime import datetime, timedelta, timezone

from app.database.database import engine, Base
from app.database import models


def month_range(dt: datetime):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if dt.month == 12:
        end = start.replace(year=dt.year + 1, month=1)
    else:
        end = start.replace(month=dt.month + 1)

    return start, end


def partition_name(dt: datetime):
    return f"notifications_{dt.year}_{dt.month:02d}"


def create_partition(conn, dt: datetime):

    start, end = month_range(dt)
    name = partition_name(dt)

    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {name}
        PARTITION OF notifications
        FOR VALUES FROM ('{start}') TO ('{end}');
    """))

    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_{name}_queue
        ON {name} (status, scheduled_at, created_at);
    """))

    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_{name}_locked
        ON {name} (locked_at);
    """))

    constraint_name = f"uq_{name}_event_dedup"

    exists = conn.execute(text(f"""
        SELECT 1
        FROM pg_constraint
        WHERE conname = :constraint_name
        LIMIT 1;
    """), {"constraint_name": constraint_name}).scalar()

    if not exists:
        conn.execute(text(f"""
            ALTER TABLE {name}
            ADD CONSTRAINT {constraint_name}
            UNIQUE (event_id, deduplication_key);
        """))


def ensure_partitions():

    now = datetime.now(timezone.utc)

    current = now

    next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)

    with engine.begin() as conn:
        create_partition(conn, current)
        create_partition(conn, next_month)


def create_partitioned_notifications():

    with engine.begin() as conn:

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notifications (
        id UUID NOT NULL,
        type TEXT NOT NULL,
        event_id UUID NOT NULL,
        status TEXT,
        user_id UUID NOT NULL,
        payload JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        processed_at TIMESTAMPTZ,
        locked_at TIMESTAMPTZ,
        scheduled_at TIMESTAMPTZ,
        retry_count INT DEFAULT 0,
        deduplication_key TEXT NOT NULL,
        version INT DEFAULT 0 NOT NULL
    ) PARTITION BY RANGE (created_at);
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_notifications_id
        ON notifications (id);
        """))

    ensure_partitions()


def init():

    Base.metadata.create_all(bind=engine, tables=[
        models.Event.__table__,
        models.NotificationCounter.__table__,
    ])

    create_partitioned_notifications()


if __name__ == "__main__":
    init()