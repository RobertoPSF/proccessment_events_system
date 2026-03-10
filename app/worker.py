import time

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Notification


def process_notification(notification):
    print("Processing notification:", notification.id)

    time.sleep(2)

    notification.status = "done"


def run_worker():

    while True:

        db: Session = SessionLocal()

        try:

            stmt = (
                select(Notification)
                .where(Notification.status == "pending")
                .limit(10)
            )

            notifications = db.execute(stmt).scalars().all()

            if not notifications:
                time.sleep(5)
                continue

            for notification in notifications:

                notification.status = "processing"

                db.commit()

                process_notification(notification)

                db.commit()

        finally:
            db.close()


if __name__ == "__main__":
    run_worker()