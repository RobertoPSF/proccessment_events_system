import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update

from app.database.database import SessionLocal
from app.database.models import Notification
from app.utils.rate_limiter import RateLimiter


BATCH_SIZE = 10
TIMEOUT_SECONDS = 30
rate_limiter = RateLimiter(rate_per_minute=600)


def get_timeout_limit(now):
    return now - timedelta(seconds=TIMEOUT_SECONDS)


def process_notification(notification_id):
    print(f"Processing notification {notification_id}")
    time.sleep(2)


def fetch_notifications():

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        timeout_limit = get_timeout_limit(now)

        with db.begin():

            pending_stmt = (
                select(Notification)
                .where(
                    Notification.status == "pending",
                    Notification.scheduled_at <= now
                )
                .order_by(Notification.created_at)
                .limit(BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )

            pending_notifications = db.execute(pending_stmt).scalars().all()

            remaining_slots = BATCH_SIZE - len(pending_notifications)

            notifications = list(pending_notifications)

            if remaining_slots > 0:

                retry_stmt = (
                    select(Notification)
                    .where(
                        Notification.status == "processing",
                        Notification.locked_at < timeout_limit
                    )
                    .order_by(Notification.created_at)
                    .limit(remaining_slots)
                    .with_for_update(skip_locked=True)
                )

                retry_notifications = db.execute(retry_stmt).scalars().all()

                notifications.extend(retry_notifications)

            for notification in notifications:
                notification.status = "processing"
                notification.locked_at = now

            return [n.id for n in notifications]

    finally:
        db.close()


def mark_done(notification_id):

    db = SessionLocal()

    try:
        with db.begin():

            stmt = (
                update(Notification)
                .where(
                    Notification.id == notification_id,
                    Notification.status == "processing"
                )
                .values(
                    status="done",
                    processed_at=datetime.now(timezone.utc),
                    locked_at=None
                )
            )

            result = db.execute(stmt)

    finally:
        db.close()


def run_worker():

    while True:

        ids = fetch_notifications()

        if not ids:
            time.sleep(3)
            continue

        for notification_id in ids:

            while not rate_limiter.allow():
                time.sleep(0.05)

            process_notification(notification_id)
            mark_done(notification_id)


if __name__ == "__main__":
    run_worker()