from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from bson import ObjectId

from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler
    ) -> JsonSchemaValue:
        return {"type": "string", "example": "507f1f77bcf86cd799439011"}

class DocumentMetadata(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    document_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: str
    upload_timestamp: datetime
    file_hash: str
    file_path: str
    # Object storage
    storage_bucket: Optional[str] = None
    storage_key: Optional[str] = None
    
    # Processing results
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    page_count: Optional[int] = None
    json_keys_count: Optional[int] = None
    json_structure_valid: Optional[bool] = None
    content_preview: Optional[str] = None

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "_id" in data and isinstance(data["_id"], ObjectId):
            data["_id"] = str(data["_id"])
        return data

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    file_type: str
    upload_timestamp: datetime
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    page_count: Optional[int] = None
    json_keys_count: Optional[int] = None
    content_preview: Optional[str] = None
    # Expose storage info if needed in future (kept internal for now)

class UploadResponse(BaseModel):
    success: bool
    message: str
    document: DocumentResponse

class DocumentListResponse(BaseModel):
    success: bool
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class ErrorResponse(BaseModel):
    success: bool
    error: str
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    dependencies: dict