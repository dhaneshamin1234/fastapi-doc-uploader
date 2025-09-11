from app.celery_app import celery_app  # ✅ no circular import now
import logging
import time

logger = logging.getLogger("celery_task")

@celery_app.task(name="app.tasks.process_document")
def process_document(payload: dict):
    try:
        logger.info(f"Celery task received: {payload}")
        time.sleep(1)  # simulate work
        logger.info(f"Processed document {payload.get('document_id')}")
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise
