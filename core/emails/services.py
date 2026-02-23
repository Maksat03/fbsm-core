from uuid import uuid4

from core.emails.queues import EmailSendMQ


def send(
    subject: str,
    content: str,
    to_mail: str,
    idempotency_key: str | None = None,
    raise_exception: bool = True,
):
    EmailSendMQ.publish(
        idempotency_key or uuid4(),
        {"subject": subject, "content": content, "to_mail": to_mail},
        raise_exception=raise_exception,
    )
