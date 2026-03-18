from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import Event
from app.services.notification_service import NotificationService


class EventService:

    @staticmethod
    def create_event(
        db: Session, 
        event_type: str, 
        payload: dict
    ):
        
        with db.begin():

            stmt = insert(Event).values(
                type=event_type,
                payload=payload
            )

            db.execute(stmt)
            db.flush()

            notifications_payload = [
                {"type": "email", "data": payload},
                {"type": "audit_log", "data": payload}
            ]

            NotificationService.create_notification_batch(
                db=db,
                event_id=stmt.returning(Event.id),
                notifications_payload=notifications_payload
            )

        return stmt.returning(Event.id)