from celery import Celery
from app.config import settings
from kombu import Exchange, Queue

celery_app = Celery(
    "tasks",
    broker=settings.RABBITMQ_URL,
    backend="rpc://",  # Optional
)

celery_app.conf.task_queues = (
    Queue(
        name=settings.RABBITMQ_QUEUE,
        exchange=Exchange(settings.RABBITMQ_EXCHANGE, type='topic'),
        routing_key=settings.RABBITMQ_ROUTING_KEY,
        queue_arguments={
            "x-dead-letter-exchange": "dlx_exchange",
            "x-dead-letter-routing-key": "document.failed"
        }
    ),
)

celery_app.conf.task_routes = {
    'app.tasks.*': {'queue': settings.RABBITMQ_QUEUE},
}
