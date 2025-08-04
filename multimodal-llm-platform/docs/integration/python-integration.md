# Python Integration Guide

Complete guide for integrating Autopicker Platform with Python applications, including FastAPI, Django, Flask, and data science workflows.

## 🐍 Installation & Setup

### Prerequisites

```bash
pip install requests aiohttp python-multipart aiofiles
```

### Basic Client Library

```python
# autopicker_client.py
import asyncio
import aiohttp
import requests
import json
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path

class AutopickerClient:
    def __init__(
        self, 
        base_url: str = "http://38.242.229.78:8001",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        
        if api_key:
            self.headers["X-API-Key"] = api_key
        
        # Synchronous session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    # Synchronous methods
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat completion request"""
        data = {"messages": messages, **kwargs}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion response"""
        data = {"messages": messages, "stream": True, **kwargs}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json=data,
            stream=True,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                try:
                    chunk = json.loads(line[6:])
                    if chunk.get('choices') and chunk['choices'][0]['delta'].get('content'):
                        yield chunk['choices'][0]['delta']['content']
                except json.JSONDecodeError:
                    continue
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload a file and return file info"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/v1/upload",
                files=files,
                headers={k: v for k, v in self.headers.items() if k != "Content-Type"},
                timeout=60
            )
        
        response.raise_for_status()
        return response.json()
    
    def chat_with_files(
        self, 
        messages: List[Dict[str, str]], 
        file_ids: List[str],
        **kwargs
    ) -> str:
        """Chat with file context"""
        data = {
            "messages": messages,
            "file_ids": file_ids,
            **kwargs
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/multimodal",
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def transcribe_audio(self, file_id: str) -> Dict[str, Any]:
        """Transcribe audio file"""
        response = self.session.post(
            f"{self.base_url}/api/v1/transcribe/{file_id}",
            timeout=60
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models"""
        response = self.session.get(f"{self.base_url}/api/v1/models")
        response.raise_for_status()
        
        return response.json()["data"]
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        
        return response.json()
    
    # Asynchronous methods
    async def achat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Async chat completion"""
        data = {"messages": messages, **kwargs}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat/completions",
                json=data,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def aupload_file(self, file_path: str) -> Dict[str, Any]:
        """Async file upload"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f)
                
                async with session.post(
                    f"{self.base_url}/api/v1/upload",
                    data=data,
                    headers={k: v for k, v in self.headers.items() if k != "Content-Type"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
    
    async def achat_with_files(
        self,
        messages: List[Dict[str, str]],
        file_ids: List[str],
        **kwargs
    ) -> str:
        """Async chat with files"""
        data = {
            "messages": messages,
            "file_ids": file_ids,
            **kwargs
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat/multimodal",
                json=data,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["choices"][0]["message"]["content"]

# Usage examples
if __name__ == "__main__":
    client = AutopickerClient()
    
    # Simple chat
    response = client.chat([{"role": "user", "content": "Hello!"}])
    print(response)
    
    # Upload and analyze file
    file_info = client.upload_file("document.pdf")
    analysis = client.chat_with_files(
        [{"role": "user", "content": "Summarize this document"}],
        [file_info["id"]]
    )
    print(analysis)
```

## 🚀 FastAPI Integration

### Basic FastAPI Service

```python
# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os

from autopicker_client import AutopickerClient

app = FastAPI(title="Document Analysis Service")
client = AutopickerClient()

class ChatRequest(BaseModel):
    message: str
    stream: bool = False

class AnalysisRequest(BaseModel):
    question: str
    file_ids: List[str]

@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...), question: str = "Summarize this document"):
    """Upload and analyze a document"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to Autopicker
            file_info = client.upload_file(tmp_file_path)
            
            # Analyze document
            analysis = client.chat_with_files(
                [{"role": "user", "content": question}],
                [file_info["id"]]
            )
            
            return {
                "filename": file.filename,
                "file_id": file_info["id"],
                "file_type": file_info["file_type"],
                "question": question,
                "analysis": analysis
            }
        
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with AI"""
    try:
        if request.stream:
            def generate():
                for chunk in client.chat_stream([{"role": "user", "content": request.message}]):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            response = client.chat([{"role": "user", "content": request.message}])
            return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/multi-document-analysis")
async def multi_document_analysis(files: List[UploadFile] = File(...), question: str = "Compare these documents"):
    """Analyze multiple documents"""
    try:
        file_ids = []
        temp_files = []
        
        # Upload all files
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
                
                file_info = client.upload_file(tmp_file.name)
                file_ids.append(file_info["id"])
        
        try:
            # Analyze all documents together
            analysis = client.chat_with_files(
                [{"role": "user", "content": question}],
                file_ids
            )
            
            return {
                "files_analyzed": len(files),
                "file_ids": file_ids,
                "question": question,
                "analysis": analysis
            }
        
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                os.unlink(temp_file)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check that includes Autopicker API status"""
    try:
        autopicker_health = client.health_check()
        return {
            "status": "healthy",
            "autopicker_status": autopicker_health["status"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

### Advanced FastAPI with Background Tasks

```python
# advanced_service.py
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List
import uuid
import asyncio
from datetime import datetime

