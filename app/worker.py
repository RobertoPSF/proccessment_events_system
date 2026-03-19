import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

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

            stmt = (
                select(Notification)
                .where(
                    (
                        (Notification.status == "pending") &
                        (Notification.scheduled_at <= now)
                    )
                    |
                    (
                        (Notification.status == "processing") &
                        (Notification.locked_at < timeout_limit)
                    )
                )
                .order_by(Notification.created_at)
                .limit(BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )

            notifications = db.execute(stmt).scalars().all()

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

            notification = db.get(Notification, notification_id)

            if not notification:
                return

            notification.status = "done"
            notification.processed_at = datetime.now(timezone.utc)
            notification.locked_at = None

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