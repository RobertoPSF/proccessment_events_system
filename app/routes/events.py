from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Event, Notification
from app.schemas import EventCreate
from app.service.event_service import EventService

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/events")
def create_event(event: EventCreate, db: Session = Depends(get_db)):

    new_event = EventService.create_event(
        db=db,
        event_type=event.type,
        payload=event.payload
    )

    return {
        "event_id": str(new_event.id)
    }
    