app = FastAPI()
client = AutopickerClient()

# In-memory job storage (use Redis/DB in production)
jobs: Dict[str, Dict] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

async def process_documents_background(job_id: str, file_paths: List[str], analysis_prompt: str):
    """Background task to process multiple documents"""
    try:
        jobs[job_id]["status"] = "processing"
        
        # Upload all files
        file_ids = []
        for file_path in file_paths:
            file_info = await client.aupload_file(file_path)
            file_ids.append(file_info["id"])
        
        # Process with AI
        result = await client.achat_with_files(
            [{"role": "user", "content": analysis_prompt}],
            file_ids
        )
        
        jobs[job_id].update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })

@app.post("/analyze-batch")
async def analyze_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    analysis_prompt: str = "Analyze and summarize these documents"
):
    """Start batch document analysis"""
    job_id = str(uuid.uuid4())
    
    # Save files temporarily
    temp_files = []
    for file in files:
        temp_path = f"/tmp/{job_id}_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        temp_files.append(temp_path)
    
    # Create job record
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now(),
        "file_count": len(files)
    }
    
    # Start background processing
    background_tasks.add_task(
        process_documents_background,
        job_id,
        temp_files,
        analysis_prompt
    )
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and results"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]
```

## 🌐 Django Integration

### Django Views

```python
# views.py
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import tempfile
import os

from .autopicker_client import AutopickerClient

client = AutopickerClient()

@csrf_exempt
@require_http_methods(["POST"])
def upload_and_analyze(request):
    """Django view for document analysis"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        uploaded_file = request.FILES['file']
        question = request.POST.get('question', 'Summarize this document')
        
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}")
        
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()
        
        try:
            # Upload to Autopicker
            file_info = client.upload_file(temp_file.name)
            
            # Analyze
            analysis = client.chat_with_files(
                [{"role": "user", "content": question}],
                [file_info["id"]]
            )
            
            return JsonResponse({
                "success": True,
                "filename": uploaded_file.name,
                "analysis": analysis,
                "file_id": file_info["id"]
            })
        
        finally:
            os.unlink(temp_file.name)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def chat_view(request):
    """Django chat endpoint"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        stream = data.get('stream', False)
        
        if not message:
            return JsonResponse({"error": "Message is required"}, status=400)
        
        if stream:
            def generate():
                for chunk in client.chat_stream([{"role": "user", "content": message}]):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            response = StreamingHttpResponse(generate(), content_type='text/plain')
            response['Cache-Control'] = 'no-cache'
            return response
        else:
            response_text = client.chat([{"role": "user", "content": message}])
            return JsonResponse({"response": response_text})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.upload_and_analyze, name='analyze'),
    path('chat/', views.chat_view, name='chat'),
]
```

### Django Models and Admin

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class DocumentAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    file_id = models.CharField(max_length=100)
    question = models.TextField()
    analysis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # user, assistant
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

# admin.py
from django.contrib import admin
from .models import DocumentAnalysis, ChatSession, ChatMessage

@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['filename', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['filename', 'user__username']
    readonly_fields = ['file_id', 'analysis', 'created_at']

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at']
    list_filter = ['created_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'timestamp']
    list_filter = ['role', 'timestamp']
```

## 🧪 Flask Integration

