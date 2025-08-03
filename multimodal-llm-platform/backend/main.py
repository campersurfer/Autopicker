from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
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
from processors.file_processor import FileProcessor, FileProcessorError
from services.search_service import SearchService, SearchResult
from services.concurrent_processor import ConcurrentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multimodal LLM Platform API",
    description="A comprehensive API for processing multimodal content using various LLM providers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:19006"],  # React and React Native
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:8000")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize file processor, search service, and concurrent processor
file_processor = FileProcessor()
search_service = SearchService()
concurrent_processor = ConcurrentProcessor(file_processor, search_service)

# Request/Response Models
class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    mime_type: str
    upload_path: str

class FileProcessRequest(BaseModel):
    file_id: str
    auto_process: Optional[bool] = True

class FileProcessResponse(BaseModel):
    file_id: str
    processing_status: str
    content: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    error: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    num_results: Optional[int] = 5
    engines: Optional[List[str]] = None

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_time_ms: Optional[int] = None

class ConcurrentProcessRequest(BaseModel):
    file_ids: List[str]
    query: str
    num_results: Optional[int] = 5

class ConcurrentProcessResponse(BaseModel):
    file_contents: List[Dict[str, Any]]
    search_results: Dict[str, Any]
    query: str
    total_files: int
    processing_time_savings: str

class BatchProcessRequest(BaseModel):
    file_ids: List[str]
    batch_size: Optional[int] = 5

class BatchProcessResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_files: int
    successful_files: int
    failed_files: int

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multimodal-llm-platform"}

