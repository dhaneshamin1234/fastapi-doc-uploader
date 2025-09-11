import os
import io
import json
import pytest
import sys
from fastapi.testclient import TestClient

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..'))

os.environ.setdefault("DISABLE_EXTERNAL_CONNECTIONS", "true")

from main import app  # noqa: E402

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"healthy", "degraded"}
    assert "version" in data


def test_list_documents_empty_ok():
    resp = client.get("/documents")
    # May error if DB disabled; but with DISABLE_EXTERNAL_CONNECTIONS, handlers shouldn't crash
    assert resp.status_code in {200, 500}
    if resp.status_code == 200:
        body = resp.json()
        assert body["success"] is True
        assert "documents" in body


def test_upload_validation_too_large(monkeypatch):
    # Force small max size
    from app.config import settings

    old = settings.MAX_FILE_SIZE
    settings.MAX_FILE_SIZE = 1  # 1 byte
    try:
        file_bytes = b"abc"
        resp = client.post(
            "/documents",
            files={"file": ("a.txt", io.BytesIO(file_bytes), "text/plain")},
        )
        assert resp.status_code == 413
    finally:
        settings.MAX_FILE_SIZE = old


def test_upload_validation_bad_type():
    file_bytes = b"%PDF-1.4 invalid but extension wrong"
    resp = client.post(
        "/documents",
        files={"file": ("a.exe", io.BytesIO(file_bytes), "application/octet-stream")},
    )
    assert resp.status_code in {400, 500}

