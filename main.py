import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import *
from app.database import connect_to_mongo, close_mongo_connection, mongodb
from app.storage import connect_to_storage, close_storage_connection, get_object_stream
from app.services import DocumentService
from app.config import settings
from app.storage import storage
from app.messaging import connect_to_rabbitmq, close_rabbitmq_connection, publish_event
import math
import uvicorn

#test ci push

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    # Initialize MinIO
    connect_to_storage()
    # Initialize RabbitMQ
    try:
        connect_to_rabbitmq()
    except Exception:
        logger.warning("RabbitMQ connection failed; event publishing will be disabled until available")
    yield
    # Shutdown
    await close_mongo_connection()
    close_storage_connection()
    close_rabbitmq_connection()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description="RESTful API for uploading and managing documents (PDF, TXT, JSON) with MongoDB storage",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint - returns service status and dependencies
    """
    dependencies = {}
    
    # Check MongoDB connection
    try:
        if mongodb.client:
            await mongodb.client.admin.command('ping')
            dependencies["mongodb"] = "healthy"
        else:
            dependencies["mongodb"] = "disconnected"
    except Exception as e:
        dependencies["mongodb"] = f"error: {str(e)}"
    
    # Check upload directory
    dependencies["upload_directory"] = "healthy" if os.path.exists(settings.UPLOAD_DIR) else "missing"
    
    # Check MinIO
    try:
        if storage.client:
            # Attempt a simple list operation on the bucket to verify connectivity
            objects = storage.client.list_objects(settings.MINIO_BUCKET, recursive=True)
            next(objects, None)
            dependencies["minio"] = "healthy"
        else:
            dependencies["minio"] = "disconnected"
    except Exception as e:
        dependencies["minio"] = f"error: {str(e)}"
    
    # Overall status
    overall_status = "healthy" if all(
        dep in ["healthy", "connected"] for dep in dependencies.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.API_VERSION,
        dependencies=dependencies
    )

# Document Upload Endpoint
@app.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, TXT, or JSON)
    
    - **file**: The document file to upload
    
    Returns document metadata including unique ID and processing results
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Create document
        document = await DocumentService.create_document(
            file_content, file.filename, file.content_type
        )
        
        # Convert to response format
        doc_response = DocumentResponse(
            document_id=document.document_id,
            filename=document.filename,
            file_size=document.file_size,
            file_type=document.file_type,
            upload_timestamp=document.upload_timestamp,
            word_count=document.word_count,
            character_count=document.character_count,
            page_count=document.page_count,
            json_keys_count=document.json_keys_count,
            content_preview=document.content_preview
        )
        
        # Publish event (best-effort)
        try:
            publish_event(
                event_type="document.uploaded",
                payload={
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "mime_type": document.mime_type,
                    "storage_key": document.storage_key,
                    "bucket": document.storage_bucket,
                    "uploaded_at": document.upload_timestamp.isoformat(),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")
        
        return UploadResponse(
            success=True,
            message="Document uploaded and processed successfully",
            document=doc_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the file: {str(e)}"
        )

# Document Retrieval Endpoints
@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    List all documents with pagination
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 100)
    """
    try:
        documents, total = await DocumentService.list_documents(page, per_page)
        
        # Convert to response format
        doc_responses = [
            DocumentResponse(
                document_id=doc.document_id,
                filename=doc.filename,
                file_size=doc.file_size,
                file_type=doc.file_type,
                upload_timestamp=doc.upload_timestamp,
                word_count=doc.word_count,
                character_count=doc.character_count,
                page_count=doc.page_count,
                json_keys_count=doc.json_keys_count,
                content_preview=doc.content_preview
            )
            for doc in documents
        ]
        
        total_pages = math.ceil(total / per_page)
        
        return DocumentListResponse(
            success=True,
            documents=doc_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get specific document details by ID
    
    - **document_id**: The unique identifier of the document
    """
    document = await DocumentService.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        document_id=document.document_id,
        filename=document.filename,
        file_size=document.file_size,
        file_type=document.file_type,
        upload_timestamp=document.upload_timestamp,
        word_count=document.word_count,
        character_count=document.character_count,
        page_count=document.page_count,
        json_keys_count=document.json_keys_count,
        content_preview=document.content_preview
    )

@app.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """
    Download original file by document ID
    
    - **document_id**: The unique identifier of the document
    """
    document = await DocumentService.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # If using object storage, stream from MinIO; otherwise fall back to disk
    if document.storage_key:
        try:
            obj = get_object_stream(document.storage_key)
            return StreamingResponse(
                content=obj.stream(32 * 1024),
                media_type=document.mime_type,
                headers={
                    "Content-Disposition": f"attachment; filename=\"{document.original_filename}\""
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document object not found in storage: {str(e)}"
            )
    else:
        if not os.path.exists(document.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found on disk"
            )
        return FileResponse(
            path=document.file_path,
            filename=document.original_filename,
            media_type=document.mime_type
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
            detail=str(exc.detail) if exc.detail else None
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )