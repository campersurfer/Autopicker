#!/usr/bin/env python3
"""
Simple standalone API for VPS deployment
Minimal version with just essential functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import os
import uuid
import aiofiles
from pathlib import Path
import logging
import base64
from PIL import Image
import PyPDF2
from docx import Document
import openpyxl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multimodal LLM Platform API - Simple",
    description="Simplified API for VPS deployment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# File processing functions
def process_pdf(file_path: Path) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return f"Error processing PDF: {str(e)}"

def process_docx(file_path: Path) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing DOCX: {e}")
        return f"Error processing DOCX: {str(e)}"

def process_excel(file_path: Path) -> str:
    """Extract text from Excel file"""
    try:
        workbook = openpyxl.load_workbook(file_path)
        text = ""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"Sheet: {sheet_name}\n"
            for row in sheet.iter_rows(values_only=True):
                row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    text += row_text + "\n"
            text += "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing Excel: {e}")
        return f"Error processing Excel: {str(e)}"

def process_image(file_path: Path) -> Dict[str, Any]:
    """Process image file and return metadata"""
    try:
        with Image.open(file_path) as img:
            # Convert image to base64 for potential future use
            import io
            buffered = io.BytesIO()
            img.save(buffered, format=img.format or "PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "type": "image",
                "size": img.size,
                "mode": img.mode,
                "format": img.format,
                "description": f"Image: {img.size[0]}x{img.size[1]} pixels, {img.mode} mode",
                "base64": img_base64[:100] + "..." if len(img_base64) > 100 else img_base64  # Truncated for preview
            }
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return {"type": "image", "error": str(e)}

def process_text(file_path: Path) -> str:
    """Process text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error processing text file: {e}")
        return f"Error processing text file: {str(e)}"

def get_file_content(file_path: Path) -> Dict[str, Any]:
    """Process any supported file type"""
    suffix = file_path.suffix.lower()
    
    if suffix == '.pdf':
        content = process_pdf(file_path)
        return {"type": "pdf", "content": content}
    elif suffix == '.docx':
        content = process_docx(file_path)
        return {"type": "docx", "content": content}
    elif suffix in ['.xlsx', '.xls']:
        content = process_excel(file_path)
        return {"type": "excel", "content": content}
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        content = process_image(file_path)
        return content
    elif suffix in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css']:
        content = process_text(file_path)
        return {"type": "text", "content": content}
    else:
        return {"type": "unknown", "error": f"Unsupported file type: {suffix}"}

# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama3.2-local"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    mime_type: str
    content_preview: Optional[str] = None
    file_type: Optional[str] = None

class MultimodalRequest(BaseModel):
    messages: List[ChatMessage]
    file_ids: Optional[List[str]] = []
    model: Optional[str] = "llama3.2-local"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multimodal-llm-platform-simple"}

