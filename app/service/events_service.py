from sqlalchemy.orm import Session

from app.models import Event, Notification


class EventService:

    @staticmethod
    def create_event(db: Session, event_type: str, payload: dict):

        event = Event(
            type=event_type,
            payload=payload
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        notification = Notification(
            event_id=event.id,
            payload=payload
        )

        db.add(notification)
        db.commit()

        return event