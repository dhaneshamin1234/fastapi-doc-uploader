# fastapi-doc-uploader

A FastAPI-based document uploading service using MongoDB, MinIO, and RabbitMQ for scalable file processing and storage.

## Features

- Upload documents through REST APIs
- Store metadata in MongoDB
- Store files in MinIO (S3-compatible object storage)
- Asynchronous processing with RabbitMQ message broker
- Dockerized for easy deployment

## Tech Stack

- FastAPI
- MongoDB
- MinIO
- RabbitMQ
- Python 3.12

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12

### Running the app locally

1. Clone the repo:

```bash
git clone https://github.com/your-username/fastapi-doc-uploader.git
cd fastapi-doc-uploader