# Test Ollama endpoint
@app.get("/test-ollama")
async def test_ollama():
    """Test connection to local Ollama"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                return {
                    "status": "success",
                    "ollama_connected": True,
                    "available_models": models.get("models", [])
                }
            else:
                return {
                    "status": "error", 
                    "ollama_connected": False,
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "error",
            "ollama_connected": False, 
            "error": str(e)
        }

# Chat with local Ollama
@app.post("/api/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    """Chat completion using local Ollama"""
    try:
        # Convert to Ollama format
        payload = {
            "model": "llama3.2:1b",  # Use the actual model name
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": False
        }
        
        logger.info(f"Sending request to Ollama: {request.model}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama error: {response.text}"
                )
            
            result = response.json()
            
            # Convert Ollama response to OpenAI format
            openai_response = {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("message", {}).get("content", "")
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
            }
            
            logger.info(f"Successfully processed request with Ollama")
            return openai_response
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ollama is not available. Please ensure it's running."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multimodal chat endpoint
@app.post("/api/v1/chat/multimodal")
async def multimodal_chat(request: MultimodalRequest):
    """Chat completion with file support"""
    try:
        # Build the context with file contents
        context_messages = []
        
        # Add file contents to context if provided
        if request.file_ids:
            file_context = "=== Attached Files ===\n"
            for file_id in request.file_ids:
                # Find the file
                file_found = False
                for file_path in UPLOAD_DIR.iterdir():
                    if file_path.stem == file_id:
                        file_content = get_file_content(file_path)
                        file_type = file_content.get("type", "unknown")
                        
                        if file_type in ["pdf", "docx", "text", "excel"]:
                            file_context += f"\nFile: {file_path.name}\nType: {file_type}\nContent:\n{file_content.get('content', 'No content available')}\n\n"
                        elif file_type == "image":
                            file_context += f"\nFile: {file_path.name}\nType: Image\nDescription: {file_content.get('description', 'Image file')}\n\n"
                        else:
                            file_context += f"\nFile: {file_path.name}\nType: {file_type}\nNote: This file type is not fully processed but was uploaded successfully.\n\n"
                        
                        file_found = True
                        break
                
                if not file_found:
                    file_context += f"\nFile ID {file_id} not found.\n"
            
            # Add file context as a system message
            context_messages.append({
                "role": "system", 
                "content": f"You are analyzing the following files. Use this information to answer the user's questions:\n\n{file_context}"
            })
        
        # Add the user's messages
        for msg in request.messages:
            context_messages.append({"role": msg.role, "content": msg.content})
        
        # Convert to Ollama format
        payload = {
            "model": "llama3.2:1b",
            "messages": context_messages,
            "stream": False
        }
        
        logger.info(f"Sending multimodal request to Ollama with {len(request.file_ids)} files")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama error: {response.text}"
                )
            
            result = response.json()
            
            # Convert Ollama response to OpenAI format
            openai_response = {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("message", {}).get("content", "")
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                "files_processed": len(request.file_ids) if request.file_ids else 0
            }
            
            logger.info(f"Successfully processed multimodal request with {len(request.file_ids)} files")
            return openai_response
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ollama is not available. Please ensure it's running."
        )
    except Exception as e:
        logger.error(f"Unexpected error in multimodal chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File upload
@app.post("/api/v1/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and save files with content processing"""
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ""
        stored_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Get file size
        file_size = len(content)
        
        # Process file content
        file_content = get_file_content(file_path)
        content_preview = None
        file_type = file_content.get("type", "unknown")
        
        # Create preview based on file type
        if file_type in ["pdf", "docx", "text"]:
            content_preview = file_content.get("content", "")[:200] + "..." if len(file_content.get("content", "")) > 200 else file_content.get("content", "")
        elif file_type == "image":
            content_preview = file_content.get("description", "Image file")
        elif file_type == "excel":
            content_preview = file_content.get("content", "")[:200] + "..." if len(file_content.get("content", "")) > 200 else file_content.get("content", "")
        
        logger.info(f"File uploaded and processed: {file.filename} -> {stored_filename} ({file_size} bytes, type: {file_type})")
        
        return FileUploadResponse(
            id=file_id,
            filename=stored_filename,
            original_filename=file.filename or "unknown",
            size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            content_preview=content_preview,
            file_type=file_type
        )
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# List files
@app.get("/api/v1/files")
async def list_files():
    """List all uploaded files"""
    try:
        files = []
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "path": str(file_path)
                })
        
        return {"files": files, "count": len(files)}
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get available models
@app.get("/api/v1/models")
async def get_models():
    """Get list of available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                ollama_models = response.json()
                # Convert to OpenAI format
                models = []
                for model in ollama_models.get("models", []):
                    models.append({
                        "id": model.get("name", ""),
                        "object": "model",
                        "created": 0,
                        "owned_by": "local-ollama"
                    })
                
                return {
                    "object": "list",
                    "data": models
                }
            else:
                # Return default if Ollama not available
                return {
                    "object": "list",
                    "data": [
                        {"id": "llama3.2-local", "object": "model", "owned_by": "local-ollama"}
                    ]
                }
            
    except Exception as e:
        logger.error(f"Models endpoint error: {e}")
        # Return default models on error
        return {
            "object": "list",
            "data": [
                {"id": "llama3.2-local", "object": "model", "owned_by": "local-ollama"}
            ]
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Multimodal LLM Platform API - Simple",
        "version": "1.0.0",
        "description": "Simplified API for VPS deployment with Ollama integration",
        "endpoints": {
            "health": "/health",
            "test_ollama": "/test-ollama",
            "chat": "/api/v1/chat/completions",
            "multimodal_chat": "/api/v1/chat/multimodal",
            "upload": "/api/v1/upload",
            "files": "/api/v1/files",
            "models": "/api/v1/models"
        },
        "supported_file_types": {
            "documents": ["pdf", "docx", "txt", "md"],
            "spreadsheets": ["xlsx", "xls", "csv"],
            "images": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            "code": ["py", "js", "html", "css", "json"]
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)