from sqlalchemy import Column, ForeignKey, Index, String, DateTime, Integer, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from .database import Base


class Event(Base):

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    idempotency_key = Column(String, unique=True, index=True, nullable=False)


class Notification(Base):

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)

    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False
    )

    status = Column(String, default="pending", index=True)
    payload = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    processed_at = Column(DateTime(timezone=True))
    locked_at = Column(DateTime(timezone=True), nullable=True)

    scheduled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    retry_count = Column(Integer, default=0)
    deduplication_key = Column(String, nullable=False)

    __table_args__ = (
        Index(
            "idx_notifications_queue",
            "status",
            "scheduled_at",
            "created_at"
        ),

        Index(
            "idx_notifications_locked",
            "locked_at"
        ),

        Index(
            "idx_notifications_pending",
            "created_at",
            postgresql_where=text("status = 'pending'")
        ),
        UniqueConstraint("event_id","deduplication_key")
    )


class NotificationCounter(Base):

    __tablename__ = "notification_counters"

    user_id = Column(Integer, primary_key=True)
    unread_count = Column(Integer, default=0)