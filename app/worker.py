import time
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Notification
from app.init_db import init


def process_notification(notification_id):
    print(f"Processing notification {notification_id}")
    time.sleep(2)


def fetch_notifications():

    db = SessionLocal()

    try:

        with db.begin():

            stmt = (
                select(Notification)
                .where(Notification.status == "pending")
                .order_by(Notification.created_at)
                .with_for_update(skip_locked=True)
                .limit(limit=10)
            )

            notifications = db.execute(stmt).scalars().all()

            for notification in notifications:
                notification.status = "processing"

            return [n.id for n in notifications]

    finally:
        db.close()


def mark_done(notification_id):

    db = SessionLocal()

    try:

        with db.begin():

            notification = db.get(Notification, notification_id)

            notification.status = "done"

    finally:
        db.close()


def run_worker():

    while True:

        ids = fetch_notifications()

        if not ids:
            time.sleep(3)
            continue

        for notification_id in ids:

            process_notification(notification_id)

            mark_done(notification_id)


if __name__ == "__main__":
    #init()
    run_worker()