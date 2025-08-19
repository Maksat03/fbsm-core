from dataclasses import asdict, is_dataclass
from uuid import uuid4

from core.notifications.base import Notification
from core.notifications.queues import NotificationSendMQ


def send(
    account_id: int,
    notification: Notification,
    push: bool,
    idempotency_key: str | None = None,
    raise_exception: bool = True,
) -> None:
    if not isinstance(notification, Notification) or not is_dataclass(notification):
        raise TypeError(
            "Нужно передать наследника от `core.notifications.base.Notification`"
        )

    payload = {
        "type": notification.type,
        "level": notification.level.value,
        "account_id": account_id,
        "push": push,
        "metadata": asdict(notification),
    }
    if not idempotency_key:
        idempotency_key = str(uuid4())

    NotificationSendMQ.publish(
        idempotency_key, payload=payload, raise_exception=raise_exception
    )
