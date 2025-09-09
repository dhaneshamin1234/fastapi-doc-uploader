import json
import logging
import time
import pika
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


def main():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='topic', durable=True)
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
    channel.queue_bind(queue=settings.RABBITMQ_QUEUE, exchange=settings.RABBITMQ_EXCHANGE, routing_key=settings.RABBITMQ_ROUTING_KEY)

    logger.info("Worker started; waiting for messages...")

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            event_type = message.get("type")
            payload = message.get("payload", {})
            logger.info(f"Received event: {event_type} payload={payload}")

            # Simulate processing work
            time.sleep(0.5)
            logger.info(f"Processed document_id={payload.get('document_id')} status=completed")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            logger.error(f"Processing failed: {exc}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=settings.RABBITMQ_QUEUE, on_message_callback=callback)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()


