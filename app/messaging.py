import json
import logging
import pika
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    connection: Optional[pika.BlockingConnection] = None
    channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None


mq = RabbitMQClient()


def connect_to_rabbitmq():
    try:
        params = pika.URLParameters(settings.RABBITMQ_URL)
        mq.connection = pika.BlockingConnection(params)
        mq.channel = mq.connection.channel()
        # Declare exchange and queue, and bind
        mq.channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='topic', durable=True)
        mq.channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
        mq.channel.queue_bind(queue=settings.RABBITMQ_QUEUE, exchange=settings.RABBITMQ_EXCHANGE, routing_key=settings.RABBITMQ_ROUTING_KEY)
        logger.info("Connected to RabbitMQ and declared topology")
    except Exception as exc:
        logger.error(f"Failed to connect to RabbitMQ: {exc}")
        raise


def close_rabbitmq_connection():
    try:
        if mq.channel and mq.channel.is_open:
            mq.channel.close()
        if mq.connection and mq.connection.is_open:
            mq.connection.close()
    except Exception:
        pass


def publish_event(event_type: str, payload: dict):
    if not mq.channel or not mq.channel.is_open:
        raise RuntimeError("RabbitMQ channel not initialized")
    message = {
        "type": event_type,
        "payload": payload,
    }
    body = json.dumps(message).encode('utf-8')
    mq.channel.basic_publish(
        exchange=settings.RABBITMQ_EXCHANGE,
        routing_key=settings.RABBITMQ_ROUTING_KEY,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2  # persistent
        )
    )

