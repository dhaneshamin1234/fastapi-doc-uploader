# Document Processing Service

FastAPI-based document service with MongoDB, MinIO, and RabbitMQ. Supports upload, metadata extraction, storage, and async processing.

## Features

- Upload documents through REST APIs
- Store metadata in MongoDB
- Store files in MinIO (S3-compatible object storage)
- Asynchronous processing with RabbitMQ + Celery
- Dockerized for easy deployment
- OpenAPI docs at `/docs` and `/redoc`

## Tech Stack

- FastAPI
- MongoDB (Motor)
- MinIO
- RabbitMQ + Celery
- Python 3.12

## Configuration

Environment variables (see `.env` example):

```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=document_service
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=.pdf,.txt,.json
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9001
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=documents
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=document_events
RABBITMQ_QUEUE=document_processing
RABBITMQ_ROUTING_KEY=document.process
DISABLE_EXTERNAL_CONNECTIONS=false
LOG_REQUESTS=true
```

## Running locally

### With Docker Compose

```bash
docker compose up --build
```

The API runs on `http://localhost:8000`. Open docs at `http://localhost:8000/docs`.

### Without Docker

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

To run the Celery worker:

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

To run with external dependencies disabled (for tests/local offline):

```bash
export DISABLE_EXTERNAL_CONNECTIONS=true  # Windows: set DISABLE_EXTERNAL_CONNECTIONS=true
uvicorn main:app --reload
```

## API

- `GET /health` – Service health and dependency statuses
- `POST /documents` – Upload file (pdf, txt, json)
- `GET /documents` – List documents (pagination via `page`, `per_page`)
- `GET /documents/{id}` – Get document metadata
- `GET /documents/{id}/download` – Download original file

OpenAPI: `/docs` (Swagger UI), `/redoc` (ReDoc)

## Development

- Linting: follow PEP 8, add docstrings for public functions
- Logging: enabled by default; disable by setting `LOG_REQUESTS=false`

## Testing

Install test deps (already in `requirements.txt`): `pytest`, `pytest-asyncio`, `anyio`.

Run tests with external connections disabled:

```bash
set DISABLE_EXTERNAL_CONNECTIONS=true  # PowerShell: $env:DISABLE_EXTERNAL_CONNECTIONS='true'
pytest -q
```

## License

MIT
