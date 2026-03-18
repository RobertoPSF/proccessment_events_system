from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert

from app.models import Notification


class NotificationService:

    @staticmethod
    def create_notification_batch(
        db: Session,
        event_id: int,
        notifications_payload: list[dict]
    ):

        now = datetime.now()

        stmt = insert(Notification).values([
            {
                "event_id": event_id,
                "payload": payload,
                "status": "pending",
                "locked_at": None,
                "created_at": now
            }
            for payload in notifications_payload
        ])

        db.execute(stmt)