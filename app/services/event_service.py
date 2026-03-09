from sqlalchemy.orm import Session
from app.db.models import Event

def create_event(db: Session, type: str, payload: dict):

    event = Event(
        type=type,
        payload=payload
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event