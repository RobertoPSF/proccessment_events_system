from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
import uuid

from app.database.models import Notification
from app.utils.hash_generate import generate_hash


class NotificationService:

    @staticmethod
    def create_notification_batch(
        db: Session,
        event_id: uuid,
        notifications_payload: list[dict]
    ):

        now = datetime.now(timezone.utc)

        stmt = insert(Notification).values([
            {
                "event_id": event_id,
                "payload": payload,
                "status": "pending",
                "type": payload.get("type", "default"),
                "locked_at": None,
                "created_at": now,
                "scheduled_at": now,
                "version": 0,
                "deduplication_key": generate_hash(payload)
            }
            for payload in notifications_payload
        ])

        stmt = stmt.on_conflict_do_nothing(
            index_elements=["event_id", "deduplication_key"]
        )

        db.execute(stmt)