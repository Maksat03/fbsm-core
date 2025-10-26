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

    extra_meta: list[dict[str, str]] = [
        {"name": k, "value": str(v)} for k, v in asdict(notification).items()
    ]
    payload = {
        "type": notification.type,
        "level": notification.level.value,
        "account_id": account_id,
        "push": push,
        "extra_meta": extra_meta,
    }
    if not idempotency_key:
        idempotency_key = uuid4()

    NotificationSendMQ.publish(
        idempotency_key, payload=payload, raise_exception=raise_exception
    )


def send_many(
    account_ids: list[int],
    notification: Notification,
    push: bool,
    idempotency_key: str | None = None,
    raise_exception: bool = True,
):
    raise NotImplementedError()

    if not isinstance(notification, Notification) or not is_dataclass(notification):
        raise TypeError(
            "Нужно передать наследника от `core.notifications.base.Notification`"
        )

    extra_meta: list[dict[str, str]] = [
        {"name": k, "value": str(v)} for k, v in asdict(notification).items()
    ]
    payload = {
        "type": notification.type,
        "level": notification.level.value,
        "account_ids": account_ids,
        "push": push,
        "extra_meta": extra_meta,
    }
    if not idempotency_key:
        idempotency_key = uuid4()