```python
# app.py
from flask import Flask, request, jsonify, Response
import tempfile
import os
import json

from autopicker_client import AutopickerClient

app = Flask(__name__)
client = AutopickerClient()

@app.route('/analyze', methods=['POST'])
def analyze_document():
    """Flask endpoint for document analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        question = request.form.get('question', 'Summarize this document')
        
        # Save temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}")
        file.save(temp_file.name)
        
        try:
            # Upload and analyze
            file_info = client.upload_file(temp_file.name)
            analysis = client.chat_with_files(
                [{"role": "user", "content": question}],
                [file_info["id"]]
            )
            
            return jsonify({
                "filename": file.filename,
                "analysis": analysis,
                "file_id": file_info["id"]
            })
        
        finally:
            os.unlink(temp_file.name)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Flask chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        stream = data.get('stream', False)
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        if stream:
            def generate():
                for chunk in client.chat_stream([{"role": "user", "content": message}]):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return Response(generate(), mimetype='text/plain')
        else:
            response_text = client.chat([{"role": "user", "content": message}])
            return jsonify({"response": response_text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """Health check"""
    try:
        autopicker_health = client.health_check()
        return jsonify({
            "status": "healthy",
            "autopicker_status": autopicker_health["status"]
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## 📊 Data Science Integration

### Pandas Integration

```python
# data_analysis.py
import pandas as pd
import numpy as np
from autopicker_client import AutopickerClient
import tempfile
import os

class DataAnalyzer:
    def __init__(self):
        self.client = AutopickerClient()
    
    def analyze_csv_data(self, df: pd.DataFrame, analysis_question: str) -> str:
        """Analyze pandas DataFrame using AI"""
        # Save DataFrame to temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            
            try:
                # Upload and analyze
                file_info = self.client.upload_file(tmp_file.name)
                analysis = self.client.chat_with_files(
                    [{"role": "user", "content": analysis_question}],
                    [file_info["id"]]
                )
                
                return analysis
            
            finally:
                os.unlink(tmp_file.name)
    
    def generate_data_insights(self, df: pd.DataFrame) -> dict:
        """Generate comprehensive data insights"""
        # Basic statistics
        basic_stats = df.describe().to_string()
        
        # Data types and missing values
        info_summary = f"""
        Data Shape: {df.shape}
        Data Types: {df.dtypes.to_dict()}
        Missing Values: {df.isnull().sum().to_dict()}
        """
        
        # Create analysis prompt
        prompt = f"""
        Analyze this dataset and provide insights:
        
        Basic Statistics:
        {basic_stats}
        
        Dataset Info:
        {info_summary}
        
        Please provide:
        1. Key insights about the data
        2. Notable patterns or anomalies
        3. Recommendations for further analysis
        4. Potential data quality issues
        """
        
        ai_analysis = self.analyze_csv_data(df, prompt)
        
        return {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "data_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "basic_stats": df.describe().to_dict(),
            "ai_insights": ai_analysis
        }

# Usage example
analyzer = DataAnalyzer()

# Load your data
df = pd.read_csv("sales_data.csv")

# Get AI-powered insights
insights = analyzer.generate_data_insights(df)
print("AI Insights:", insights["ai_insights"])

# Ask specific questions
trend_analysis = analyzer.analyze_csv_data(
    df, 
    "What are the main trends and seasonal patterns in this sales data?"
)
print("Trend Analysis:", trend_analysis)
```

### Jupyter Notebook Integration

```python
# jupyter_helpers.py
from IPython.display import display, HTML, Markdown
import matplotlib.pyplot as plt
import seaborn as sns
from autopicker_client import AutopickerClient

class JupyterAutopicker:
    def __init__(self):
        self.client = AutopickerClient()
    
    def analyze_and_display(self, file_path: str, question: str = "Analyze this data"):
        """Analyze file and display results in Jupyter"""
        try:
            # Upload and analyze
            file_info = self.client.upload_file(file_path)
            analysis = self.client.chat_with_files(
                [{"role": "user", "content": question}],
                [file_info["id"]]
            )
            
            # Display results
            display(HTML(f"<h3>Analysis of {file_path}</h3>"))
            display(Markdown(analysis))
            
            return analysis
        
        except Exception as e:
            display(HTML(f"<div style='color: red;'>Error: {str(e)}</div>"))
            return None
    
    def chat_with_plot(self, data, plot_type: str = "analyze"):
        """Create a plot and ask AI to analyze it"""
        # Save plot
        plt.figure(figsize=(10, 6))
        
        if plot_type == "histogram":
            plt.hist(data, bins=30, alpha=0.7)
        elif plot_type == "scatter":
            plt.scatter(data[:, 0], data[:, 1], alpha=0.7)
        else:
            plt.plot(data)
        
        plot_path = "/tmp/analysis_plot.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.show()
        
        # Analyze plot with AI
        analysis = self.analyze_and_display(plot_path, "Analyze this data visualization")
        return analysis

