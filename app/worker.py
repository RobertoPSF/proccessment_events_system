import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import insert, select, update

from app.database.database import SessionLocal
from app.database.models import Notification, FailedNotification
from app.utils.rate_limiter import RateLimiter


BATCH_SIZE = 10
TIMEOUT_SECONDS = 30
rate_limiter = RateLimiter(rate_per_minute=600)
MAX_RETRIES = 5


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
                .order_by(Notification.created_at, Notification.id)  # ✅ ordem consistente
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
                    .order_by(Notification.created_at, Notification.id)
                    .limit(remaining_slots)
                    .with_for_update(skip_locked=True)
                )

                retry_notifications = db.execute(retry_stmt).scalars().all()
                notifications.extend(retry_notifications)

            ids = [n.id for n in notifications]

            if ids:
                db.execute(
                    update(Notification)
                    .where(Notification.id.in_(ids))
                    .values(
                        status="processing",
                        locked_at=now
                    )
                )

            return [
                {
                    "id": n.id,
                    "retry_count": n.retry_count,
                    "event_id": n.event_id,
                    "user_id": n.user_id,
                    "type": n.type,
                    "payload": n.payload
                }
                for n in notifications
            ]

    finally:
        db.close()


def handle_failure_batch(failed_notifications):

    if not failed_notifications:
        return

    db = SessionLocal()

    try:
        with db.begin():

            to_failed = []
            to_retry = []

            for n, error in failed_notifications:

                if n["retry_count"] + 1 >= MAX_RETRIES:
                    to_failed.append((n, error))
                else:
                    to_retry.append((n, error))

            if to_failed:
                db.execute(
                    insert(FailedNotification).values([
                        {
                            "notification_id": n["id"],
                            "event_id": n["event_id"],
                            "user_id": n["user_id"],
                            "type": n["type"],
                            "payload": n["payload"],
                            "error_message": str(error),
                            "retry_count": n["retry_count"] + 1
                        }
                        for n, error in to_failed
                    ])
                )

                db.execute(
                    update(Notification)
                    .where(Notification.id.in_([n["id"] for n, _ in to_failed]))
                    .values(status="failed")
                )

            if to_retry:
                db.execute(
                    update(Notification)
                    .where(Notification.id.in_([n["id"] for n, _ in to_retry]))
                    .values(
                        status="pending",
                        retry_count=Notification.retry_count + 1,
                        scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=5)
                    )
                )

    finally:
        db.close()


def mark_done_batch(notification_ids):

    if not notification_ids:
        return

    db = SessionLocal()

    try:
        with db.begin():

            db.execute(
                update(Notification)
                .where(Notification.id.in_(notification_ids))
                .values(
                    status="done",
                    processed_at=datetime.now(timezone.utc),
                    locked_at=None
                )
            )

    finally:
        db.close()


def run_worker():

    while True:

        notifications = fetch_notifications()

        if not notifications:
            time.sleep(3)
            continue

        success_ids = []
        failed = []

        for notification in notifications:

            while not rate_limiter.allow():
                time.sleep(0.05)

            try:
                process_notification(notification["id"])
                success_ids.append(notification["id"])

            except Exception as e:
                failed.append((notification, e))

        mark_done_batch(success_ids)
        handle_failure_batch(failed)


if __name__ == "__main__":
    run_worker()