from sqlalchemy.orm import Session

from app.models import Event
from app.service.notification_service import NotificationService


class EventService:

    @staticmethod
    def create_event(
        db: Session, 
        event_type: str, 
        payload: dict
    ):
        
        with db.begin():

            event = Event(
                type=event_type,
                payload=payload
            )

            db.add(event)
            db.flush()

            NotificationService.create_notification(
                db=db,
                event_id=event.id,
                payload=payload
            )

        return event