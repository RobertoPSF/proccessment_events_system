from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.event import EventCreate
from app.services.event_service import create_event
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/events")
def create_event_endpoint(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    created_event = create_event(
        db,
        event.type,
        event.payload
    )

    return created_event