from sqlalchemy.orm import Session

from app.models import Notification


class NotificationService:

    @staticmethod
    def create_notification_batch(
        db: Session,
        event_id,
        notifications_payload: list[dict]
    ):
        
        notifications = [
            Notification(
                event_id=event_id,
                payload=payload,
                status="pending"
            )
            for payload in notifications_payload
        ]

        db.add_all(notifications)

        return notifications
    
