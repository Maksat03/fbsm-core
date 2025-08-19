from django.conf import settings

from core.rabbitmq import BaseRabbitMQ


class NotificationSendMQ(BaseRabbitMQ):
    host = getattr(settings, "RABBIT_MQ_HOST", "localhost")
    port = getattr(settings, "RABBIT_MQ_PORT", "5672")
    username = getattr(settings, "RABBIT_MQ_USER", "guest")
    password = getattr(settings, "RABBIT_MQ_PASSWORD", "guest")
    virtual_host = "notifications"

    exchange = "notification.send"
    exchange_type = "fanout"
    publishing_routing_key = ""
