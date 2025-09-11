import json
import logging
import aio_pika
from typing import Optional
from app.config import settings
from aio_pika import Message, DeliveryMode, ExchangeType

logger = logging.getLogger(__name__)


class AioRabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            name=settings.RABBITMQ_EXCHANGE,
            type=ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("Connected to RabbitMQ (aio_pika)")

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def publish_event(self, event_type: str, payload: dict):
        if not self.exchange:
            raise RuntimeError("RabbitMQ exchange not initialized")

        message = Message(
            body=json.dumps({
                "type": event_type,
                "payload": payload
            }).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(
            message,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
        )

rabbitmq_publisher = AioRabbitMQPublisher()