# In Jupyter notebook:
# jp = JupyterAutopicker()
# jp.analyze_and_display("data.csv", "What insights can you find in this data?")
```

## 🔄 Async Processing Patterns

### Concurrent File Processing

```python
# async_processing.py
import asyncio
import aiohttp
from typing import List, Dict, Any
import time

class AsyncBatchProcessor:
    def __init__(self, base_url: str = "http://38.242.229.78:8001", max_concurrent: int = 5):
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def process_file_batch(
        self, 
        file_paths: List[str], 
        analysis_prompts: List[str]
    ) -> List[Dict[str, Any]]:
        """Process multiple files concurrently"""
        tasks = [
            self._process_single_file(file_path, prompt)
            for file_path, prompt in zip(file_paths, analysis_prompts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "file_path": file_paths[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append({
                    "file_path": file_paths[i],
                    "analysis": result,
                    "success": True
                })
        
        return processed_results
    
    async def _process_single_file(self, file_path: str, prompt: str) -> str:
        """Process a single file with rate limiting"""
        async with self.semaphore:
            # Upload file
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f)
                
                async with self.session.post(f"{self.base_url}/api/v1/upload", data=data) as response:
                    response.raise_for_status()
                    upload_result = await response.json()
                    file_id = upload_result["id"]
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
            
            # Analyze file
            chat_data = {
                "messages": [{"role": "user", "content": prompt}],
                "file_ids": [file_id]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/multimodal", 
                json=chat_data
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["choices"][0]["message"]["content"]

# Usage example
async def main():
    file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    prompts = [
        "Summarize the key findings",
        "Extract action items",
        "Identify risks and opportunities"
    ]
    
    async with AsyncBatchProcessor(max_concurrent=3) as processor:
        start_time = time.time()
        results = await processor.process_file_batch(file_paths, prompts)
        elapsed = time.time() - start_time
        
        print(f"Processed {len(file_paths)} files in {elapsed:.2f} seconds")
        
        for result in results:
            if result["success"]:
                print(f"\n{result['file_path']}:")
                print(result["analysis"][:200] + "...")
            else:
                print(f"\nError processing {result['file_path']}: {result['error']}")

# Run async processing
# asyncio.run(main())
```

## 🧪 Testing

```python
# test_autopicker_integration.py
import pytest
import tempfile
import os
from autopicker_client import AutopickerClient

@pytest.fixture
def client():
    return AutopickerClient()

@pytest.fixture
def sample_text_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document with sample content for analysis.")
        return f.name

def test_health_check(client):
    """Test API health check"""
    health = client.health_check()
    assert health["status"] == "healthy"

def test_basic_chat(client):
    """Test basic chat functionality"""
    response = client.chat([{"role": "user", "content": "Hello, how are you?"}])
    assert isinstance(response, str)
    assert len(response) > 0

def test_file_upload_and_analysis(client, sample_text_file):
    """Test file upload and analysis"""
    try:
        # Upload file
        file_info = client.upload_file(sample_text_file)
        assert "id" in file_info
        assert file_info["file_type"] == "text"
        
        # Analyze file
        analysis = client.chat_with_files(
            [{"role": "user", "content": "What is this document about?"}],
            [file_info["id"]]
        )
        assert isinstance(analysis, str)
        assert len(analysis) > 0
        
    finally:
        os.unlink(sample_text_file)

def test_streaming_chat(client):
    """Test streaming chat functionality"""
    chunks = list(client.chat_stream([{"role": "user", "content": "Count to 5"}]))
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)

@pytest.mark.asyncio
async def test_async_chat(client):
    """Test async chat functionality"""
    response = await client.achat([{"role": "user", "content": "Hello async!"}])
    assert isinstance(response, str)
    assert len(response) > 0

# Run tests with: pytest test_autopicker_integration.py -v
```

This comprehensive Python integration guide covers all major frameworks and use cases. Each example is production-ready and includes proper error handling, async support, and best practices.