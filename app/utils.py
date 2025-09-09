import os
import uuid
import json
import hashlib
import magic
from datetime import datetime
from typing import Dict, Any, Tuple
from pathlib import Path
from io import BytesIO
import PyPDF2
from app.config import settings

def generate_document_id() -> str:
    """Generate a unique document ID using UUID4"""
    return str(uuid.uuid4())

def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def validate_file_type(filename: str, mime_type: str) -> Tuple[bool, str]:
    """
    Validate file type based on extension and MIME type
    Returns (is_valid, error_message)
    """
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"File extension {file_ext} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    if mime_type not in settings.ALLOWED_MIME_TYPES:
        return False, f"MIME type {mime_type} not allowed"
    
    return True, ""

def detect_mime_type(file_content: bytes, fallback: str = None) -> str:
    """Detect MIME type of file content"""
    try:
        return magic.from_buffer(file_content, mime=True)
    except:
        return fallback or 'application/octet-stream'

def save_file(document_id: str, filename: str, file_content: bytes) -> str:
    """Save file to disk and return file path"""
    safe_filename = f"{document_id}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

def process_pdf_file(file_content: bytes) -> Dict[str, Any]:
    """Process PDF file and extract metadata"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        page_count = len(pdf_reader.pages)
        
        # Extract text for preview and word count
        full_text = ""
        for page in pdf_reader.pages[:3]:  # First 3 pages for preview
            full_text += page.extract_text()
        
        # Create preview
        preview = full_text[:300] + "..." if len(full_text) > 300 else full_text
        preview = preview.strip() or "No readable text found"
        
        # Count words and characters
        words = full_text.split()
        word_count = len(words)
        character_count = len(full_text)
        
        return {
            "page_count": page_count,
            "word_count": word_count,
            "character_count": character_count,
            "content_preview": preview
        }
    except Exception as e:
        return {
            "page_count": 0,
            "word_count": 0,
            "character_count": 0,
            "content_preview": f"Error processing PDF: {str(e)}"
        }

def process_text_file(file_content: bytes) -> Dict[str, Any]:
    """Process text file and extract metadata"""
    try:
        text_content = file_content.decode('utf-8')
        
        # Count words and characters
        word_count = len(text_content.split())
        character_count = len(text_content)
        
        # Create preview
        preview = text_content[:300] + "..." if len(text_content) > 300 else text_content
        
        return {
            "word_count": word_count,
            "character_count": character_count,
            "content_preview": preview.strip()
        }
    except UnicodeDecodeError:
        return {
            "word_count": 0,
            "character_count": 0,
            "content_preview": "Error: Unable to decode text file"
        }

def process_json_file(file_content: bytes) -> Dict[str, Any]:
    """Process JSON file and extract metadata"""
    try:
        json_data = json.loads(file_content.decode('utf-8'))
        
        # Count keys if it's an object
        keys_count = None
        structure_valid = True
        
        if isinstance(json_data, dict):
            keys_count = len(json_data.keys())
            preview = f"JSON object with {keys_count} keys: {', '.join(list(json_data.keys())[:5])}"
            if keys_count > 5:
                preview += f" and {keys_count - 5} more..."
        elif isinstance(json_data, list):
            preview = f"JSON array with {len(json_data)} items"
            if len(json_data) > 0 and isinstance(json_data[0], dict):
                keys_count = len(json_data[0].keys()) if json_data[0] else 0
        else:
            preview = f"JSON value: {str(json_data)[:200]}..."
        
        return {
            "json_keys_count": keys_count,
            "json_structure_valid": structure_valid,
            "content_preview": preview
        }
    except json.JSONDecodeError:
        return {
            "json_keys_count": None,
            "json_structure_valid": False,
            "content_preview": "Error: Invalid JSON format"
        }

def process_file_content(filename: str, file_content: bytes) -> Dict[str, Any]:
    """Process file content based on file type"""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext == '.pdf':
        return process_pdf_file(file_content)
    elif file_ext == '.txt':
        return process_text_file(file_content)
    elif file_ext == '.json':
        return process_json_file(file_content)
    else:
        return {"content_preview": "Unsupported file type"}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"