from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database.models import Event
from app.services.notification_service import NotificationService

USER_NOTIFICATION_LIMIT = 50


class EventService:

    @staticmethod
    def create_event(
        db: Session,
        event_type: str,
        payload: dict,
        idempotency_key: str
    ):
        with db.begin():

            stmt = (
                insert(Event)
                .values(
                    type=event_type,
                    payload=payload,
                    idempotency_key=idempotency_key
                )
                .on_conflict_do_nothing(
                    index_elements=["idempotency_key"]
                )
                .returning(Event.id)
            )

            result = db.execute(stmt)
            event_id = result.scalar()

            if not event_id:
                event = db.query(Event).filter_by(
                    idempotency_key=idempotency_key
                ).first()
                event_id = event.id
            else:
                event = db.get(Event, event_id)

            user_id = payload["user_id"]

            notifications_payload = [
                {"type": "email", "data": payload},
                {"type": "audit_log", "data": payload}
            ]

            amount = len(notifications_payload)

            NotificationService.increment_user_counter(
                db=db,
                user_id=user_id,
                amount=amount,
                limit=USER_NOTIFICATION_LIMIT
            )

            NotificationService.create_notification_batch(
                db=db,
                event_id=event_id,
                user_id=user_id,
                notifications_payload=notifications_payload
            )

        return event