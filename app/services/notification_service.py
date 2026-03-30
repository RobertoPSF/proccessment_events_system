from http.client import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import update
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
import uuid

from app.database.models import Notification, NotificationCounter
from app.utils.hash_generate import generate_hash


class NotificationService:

    @staticmethod
    def create_notification_batch(
        db: Session,
        event_id: uuid,
        user_id: uuid,
        notifications_payload: list[dict]
    ):

        now = datetime.now(timezone.utc)

        stmt = insert(Notification).values([
            {
                "event_id": event_id,
                "payload": payload,
                "status": "pending",
                "type": payload.get("type", "default"),
                "user_id": user_id,
                "locked_at": None,
                "created_at": now,
                "scheduled_at": now,
                "version": 0,
                "deduplication_key": generate_hash(payload)
            }
            for payload in notifications_payload
        ])

        try:
            db.execute(stmt)
        except IntegrityError as e:
            print("Integrity error:", e)
            raise


    @staticmethod
    def increment_user_counter(db: Session, user_id: uuid.UUID, amount: int, limit: int):

        stmt = (
            update(NotificationCounter)
            .where(
                NotificationCounter.user_id == user_id,
                NotificationCounter.unread_count + amount <= limit
            )
            .values(
                unread_count=NotificationCounter.unread_count + amount
            )
            .returning(NotificationCounter.unread_count)
        )

        result = db.execute(stmt).scalar()

        if result is None:
            print("User notification limit reached or user does not exist.")