# Chat completion endpoint
@app.post("/api/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    """
    Process chat completion requests and forward to LiteLLM proxy
    """
    try:
        # Convert Pydantic model to dict
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        logger.info(f"Forwarding request to LiteLLM: {request.model}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LITELLM_PROXY_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"LiteLLM error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LiteLLM proxy error: {response.text}"
                )
            
            result = response.json()
            logger.info(f"Successfully processed request with model: {result.get('model')}")
            return result
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="LiteLLM proxy is not available. Please ensure it's running."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Streaming chat completion endpoint
@app.post("/api/v1/chat/completions/stream")
async def chat_completion_stream(request: ChatCompletionRequest):
    """
    Process streaming chat completion requests
    """
    try:
        # Force streaming mode
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        logger.info(f"Starting streaming request to LiteLLM: {request.model}")
        
        async def generate_stream():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{LITELLM_PROXY_URL}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'error': f'LiteLLM error: {response.status_code}'})}\n\n"
                        return
                    
                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File upload endpoint
@app.post("/api/v1/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and save files for processing
    """
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
        
        logger.info(f"File uploaded: {file.filename} -> {stored_filename} ({file_size} bytes)")
        
        return FileUploadResponse(
            id=file_id,
            filename=stored_filename,
            original_filename=file.filename or "unknown",
            size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            upload_path=str(file_path)
        )
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# List uploaded files
@app.get("/api/v1/files")
async def list_files():
    """
    List all uploaded files
    """
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
    """
    Get list of available models from LiteLLM proxy
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LITELLM_PROXY_URL}/v1/models")
            
            if response.status_code != 200:
                # Return default models if LiteLLM is not available
                return {
                    "object": "list",
                    "data": [
                        {"id": "gpt-3.5-turbo", "object": "model"},
                        {"id": "gpt-4", "object": "model"},
                        {"id": "claude-3-sonnet", "object": "model"},
                        {"id": "claude-3-haiku", "object": "model"}
                    ]
                }
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Models endpoint error: {e}")
        # Return default models on error
        return {
            "object": "list",
            "data": [
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "gpt-4", "object": "model"},
                {"id": "claude-3-sonnet", "object": "model"},
                {"id": "claude-3-haiku", "object": "model"}
            ]
        }

# Process uploaded file
@app.post("/api/v1/files/{file_id}/process", response_model=FileProcessResponse)
async def process_uploaded_file(file_id: str):
    """
    Process an uploaded file and extract content
    """
    try:
        # Find the file by ID (look for files starting with the ID)
        file_path = None
        for uploaded_file in UPLOAD_DIR.iterdir():
            if uploaded_file.name.startswith(file_id):
                file_path = uploaded_file
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Check if file type is supported
        if not file_processor.is_supported(file_path):
            file_type = file_processor.get_file_type(file_path)
            raise HTTPException(
                status_code=422, 
                detail=f"File type {file_type} is not supported for processing"
            )
        
        # Process the file
        result = file_processor.process_file(file_path)
        
        if result['processing_status'] == 'success':
            summary = file_processor.get_file_summary(result)
            logger.info(f"Successfully processed file {file_id}: {summary}")
            
            return FileProcessResponse(
                file_id=file_id,
                processing_status='success',
                content=result['content'],
                summary=summary
            )
        else:
            logger.error(f"Failed to process file {file_id}: {result.get('error')}")
            return FileProcessResponse(
                file_id=file_id,
                processing_status='error',
                error=result.get('error')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File processing error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

# Get file processing status
@app.get("/api/v1/files/{file_id}/process")
async def get_file_process_status(file_id: str):
    """
    Get the processing status of a file
    """
    try:
        # Find the file by ID
        file_path = None
        for uploaded_file in UPLOAD_DIR.iterdir():
            if uploaded_file.name.startswith(file_id):
                file_path = uploaded_file
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Check if file is supported
        is_supported = file_processor.is_supported(file_path)
        file_type = file_processor.get_file_type(file_path)
        
        return {
            "file_id": file_id,
            "file_name": file_path.name,
            "file_type": file_type,
            "is_supported": is_supported,
            "supported_types": file_processor.get_supported_types()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get supported file types
@app.get("/api/v1/files/supported-types")
async def get_supported_file_types():
    """
    Get list of supported file types for processing
    """
    return {
        "supported_types": file_processor.get_supported_types(),
        "description": "File types that can be processed for content extraction"
    }

# Process file with chat context
@app.post("/api/v1/files/{file_id}/chat")
async def chat_with_file(file_id: str, request: ChatCompletionRequest):
    """
    Process a file and use its content in a chat completion
    """
    try:
        # Find and process the file
        file_path = None
        for uploaded_file in UPLOAD_DIR.iterdir():
            if uploaded_file.name.startswith(file_id):
                file_path = uploaded_file
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Process the file
        result = file_processor.process_file(file_path)
        
        if result['processing_status'] != 'success':
            raise HTTPException(
                status_code=422, 
                detail=f"File processing failed: {result.get('error')}"
            )
        
        # Get the extracted text content
        file_content = result['content']
        extracted_text = file_content.get('text', '')
        
        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail="No text content could be extracted from the file"
            )
        
        # Create a system message with file content
        file_summary = file_processor.get_file_summary(result)
        system_message = ChatMessage(
            role="system",
            content=f"You are analyzing the following file: {file_summary}\n\nFile content:\n{extracted_text[:8000]}{'...' if len(extracted_text) > 8000 else ''}"
        )
        
        # Prepend system message to the conversation
        messages = [system_message] + request.messages
        
        # Create new request with file context
        chat_request = ChatCompletionRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        # Forward to chat completion endpoint
        return await chat_completion(chat_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Web search endpoint
@app.post("/api/v1/search", response_model=SearchResponse)
async def web_search(request: SearchRequest):
    """
    Perform web search using SearXNG or fallback to mock search
    """
    try:
        import time
        start_time = time.time()
        
        # Perform search
        results = await search_service.search(
            query=request.query,
            num_results=request.num_results,
            engines=request.engines
        )
        
        # Calculate search time
        search_time = int((time.time() - start_time) * 1000)
        
        # Convert results to dict format
        result_dicts = [result.to_dict() for result in results]
        
        logger.info(f"Search completed: {len(results)} results for '{request.query}' in {search_time}ms")
        
        return SearchResponse(
            query=request.query,
            results=result_dicts,
            total_results=len(results),
            search_time_ms=search_time
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Check search service status
@app.get("/api/v1/search/status")
async def search_status():
    """
    Check the status of the search service
    """
    try:
        is_available = await search_service.is_available()
        
        return {
            "searxng_available": is_available,
            "searxng_url": search_service.searxng_url,
            "fallback_mode": not is_available,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Search status error: {e}")
        return {
            "searxng_available": False,
            "searxng_url": search_service.searxng_url,
            "fallback_mode": True,
            "status": "error",
            "error": str(e)
        }

# Search with file context
@app.post("/api/v1/search/with-context")
async def search_with_context(file_id: str, request: SearchRequest):
    """
    Perform web search enhanced with file content context
    """
    try:
        # Find and process the file
        file_path = None
        for uploaded_file in UPLOAD_DIR.iterdir():
            if uploaded_file.name.startswith(file_id):
                file_path = uploaded_file
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Process the file to get context
        result = file_processor.process_file(file_path)
        
        if result['processing_status'] != 'success':
            raise HTTPException(
                status_code=422, 
                detail=f"File processing failed: {result.get('error')}"
            )
        
        # Extract context from file
        file_content = result['content']
        context = file_content.get('text', '')[:500]  # First 500 chars as context
        
        # Perform enhanced search
        search_results = await search_service.search_with_context(
            query=request.query,
            context=context,
            num_results=request.num_results
        )
        
        # Convert results to dict format
        result_dicts = [result.to_dict() for result in search_results]
        
        return {
            "query": request.query,
            "context_file": file_path.name,
            "results": result_dicts,
            "total_results": len(search_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Concurrent processing endpoint
@app.post("/api/v1/process/concurrent", response_model=ConcurrentProcessResponse)
async def concurrent_process_files_and_search(request: ConcurrentProcessRequest):
    """
    Process multiple files and perform web search concurrently
    """
    try:
        # Find file paths from IDs
        file_paths = []
        for file_id in request.file_ids:
            file_path = None
            for uploaded_file in UPLOAD_DIR.iterdir():
                if uploaded_file.name.startswith(file_id):
                    file_path = uploaded_file
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
            
            file_paths.append(file_path)
        
        # Perform concurrent processing
        result = await concurrent_processor.process_with_search(
            file_paths=file_paths,
            query=request.query,
            num_results=request.num_results
        )
        
        logger.info(f"Concurrent processing completed: {len(file_paths)} files + search for '{request.query}'")
        
        return ConcurrentProcessResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Concurrent processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Concurrent processing failed: {str(e)}")

# Context-enhanced concurrent processing
@app.post("/api/v1/process/concurrent-context")
async def concurrent_process_with_context(request: ConcurrentProcessRequest):
    """
    Process files and perform context-enhanced searches concurrently
    """
    try:
        # Find file paths from IDs
        file_paths = []
        for file_id in request.file_ids:
            file_path = None
            for uploaded_file in UPLOAD_DIR.iterdir():
                if uploaded_file.name.startswith(file_id):
                    file_path = uploaded_file
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
            
            file_paths.append(file_path)
        
        # Perform context-enhanced concurrent processing
        result = await concurrent_processor.process_files_with_context_search(
            file_paths=file_paths,
            base_query=request.query,
            num_results=request.num_results
        )
        
        logger.info(f"Context-enhanced concurrent processing completed: {len(file_paths)} files")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context-enhanced concurrent processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Context-enhanced processing failed: {str(e)}")

# Batch processing endpoint
@app.post("/api/v1/process/batch", response_model=BatchProcessResponse)
async def batch_process_files(request: BatchProcessRequest):
    """
    Process multiple files in batches to avoid system overload
    """
    try:
        # Find file paths from IDs
        file_paths = []
        for file_id in request.file_ids:
            file_path = None
            for uploaded_file in UPLOAD_DIR.iterdir():
                if uploaded_file.name.startswith(file_id):
                    file_path = uploaded_file
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
            
            file_paths.append(file_path)
        
        # Perform batch processing
        results = await concurrent_processor.batch_process_files(
            file_paths=file_paths,
            batch_size=request.batch_size
        )
        
        # Calculate statistics
        successful_files = len([r for r in results if r.get('status') == 'success'])
        failed_files = len(results) - successful_files
        
        logger.info(f"Batch processing completed: {successful_files}/{len(results)} files successful")
        
        return BatchProcessResponse(
            results=results,
            total_files=len(results),
            successful_files=successful_files,
            failed_files=failed_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "Multimodal LLM Platform API",
        "version": "1.0.0",
        "description": "A comprehensive API for processing multimodal content using various LLM providers",
        "endpoints": {
            "health": "/health",
            "chat": "/api/v1/chat/completions",
            "chat_stream": "/api/v1/chat/completions/stream", 
            "upload": "/api/v1/upload",
            "files": "/api/v1/files",
            "models": "/api/v1/models",
            "file_process": "/api/v1/files/{file_id}/process",
            "file_status": "/api/v1/files/{file_id}/process",
            "file_chat": "/api/v1/files/{file_id}/chat",
            "supported_types": "/api/v1/files/supported-types",
            "search": "/api/v1/search",
            "search_status": "/api/v1/search/status",
            "search_with_context": "/api/v1/search/with-context",
            "concurrent_process": "/api/v1/process/concurrent",
            "concurrent_context": "/api/v1/process/concurrent-context",
            "batch_process": "/api/v1/process/batch"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)