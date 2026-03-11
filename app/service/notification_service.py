from sqlalchemy.orm import Session

from app.models import Notification


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        event_id,
        payload: dict
    ):
        
        notification = Notification(
            event_id = event_id,
            payload = payload,
            status = "pending"
        )

        db.add(notification)

        return notification