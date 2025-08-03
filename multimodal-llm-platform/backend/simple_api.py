#!/usr/bin/env python3
"""
Simple standalone API for VPS deployment
Minimal version with just essential functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncGenerator
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
import asyncio

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

async def process_audio(file_path: Path) -> Dict[str, Any]:
    """Process audio file and return transcription"""
    try:
        logger.info(f"Processing audio file: {file_path}")
        
        # Prepare file for Whisper API
        async with aiofiles.open(file_path, 'rb') as audio_file:
            files = {'audio': await audio_file.read()}
        
        # Send to Whisper service
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:9002/asr",
                files={'audio': files['audio']},
                params={'output': 'json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get('text', '').strip()
                
                return {
                    "type": "audio",
                    "transcription": transcription,
                    "language": result.get('language', 'unknown'),
                    "duration": result.get('duration', 0),
                    "content": transcription  # For compatibility with text processing
                }
            else:
                logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                return {
                    "type": "audio", 
                    "error": f"Transcription failed: {response.status_code}",
                    "fallback": f"Audio file ({file_path.suffix}) uploaded but transcription unavailable"
                }
                
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {
            "type": "audio", 
            "error": str(e),
            "fallback": f"Audio file ({file_path.suffix}) uploaded but processing failed"
        }

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
    elif suffix in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
        # Audio files need async processing, return placeholder for now
        return {"type": "audio", "content": "Audio file uploaded, use transcription endpoint"}
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
    stream: Optional[bool] = False

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
    model: Optional[str] = "auto"  # Changed default to "auto" for smart routing
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ModelSelector:
    """Smart routing logic for model selection based on request complexity"""
    
    def __init__(self):
        # Available models and their capabilities
        self.models = {
            "llama3.2:1b": {
                "type": "text",
                "max_context": 2048,
                "complexity_score": 1,
                "best_for": ["simple_text", "basic_chat", "small_files"]
            }
            # We can add more models here as we deploy them
        }
    
    def calculate_complexity_score(self, request: MultimodalRequest, file_info: List[Dict] = None) -> float:
        """Calculate complexity score for the request"""
        complexity_score = 0.0
        
        # Message complexity
        total_message_length = sum(len(msg.content) for msg in request.messages)
        if total_message_length > 2000:
            complexity_score += 30
        elif total_message_length > 500:
            complexity_score += 15
        
        # File complexity
        if file_info:
            for file_data in file_info:
                file_type = file_data.get("type", "unknown")
                
                if file_type == "pdf":
                    complexity_score += 25  # PDFs can be complex
                elif file_type == "excel":
                    complexity_score += 20  # Excel files often have complex data
                elif file_type == "audio":
                    complexity_score += 30  # Audio transcription adds complexity
                elif file_type == "image":
                    complexity_score += 35  # Images require vision capabilities
                elif file_type in ["docx", "text"]:
                    complexity_score += 10  # Text files are simpler
                
                # File size factor
                file_size = file_data.get("size", 0)
                if file_size > 1000000:  # > 1MB
                    complexity_score += 20
                elif file_size > 100000:  # > 100KB
                    complexity_score += 10
        
        # Multiple files increase complexity
        if file_info and len(file_info) > 1:
            complexity_score += len(file_info) * 5
        
        # Request type complexity
        if request.file_ids and len(request.file_ids) > 0:
            complexity_score += 15  # Multimodal requests are more complex
        
        return min(complexity_score, 100.0)  # Cap at 100
    
    def select_model(self, request: MultimodalRequest, file_info: List[Dict] = None) -> str:
        """Select the best model for the given request"""
        
        # If user explicitly specified a model (not "auto"), use it
        if request.model and request.model != "auto":
            if request.model == "llama3.2-local":
                return "llama3.2:1b"
            return request.model
        
        # Calculate complexity
        complexity_score = self.calculate_complexity_score(request, file_info)
        
        # For now, we only have one model, but this logic can be extended
        # When we add more models, we can route based on complexity:
        
        # if complexity_score < 30:
        #     return "llama3.2:1b"  # Simple requests
        # elif complexity_score < 60:
        #     return "llama3.2:3b"  # Medium complexity
        # else:
        #     return "gpt-4"  # Complex requests (external API)
        
        # For now, always return our available model
        selected_model = "llama3.2:1b"
        
        logger.info(f"Smart routing: complexity_score={complexity_score:.1f}, selected_model={selected_model}")
        return selected_model

# Initialize model selector
model_selector = ModelSelector()

# Streaming helper functions
async def stream_ollama_response(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Stream response from Ollama API"""
    try:
        # Add streaming to payload
        payload["stream"] = True
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", "http://localhost:11434/api/chat", json=payload) as response:
                if response.status_code != 200:
                    logger.error(f"Ollama streaming error: {response.status_code}")
                    yield f"data: {json.dumps({'error': f'Ollama error: {response.status_code}'})}\n\n"
                    return
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        try:
                            # Parse each JSON line from Ollama
                            for line in chunk.strip().split('\n'):
                                if line:
                                    ollama_response = json.loads(line)
                                    
                                    # Convert Ollama streaming format to OpenAI format
                                    if "message" in ollama_response and "content" in ollama_response["message"]:
                                        content = ollama_response["message"]["content"]
                                        
                                        openai_chunk = {
                                            "id": str(uuid.uuid4()),
                                            "object": "chat.completion.chunk",
                                            "model": payload.get("model", "llama3.2:1b"),
                                            "choices": [{
                                                "index": 0,
                                                "delta": {"content": content},
                                                "finish_reason": None
                                            }]
                                        }
                                        
                                        yield f"data: {json.dumps(openai_chunk)}\n\n"
                                    
                                    # Check if this is the final chunk
                                    if ollama_response.get("done", False):
                                        final_chunk = {
                                            "id": str(uuid.uuid4()),
                                            "object": "chat.completion.chunk",
                                            "model": payload.get("model", "llama3.2:1b"),
                                            "choices": [{
                                                "index": 0,
                                                "delta": {},
                                                "finish_reason": "stop"
                                            }]
                                        }
                                        yield f"data: {json.dumps(final_chunk)}\n\n"
                                        yield "data: [DONE]\n\n"
                                        return
                                        
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error in streaming: {e}")
                            continue
                            
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

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
            "stream": request.stream
        }
        
        # Return streaming response if requested
        if request.stream:
            logger.info(f"Streaming chat completion request: {request.model}")
            return StreamingResponse(
                stream_ollama_response(payload),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        
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
        
        # Collect file information for smart routing
        file_info = []
        
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
                        
                        # Collect file info for routing
                        file_info.append({
                            "type": file_type,
                            "size": file_path.stat().st_size,
                            "name": file_path.name
                        })
                        
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
        
        # Smart model selection
        selected_model = model_selector.select_model(request, file_info)
        
        # Convert to Ollama format
        payload = {
            "model": selected_model,
            "messages": context_messages,
            "stream": request.stream
        }
        
        # Return streaming response if requested
        if request.stream:
            logger.info(f"Streaming multimodal request to Ollama with {len(request.file_ids)} files using model {selected_model}")
            return StreamingResponse(
                stream_ollama_response(payload),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        
        logger.info(f"Sending multimodal request to Ollama with {len(request.file_ids)} files using model {selected_model}")
        
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

# Audio transcription endpoint
@app.post("/api/v1/transcribe/{file_id}")
async def transcribe_audio(file_id: str):
    """Transcribe an uploaded audio file"""
    try:
        # Find the audio file
        audio_file_path = None
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.stem == file_id:
                # Check if it's an audio file
                if file_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                    audio_file_path = file_path
                    break
                else:
                    raise HTTPException(status_code=400, detail=f"File {file_id} is not an audio file")
        
        if not audio_file_path:
            raise HTTPException(status_code=404, detail=f"Audio file {file_id} not found")
        
        # Process the audio file
        result = await process_audio(audio_file_path)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"Successfully transcribed audio file: {audio_file_path.name}")
        return {
            "file_id": file_id,
            "filename": audio_file_path.name,
            "transcription": result.get("transcription", ""),
            "language": result.get("language", "unknown"),
            "duration": result.get("duration", 0),
            "type": "audio"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# Enhanced multimodal chat that can handle audio transcription
@app.post("/api/v1/chat/multimodal-audio")
async def multimodal_audio_chat(request: MultimodalRequest):
    """Chat completion with file support including audio transcription"""
    try:
        # Build the context with file contents
        context_messages = []
        
        # Collect file information for smart routing
        file_info = []
        
        # Add file contents to context if provided
        if request.file_ids:
            file_context = "=== Attached Files ===\n"
            for file_id in request.file_ids:
                # Find the file
                file_found = False
                for file_path in UPLOAD_DIR.iterdir():
                    if file_path.stem == file_id:
                        file_type = file_path.suffix.lower()
                        
                        # Handle audio files with transcription
                        if file_type in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                            logger.info(f"Processing audio file for chat: {file_path.name}")
                            
                            # Collect file info for routing
                            file_info.append({
                                "type": "audio",
                                "size": file_path.stat().st_size,
                                "name": file_path.name
                            })
                            
                            audio_result = await process_audio(file_path)
                            
                            if "error" in audio_result:
                                file_context += f"\nFile: {file_path.name}\nType: Audio\nNote: {audio_result.get('fallback', 'Audio processing failed')}\n\n"
                            else:
                                transcription = audio_result.get("transcription", "")
                                language = audio_result.get("language", "unknown")
                                file_context += f"\nFile: {file_path.name}\nType: Audio Transcription\nLanguage: {language}\nContent:\n{transcription}\n\n"
                        else:
                            # Collect file info for routing
                            file_content = get_file_content(file_path)
                            file_info.append({
                                "type": file_content.get("type", "unknown"),
                                "size": file_path.stat().st_size,
                                "name": file_path.name
                            })
                            
                            # Handle other file types normally
                            file_type_name = file_content.get("type", "unknown")
                            
                            if file_type_name in ["pdf", "docx", "text", "excel"]:
                                file_context += f"\nFile: {file_path.name}\nType: {file_type_name}\nContent:\n{file_content.get('content', 'No content available')}\n\n"
                            elif file_type_name == "image":
                                file_context += f"\nFile: {file_path.name}\nType: Image\nDescription: {file_content.get('description', 'Image file')}\n\n"
                            else:
                                file_context += f"\nFile: {file_path.name}\nType: {file_type_name}\nNote: This file type is not fully processed but was uploaded successfully.\n\n"
                        
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
        
        # Smart model selection
        selected_model = model_selector.select_model(request, file_info)
        
        # Convert to Ollama format
        payload = {
            "model": selected_model,
            "messages": context_messages,
            "stream": request.stream
        }
        
        # Return streaming response if requested
        if request.stream:
            logger.info(f"Streaming multimodal-audio request to Ollama with {len(request.file_ids)} files using model {selected_model}")
            return StreamingResponse(
                stream_ollama_response(payload),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        
        logger.info(f"Sending multimodal-audio request to Ollama with {len(request.file_ids)} files using model {selected_model}")
        
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
            
            logger.info(f"Successfully processed multimodal-audio request with {len(request.file_ids)} files")
            return openai_response
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ollama is not available. Please ensure it's running."
        )
    except Exception as e:
        logger.error(f"Unexpected error in multimodal-audio chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart routing analysis endpoint
@app.post("/api/v1/analyze-complexity")
async def analyze_complexity(request: MultimodalRequest):
    """Analyze request complexity and show model routing decision"""
    try:
        # Collect file information
        file_info = []
        
        if request.file_ids:
            for file_id in request.file_ids:
                for file_path in UPLOAD_DIR.iterdir():
                    if file_path.stem == file_id:
                        if file_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                            file_info.append({
                                "type": "audio",
                                "size": file_path.stat().st_size,
                                "name": file_path.name
                            })
                        else:
                            file_content = get_file_content(file_path)
                            file_info.append({
                                "type": file_content.get("type", "unknown"),
                                "size": file_path.stat().st_size,
                                "name": file_path.name
                            })
                        break
        
        # Calculate complexity
        complexity_score = model_selector.calculate_complexity_score(request, file_info)
        selected_model = model_selector.select_model(request, file_info)
        
        # Message analysis
        total_message_length = sum(len(msg.content) for msg in request.messages)
        
        return {
            "complexity_analysis": {
                "complexity_score": complexity_score,
                "selected_model": selected_model,
                "reasoning": {
                    "total_message_length": total_message_length,
                    "file_count": len(file_info),
                    "file_types": [f["type"] for f in file_info],
                    "total_file_size": sum(f["size"] for f in file_info),
                    "has_multimodal_content": len(file_info) > 0,
                    "complexity_factors": {
                        "message_complexity": "high" if total_message_length > 2000 else "medium" if total_message_length > 500 else "low",
                        "file_complexity": "high" if any(f["type"] in ["audio", "image"] for f in file_info) else "medium" if any(f["type"] in ["pdf", "excel"] for f in file_info) else "low" if file_info else "none",
                        "size_complexity": "high" if any(f["size"] > 1000000 for f in file_info) else "medium" if any(f["size"] > 100000 for f in file_info) else "low"
                    }
                }
            },
            "available_models": model_selector.models,
            "routing_logic": "Complexity-based model selection with file type and size analysis"
        }
        
    except Exception as e:
        logger.error(f"Complexity analysis error: {e}")
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
            "multimodal_audio_chat": "/api/v1/chat/multimodal-audio",
            "transcribe": "/api/v1/transcribe/{file_id}",
            "analyze_complexity": "/api/v1/analyze-complexity",
            "upload": "/api/v1/upload",
            "files": "/api/v1/files",
            "models": "/api/v1/models"
        },
        "smart_routing": {
            "enabled": True,
            "default_model": "auto",
            "complexity_factors": ["message_length", "file_types", "file_sizes", "multimodal_content"],
            "routing_logic": "Automatic model selection based on request complexity"
        },
        "streaming": {
            "enabled": True,
            "description": "Real-time streaming responses supported",
            "parameter": "Set 'stream': true in request body"
        },
        "supported_file_types": {
            "documents": ["pdf", "docx", "txt", "md"],
            "spreadsheets": ["xlsx", "xls", "csv"],
            "images": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            "audio": ["mp3", "wav", "m4a", "ogg", "flac"],
            "code": ["py", "js", "html", "css", "json"]
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)