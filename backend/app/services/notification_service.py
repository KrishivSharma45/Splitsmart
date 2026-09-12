from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    message: str,
    trip_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        message=message,
        trip_id=trip_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(notification)
    db.flush()
    return notification


def notify_many(
    db: Session,
    user_ids: list[int],
    type: str,
    message: str,
    trip_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> None:
    for user_id in user_ids:
        create_notification(db, user_id, type, message, trip_id, entity_type, entity_id)
