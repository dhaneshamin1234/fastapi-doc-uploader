from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from app.models import DocumentMetadata, DocumentResponse
from app.database import get_database
from app.utils import *
from app.config import settings
from app.storage import put_object, remove_object
from pathlib import Path
from datetime import datetime
import os
import math

class DocumentService:
    
    @staticmethod
    async def create_document(file_content: bytes, filename: str, content_type: str) -> DocumentMetadata:
        """Create and store a new document"""
        
        # Validate file size
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Detect and validate MIME type
        mime_type = detect_mime_type(file_content, content_type)
        is_valid, error_msg = validate_file_type(filename, mime_type)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Generate document ID and save file (local for fallback)
        document_id = generate_document_id()
        file_path = save_file(document_id, filename, file_content)
        
        # Process file content
        processing_results = process_file_content(filename, file_content)
        
        # Create document metadata
        storage_bucket = None
        storage_key = None

        # Attempt to upload to object storage
        try:
            object_name = f"{document_id}/{filename}"
            put_object(object_name, file_content, mime_type)
            storage_bucket = settings.MINIO_BUCKET
            storage_key = object_name
        except Exception:
            # Proceed without object storage; rely on local file fallback
            storage_bucket = None
            storage_key = None

        document = DocumentMetadata(
            document_id=document_id,
            filename=filename,
            original_filename=filename,
            file_size=len(file_content),
            file_type=Path(filename).suffix.lower(),
            mime_type=mime_type,
            upload_timestamp=datetime.utcnow(),
            file_hash=calculate_file_hash(file_content),
            file_path=file_path,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            **processing_results
        )
        
        # Store in database
        db = await get_database()
        result = await db.documents.insert_one(document.dict(by_alias=True))
        document.id = result.inserted_id
        
        return document
    
    @staticmethod
    async def get_document(document_id: str) -> Optional[DocumentMetadata]:
        """Get document by ID"""
        db = await get_database()
        doc_data = await db.documents.find_one({"document_id": document_id})
        
        if doc_data:
            # Convert ObjectId to string for proper serialization
            if '_id' in doc_data:
                doc_data['_id'] = str(doc_data['_id'])
            return DocumentMetadata(**doc_data)
        return None
    
    @staticmethod
    async def list_documents(page: int = 1, per_page: int = 10) -> Tuple[List[DocumentMetadata], int]:
        """List documents with pagination"""
        db = await get_database()
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Get total count
        total = await db.documents.count_documents({})
        
        # Get documents
        cursor = db.documents.find({}).skip(skip).limit(per_page).sort("upload_timestamp", -1)
        documents = []
        
        async for doc_data in cursor:
            # Convert ObjectId to string for proper serialization
            if '_id' in doc_data:
                doc_data['_id'] = str(doc_data['_id'])
            documents.append(DocumentMetadata(**doc_data))
        
        return documents, total
    
    @staticmethod
    async def delete_document(document_id: str) -> bool:
        """Delete document"""
        db = await get_database()
        
        # Get document first to delete file
        document = await DocumentService.get_document(document_id)
        if not document:
            return False
        
        # Delete object from storage if present
        try:
            if document.storage_key:
                remove_object(document.storage_key)
        except Exception:
            pass

        # Delete file from disk (best-effort fallback)
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception:
            pass  # Continue even if file deletion fails
        
        # Delete from database
        result = await db.documents.delete_one({"document_id": document_id})
        return result.deleted_count > 0