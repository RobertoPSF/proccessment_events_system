from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app.models import NotificationCounter


class CounterService:

    @staticmethod
    def increment_unread(db: Session, user_id: int):

        stmt = insert(NotificationCounter).values(
            user_id=user_id,
            unread_count=1
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[NotificationCounter.user_id],
            set_={"unread_count": NotificationCounter.unread_count + 1}
        )

        db.execute(stmt)