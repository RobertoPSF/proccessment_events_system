from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.schemas import EventCreate
from app.services.event_service import EventService
from app.database.get_db import get_db

router = APIRouter()


@router.post("/events")
def create_event(event: EventCreate, db: Session = Depends(get_db)):

    new_event = EventService.create_event(
        db=db,
        event_type=event.type,
        payload=event.payload,
        idempotency_key=event.idempotency_key
    )

    return {
        "event_id": str(new_event.id)
    }
    