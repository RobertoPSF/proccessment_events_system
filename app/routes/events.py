from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import EventCreate
from app.services.event_service import EventService
from app.utils.get_db import get_db

router = APIRouter()


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
    