import time
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from .database import SessionLocal
from .models import Notification

from .database import Base, engine


def run_worker():
    Base.metadata.create_all(bind=engine)

    while True:
        try:
            db = SessionLocal()

            stmt = (
                select(Notification)
                .where(Notification.status == "pending")
                .order_by(Notification.created_at)
                .limit(10)
            )

            notifications = db.execute(stmt).scalars().all()

            for notification in notifications:
                print(f"Processing notification {notification.id}")
                notification.status = "done"

            db.commit()
            db.close()

        except ProgrammingError:
            print("Table not ready yet, retrying...")
            time.sleep(3)
            continue

        time.sleep(5)


if __name__ == "__main__":
    print("Worker started")
    run_worker()