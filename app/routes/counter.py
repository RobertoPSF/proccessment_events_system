from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.counter_service import CounterService
from app.database.get_db import get_db

router = APIRouter()


@router.post("/counter/{user_id}/increment")
def increment_counter(user_id: int, db: Session = Depends(get_db)):

    with db.begin():
        CounterService.increment_unread(db, user_id)

    return {"message": f"Counter for user {user_id} incremented"}