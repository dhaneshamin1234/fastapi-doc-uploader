import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "document_service")
    
    # File upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
    ALLOWED_EXTENSIONS: set = set(os.getenv("ALLOWED_EXTENSIONS", ".pdf,.txt,.json").split(","))
    
    # MIME types
    ALLOWED_MIME_TYPES: set = {
        'application/pdf',
        'text/plain',
        'application/json',
        'text/json'
    }
    
    # API
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Document Upload API"
    API_CONTACT: dict = {
        "name": os.getenv("API_CONTACT_NAME", "API Support"),
        "email": os.getenv("API_CONTACT_EMAIL", "support@example.com"),
    }
    API_LICENSE: dict = {
        "name": os.getenv("API_LICENSE_NAME", "MIT"),
        "url": os.getenv("API_LICENSE_URL", "https://opensource.org/licenses/MIT"),
    }

    # MinIO / S3-compatible storage
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "minio")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9001")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "documents")

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "document_events")
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "document_processing")
    RABBITMQ_ROUTING_KEY: str = os.getenv("RABBITMQ_ROUTING_KEY", "document.process")

    # Testing / Runtime toggles
    DISABLE_EXTERNAL_CONNECTIONS: bool = os.getenv("DISABLE_EXTERNAL_CONNECTIONS", "false").lower() == "true"
    LOG_REQUESTS: bool = os.getenv("LOG_REQUESTS", "true").lower() == "true"
    
    def __init__(self):
        # Ensure upload directory exists
        Path(self.UPLOAD_DIR).mkdir(exist_ok=True)

settings = Settings()