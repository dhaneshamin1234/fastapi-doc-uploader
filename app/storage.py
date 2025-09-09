import logging
from typing import Optional
from minio import Minio
from minio.error import S3Error
from app.config import settings
from contextlib import asynccontextmanager
import io

logger = logging.getLogger(__name__)


class ObjectStorage:
    client: Optional[Minio] = None


storage = ObjectStorage()


def connect_to_storage():
    try:
        storage.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        # Ensure bucket exists
        if not storage.client.bucket_exists(settings.MINIO_BUCKET):
            storage.client.make_bucket(settings.MINIO_BUCKET)
            logger.info(f"Created bucket '{settings.MINIO_BUCKET}'")
        else:
            logger.info(f"Using bucket '{settings.MINIO_BUCKET}'")
    except Exception as exc:
        logger.error(f"Failed to connect to MinIO: {exc}")
        raise


def close_storage_connection():
    # Minio client doesn't maintain open sockets that need closing explicitly
    pass


def put_object(object_name: str, data: bytes, content_type: str) -> str:
    if not storage.client:
        raise RuntimeError("Storage client not initialized")
    try:
        data_stream = io.BytesIO(data)
        storage.client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            data_stream,
            length=len(data),
            content_type=content_type,
        )
        return object_name
    except S3Error as e:
        logger.error(f"MinIO put_object failed: {e}")
        raise


def get_object_stream(object_name: str):
    if not storage.client:
        raise RuntimeError("Storage client not initialized")
    try:
        return storage.client.get_object(settings.MINIO_BUCKET, object_name)
    except S3Error as e:
        logger.error(f"MinIO get_object failed: {e}")
        raise


def remove_object(object_name: str) -> bool:
    if not storage.client:
        raise RuntimeError("Storage client not initialized")
    try:
        storage.client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error as e:
        # If not found, treat as already removed
        if getattr(e, "code", "") in {"NoSuchKey", "NoSuchObject"}:
            return False
        logger.error(f"MinIO remove_object failed: {e}")
        raise


