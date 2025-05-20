import json
import time
import pika
import logging

from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)


class BaseRabbitMQ:
    host = None
    port = None
    virtual_host = None
    username = None
    password = None

    # для publishing
    exchange = None
    exchange_type = None
    publishing_routing_key = None

    # для consuming
    queue = None
    requeue_on_fail = True
    consuming_routing_key = None

    # для dead letter queue
    dlq_exchange = None
    dlq_queue = None
    dlq_routing_key = None

    # для retry queue
    retry_exchange = None
    retry_queue = None
    retry_routing_key = None

    # для правильного соединение
    heartbeat = 600  # sec
    blocked_connection_timeout = 10  # sec
    socket_timeout = 5  # sec
    consuming_retry_after = 5  # sec

    # для прочих моментов
    durable = True
    retry_ttl = 10000  # ms
    retry_max_count = 3

    _connection = None
    _channel = None
    _topology_declared = False

    @classmethod
    def _connect(cls):
        try:
            params = pika.ConnectionParameters(
                host=cls.host,
                port=cls.port,
                virtual_host=cls.virtual_host,
                credentials=pika.PlainCredentials(
                    username=cls.username,
                    password=cls.password,
                ),
                heartbeat=cls.heartbeat,
                blocked_connection_timeout=cls.blocked_connection_timeout,
                socket_timeout=cls.socket_timeout,
            )

            cls._connection = pika.BlockingConnection(params)
            cls._channel = cls._connection.channel()

            cls._channel.basic_qos(prefetch_count=1)
            cls._channel.confirm_delivery()

            cls._declare_topology() if not cls._topology_declared else None
        except Exception as exc:
            logger.critical(f"[RabbitMQ] Не удалось соединиться: {exc}", exc_info=True)
            cls._connection = None
            cls._channel = None

    @classmethod
    def _declare_topology(cls):
        if not cls.host or not cls.port or not cls.virtual_host or not cls.username or not cls.password:
            raise ValueError("Host, port, virtual_host, username, password обязательны")

        if not cls.exchange or not cls.exchange_type:
            raise ValueError("Exchange, exchange type обязательны")

        if cls.exchange_type == "fanout" and cls.publishing_routing_key:
            raise ValueError('Routing key должен быть пустым строкой "" если exchange type "fanout"')
        elif cls.exchange_type != "fanout" and not cls.publishing_routing_key:
            raise ValueError('Routing key обязателен если exchange type НЕ "fanout"')

        required_dlq_list = [cls.dlq_exchange, cls.dlq_queue, cls.dlq_routing_key]
        if any(required_dlq_list) and not all(required_dlq_list):
            raise ValueError("Dead Letter's Exchange, Queue, Routing Key обязательны вместе")

        required_retry_list = [cls.retry_exchange, cls.retry_queue, cls.retry_routing_key]
        if any(required_retry_list) and not all(required_retry_list):
            raise ValueError("Retry's Exchange, Queue, Routing Key обязательны вместе")

        cls._channel.exchange_declare(
            exchange=cls.exchange,
            exchange_type=cls.exchange_type,
            durable=cls.durable
        )

        if cls.queue and cls.consuming_routing_key:
            if cls.dlq_exchange:
                cls._channel.exchange_declare(cls.dlq_exchange, exchange_type='direct', durable=cls.durable)
                cls._channel.queue_declare(cls.dlq_queue, durable=cls.durable)
                cls._channel.queue_bind(exchange=cls.dlq_exchange, queue=cls.dlq_queue, routing_key=cls.dlq_routing_key)

            if cls.retry_exchange:
                cls._channel.exchange_declare(cls.retry_exchange, exchange_type='direct', durable=cls.durable)
                cls._channel.queue_declare(
                    cls.retry_queue,
                    durable=cls.durable,
                    arguments={
                        'x-dead-letter-exchange': cls.exchange,
                        'x-dead-letter-routing-key': cls.consuming_routing_key,
                        'x-message-ttl': cls.retry_ttl,
                    }
                )
                cls._channel.queue_bind(
                    exchange=cls.retry_exchange,
                    queue=cls.retry_queue,
                    routing_key=cls.retry_routing_key
                )

            dlq_exchange = (
                cls.retry_exchange if cls.retry_exchange
                else cls.dlq_exchange if cls.dlq_exchange
                else None
            )
            dlq_routing_key = (
                cls.retry_routing_key if cls.retry_routing_key
                else cls.dlq_routing_key if cls.dlq_routing_key
                else None
            )

            cls._channel.queue_declare(
                queue=cls.queue,
                durable=cls.durable,
                arguments={
                    'x-dead-letter-exchange': dlq_exchange,
                    'x-dead-letter-routing-key': dlq_routing_key
                } if dlq_exchange else None
            )
            cls._channel.queue_bind(
                exchange=cls.exchange,
                queue=cls.queue,
                routing_key=cls.consuming_routing_key
            )

        cls._topology_declared = True

    @classmethod
    def _get_channel(cls):
        connection_closed = (
                getattr(cls._connection, "is_closed", True)
                or not getattr(cls._connection, "is_open", False)
        )
        channel_closed = (
                getattr(cls._channel, "is_closed", True)
                or not getattr(cls._channel, "is_open", False)
        )

        if connection_closed or channel_closed:
            cls._connect()

        return cls._channel

    @classmethod
    def _safe_raise_exception(cls, msg, exc, saga_func, saga_args, raise_exception):
        logger.critical(f"[RabbitMQ] {msg}: {exc}", exc_info=True)

        if saga_func and saga_args:
            try:
                saga_func(*saga_args, exc=exc)
            except Exception as e:
                logger.critical(f"[SAGA] Ошибка при выполнений {saga_func.__name__}: {e}", exc_info=True)
                raise e

        if not raise_exception:
            return

        raise exc

    @classmethod
    def publish(cls, idempotency_key, payload, saga_func=None, saga_args=None, raise_exception=True):
        channel = cls._get_channel()

        if not channel:
            exc = RuntimeError("Канал не доступен")
            cls._safe_raise_exception("Не удалось соединиться", exc, saga_func, saga_args, raise_exception)

        try:
            channel.basic_publish(
                exchange=cls.exchange,
                routing_key=cls.publishing_routing_key,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="application/json",
                    headers={
                        "Idempotency-Key": idempotency_key
                    }
                )
            )

        except (AMQPConnectionError, ChannelClosedByBroker) as exc:
            cls._connection = None
            cls._channel = None

            cls._safe_raise_exception("Соединение прервано", exc, saga_func, saga_args, raise_exception)

        except Exception as exc:
            cls._safe_raise_exception("Не удалось опубликовать сообщение", exc, saga_func, saga_args, raise_exception)

    @classmethod
    def consume(cls, callback, is_dlq=False):
        queue = cls.dlq_queue if is_dlq else cls.queue
        retry_exchange = None if is_dlq else cls.retry_exchange
        dlq_exchange = None if is_dlq else cls.dlq_exchange
        requeue_on_fail = True if is_dlq else cls.requeue_on_fail

        if not queue or not cls.consuming_routing_key:
            raise ValueError("Queue и consuming routing key обязательны")

        def _dlq_publish(ch, method, body, properties):
            try:
                ch.basic_publish(
                    exchange=cls.dlq_exchange,
                    routing_key=cls.dlq_routing_key,
                    body=body,
                    properties=pika.BasicProperties(
                        headers=properties.headers,
                        delivery_mode=pika.DeliveryMode.Persistent,
                        content_type="application/json"
                    )
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.critical(f"[RabbitMQ] Не удалось опубликовать в DLQ: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        def _callback(ch, method, properties, body):
            try:
                data = json.loads(body)
                callback(data, idempotency_path=cls.queue, idempotency_key=properties.headers.get("Idempotency-Key"))
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.critical(f"[RabbitMQ] Неизвестная ошибка при обработка сообщений: {e}", exc_info=True)

                if retry_exchange:
                    headers = properties.headers or {}
                    attempts = headers.get("x-death", [])
                    retry_count = 0

                    for i in attempts:
                        if i.get("exchange") == cls.retry_exchange and i.get("queue") == cls.retry_queue:
                            retry_count = i.get("count", 0)
                            break

                    if cls.dlq_exchange and retry_count >= cls.retry_max_count:
                        _dlq_publish(ch, method, body, properties)
                    else:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                elif dlq_exchange:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                elif requeue_on_fail:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                else:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

        while True:
            try:
                channel = cls._get_channel()

                if not channel:
                    raise RuntimeError("[RabbitMQ] Канал не доступен")

                channel.basic_consume(
                    queue=queue,
                    on_message_callback=_callback,
                    auto_ack=False,
                    consumer_tag=f"{queue}.consumer"
                )

                logger.info("[RabbitMQ] Начинаем обрабатывать сообщении...")
                channel.start_consuming()

            except KeyboardInterrupt:
                logger.info("[RabbitMQ] Обработка сообщении остановлено")
                break

            except (AMQPConnectionError, ChannelClosedByBroker, RuntimeError) as exc:
                logger.critical(f"[RabbitMQ] Не удалось соединиться: {exc}. Retrying...", exc_info=True)
                time.sleep(cls.consuming_retry_after)

            except Exception as exc:
                logger.critical(f"[RabbitMQ] Consumer остановился из-за ошибки: {exc}", exc_info=True)
                time.sleep(cls.consuming_retry_after)

    @classmethod
    def _dlq_callback(cls, data, idempotency_key, idempotency_path=None):
        cls.publish(idempotency_key, data)

    @classmethod
    def consume_dlq(cls):
        cls.consume(cls._dlq_callback, is_dlq=True)
