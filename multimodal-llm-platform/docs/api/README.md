# Autopicker Multimodal LLM Platform API Documentation

Welcome to the Autopicker Platform API documentation! This comprehensive guide will help you integrate with our multimodal AI platform.

## 🚀 Quick Start

### Base URL
- **Production**: `http://38.242.229.78:8001`
- **Local Development**: `http://localhost:8001`

### Interactive Documentation
- **Swagger UI**: http://38.242.229.78:8001/docs
- **ReDoc**: http://38.242.229.78:8001/redoc

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Rate Limits](#rate-limits)
3. [File Upload](#file-upload)
4. [Chat Completions](#chat-completions)
5. [Multimodal Processing](#multimodal-processing)
6. [Audio Transcription](#audio-transcription)
7. [System Monitoring](#system-monitoring)
8. [Error Handling](#error-handling)
9. [SDKs and Examples](#sdks-and-examples)

## 🔐 Authentication

The API supports optional API key authentication for enhanced security:

```bash
curl -H "X-API-Key: your-api-key" \
     http://38.242.229.78:8001/api/v1/models
```

**Note**: API keys are optional for basic usage but recommended for production applications.

## ⚡ Rate Limits

- **Rate Limit**: 100 requests per minute per IP address
- **File Upload Limit**: 10MB per file
- **Concurrent Connections**: Optimized for high throughput

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641024000
```

## 📁 File Upload

### Supported File Types

| Category | File Types | Processing |
|----------|------------|------------|
| **Documents** | PDF, DOCX, TXT, MD | Text extraction |
| **Spreadsheets** | XLSX, XLS, CSV | Data extraction |
| **Images** | JPG, PNG, GIF, BMP, WEBP | Image analysis |
| **Audio** | MP3, WAV, M4A, OGG, FLAC | Speech-to-text |
| **Code** | PY, JS, HTML, CSS, JSON | Syntax analysis |

### Upload Example

```bash
curl -X POST http://38.242.229.78:8001/api/v1/upload \
  -F "file=@document.pdf"
```

```python
import requests

url = "http://38.242.229.78:8001/api/v1/upload"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
file_info = response.json()
print(f"File ID: {file_info['id']}")
```

## 💬 Chat Completions

### OpenAI-Compatible Format

Our API is fully compatible with OpenAI's chat completions format:

```bash
curl -X POST http://38.242.229.78:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "model": "llama3.2-local",
    "temperature": 0.7
  }'
```

### Streaming Responses

Enable real-time streaming by setting `stream: true`:

```python
import requests
import json

url = "http://38.242.229.78:8001/api/v1/chat/completions"
data = {
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": True
}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        # Parse streaming response
        if line.startswith(b'data: '):
            chunk = json.loads(line[6:])
            if chunk.get('choices'):
                content = chunk['choices'][0]['delta'].get('content', '')
                print(content, end='')
```

### Smart Model Routing

The platform automatically selects the best model based on request complexity:

```python
# Analyze complexity before sending request
complexity_data = {
    "messages": [{"role": "user", "content": "Analyze this complex document"}],
    "file_ids": ["file-id-123"]
}

response = requests.post(
    "http://38.242.229.78:8001/api/v1/analyze-complexity",
    json=complexity_data
)

analysis = response.json()
print(f"Complexity Score: {analysis['complexity_analysis']['complexity_score']}")
print(f"Selected Model: {analysis['complexity_analysis']['selected_model']}")
```

## 🎯 Multimodal Processing

### Chat with Files

Upload files and reference them in chat:

```python
import requests

# 1. Upload file
files = {"file": open("report.pdf", "rb")}
upload_response = requests.post("http://38.242.229.78:8001/api/v1/upload", files=files)
file_id = upload_response.json()["id"]

# 2. Chat with file context
chat_data = {
    "messages": [
        {"role": "user", "content": "Summarize the key findings from this report"}
    ],
    "file_ids": [file_id],
    "model": "auto"  # Smart routing
}

response = requests.post(
    "http://38.242.229.78:8001/api/v1/chat/multimodal",
    json=chat_data
)

print(response.json()["choices"][0]["message"]["content"])
```

### Multiple File Processing

Process multiple files simultaneously:

```python
# Upload multiple files
file_ids = []
for filename in ["doc1.pdf", "image1.jpg", "data.xlsx"]:
    files = {"file": open(filename, "rb")}
    upload_response = requests.post("http://38.242.229.78:8001/api/v1/upload", files=files)
    file_ids.append(upload_response.json()["id"])

# Analyze all files together
chat_data = {
    "messages": [
        {"role": "user", "content": "Compare and analyze all these documents"}
    ],
    "file_ids": file_ids
}

response = requests.post(
    "http://38.242.229.78:8001/api/v1/chat/multimodal-audio",
    json=chat_data
)
```

## 🎵 Audio Transcription

### Transcribe Audio Files

```python
import requests

# 1. Upload audio file
files = {"file": open("meeting.mp3", "rb")}
upload_response = requests.post("http://38.242.229.78:8001/api/v1/upload", files=files)
file_id = upload_response.json()["id"]

# 2. Transcribe audio
transcribe_response = requests.post(
    f"http://38.242.229.78:8001/api/v1/transcribe/{file_id}"
)

transcription = transcribe_response.json()
print(f"Transcription: {transcription['transcription']}")
print(f"Language: {transcription['language']}")
print(f"Duration: {transcription['duration']} seconds")
```

### Audio + Chat Integration

```python
# Upload and transcribe audio, then chat about it
files = {"file": open("interview.wav", "rb")}
upload_response = requests.post("http://38.242.229.78:8001/api/v1/upload", files=files)
file_id = upload_response.json()["id"]

# Chat with audio context (automatic transcription)
chat_data = {
    "messages": [
        {"role": "user", "content": "What are the main topics discussed in this audio?"}
    ],
    "file_ids": [file_id]
}

response = requests.post(
    "http://38.242.229.78:8001/api/v1/chat/multimodal-audio",
    json=chat_data
)
```

## 📊 System Monitoring

### Health Check

```bash
curl http://38.242.229.78:8001/health
```

### System Metrics

```python
import requests

# Get detailed system health
response = requests.get("http://38.242.229.78:8001/api/v1/monitoring/health")
metrics = response.json()

print(f"CPU Usage: {metrics['system_metrics']['cpu_percent']}%")
print(f"Memory Usage: {metrics['system_metrics']['memory_percent']}%")
print(f"Healthy APIs: {metrics['api_health']['healthy_endpoints']}")
```

### Performance Metrics

```python
# Get performance statistics
response = requests.get("http://38.242.229.78:8001/api/v1/performance/metrics")
perf = response.json()

cache_stats = perf['performance_metrics']['cache_stats']
print(f"Cache Hit Rate: {cache_stats['hit_rate_percent']}%")
```

### Load Testing

```python
# Run a load test
response = requests.post(
    "http://38.242.229.78:8001/api/v1/performance/load-test",
    params={
        "endpoint": "/health",
        "concurrent_users": 5,
        "requests_per_user": 10
    }
)

results = response.json()['load_test_results']
print(f"Success Rate: {results['success_rate_percent']}%")
print(f"Avg Response Time: {results['avg_response_time_ms']}ms")
```

## ❌ Error Handling

### HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid JSON or missing parameters |
| 401 | Unauthorized | Invalid API key |
| 413 | Payload Too Large | File exceeds 10MB limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server processing error |

### Error Response Format

```json
{
  "error": "Invalid request",
  "detail": "The 'messages' field is required",
  "status_code": 400
}
```

### Retry Logic

```python
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Use with retries
session = create_session_with_retries()
response = session.post("http://38.242.229.78:8001/api/v1/chat/completions", json=data)
```

## 🛠️ SDKs and Examples

### Python SDK Example

```python
class AutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/api/v1/upload", files=files)
            return response.json()
    
    def chat(self, messages, file_ids=None, stream=False):
        data = {
            "messages": messages,
            "stream": stream
        }
        if file_ids:
            data["file_ids"] = file_ids
        
        endpoint = "/api/v1/chat/multimodal" if file_ids else "/api/v1/chat/completions"
        response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=self.headers)
        return response.json()

# Usage
client = AutopickerClient()

# Upload and chat with file
file_info = client.upload_file("document.pdf")
response = client.chat(
    messages=[{"role": "user", "content": "Summarize this document"}],
    file_ids=[file_info["id"]]
)

print(response["choices"][0]["message"]["content"])
```

### JavaScript/Node.js Example

```javascript
class AutopickerClient {
    constructor(baseUrl = 'http://38.242.229.78:8001', apiKey = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json'
        };
        if (apiKey) {
            this.headers['X-API-Key'] = apiKey;
        }
    }

    async uploadFile(filePath) {
        const formData = new FormData();
        const fileBuffer = require('fs').readFileSync(filePath);
        const blob = new Blob([fileBuffer]);
        formData.append('file', blob);

        const response = await fetch(`${this.baseUrl}/api/v1/upload`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }

    async chat(messages, fileIds = null, stream = false) {
        const data = { messages, stream };
        if (fileIds) data.file_ids = fileIds;

        const endpoint = fileIds ? '/api/v1/chat/multimodal' : '/api/v1/chat/completions';
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return await response.json();
    }
}

// Usage
const client = new AutopickerClient();

async function example() {
    const fileInfo = await client.uploadFile('document.pdf');
    const response = await client.chat([
        { role: 'user', content: 'Analyze this document' }
    ], [fileInfo.id]);
    
    console.log(response.choices[0].message.content);
}
```

### cURL Examples

```bash
#!/bin/bash

# Set base URL
BASE_URL="http://38.242.229.78:8001"

# Upload file
echo "Uploading file..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/upload" \
  -F "file=@document.pdf")
FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id')
echo "File ID: $FILE_ID"

# Chat with file
echo "Chatting with file..."
curl -X POST "$BASE_URL/api/v1/chat/multimodal" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Summarize this document\"}
    ],
    \"file_ids\": [\"$FILE_ID\"]
  }" | jq '.choices[0].message.content'

# Health check
echo "Health check..."
curl -s "$BASE_URL/health" | jq

# Performance metrics
echo "Performance metrics..."
curl -s "$BASE_URL/api/v1/performance/metrics" | jq '.performance_metrics.cache_stats'
```

## 📚 Advanced Usage

### Batch Processing

```python
import asyncio
import aiohttp

async def process_files_batch(file_paths):
    async with aiohttp.ClientSession() as session:
        # Upload all files concurrently
        upload_tasks = [
            upload_file_async(session, path) for path in file_paths
        ]
        file_results = await asyncio.gather(*upload_tasks)
        
        # Process all files in a single multimodal request
        file_ids = [result['id'] for result in file_results]
        
        chat_data = {
            "messages": [
                {"role": "user", "content": "Analyze and compare all these documents"}
            ],
            "file_ids": file_ids
        }
        
        async with session.post(
            "http://38.242.229.78:8001/api/v1/chat/multimodal",
            json=chat_data
        ) as response:
            return await response.json()

async def upload_file_async(session, file_path):
    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f)
        
        async with session.post(
            "http://38.242.229.78:8001/api/v1/upload",
            data=data
        ) as response:
            return await response.json()
```

### Streaming with WebSockets (Future Enhancement)

```python
# Note: WebSocket support is planned for future releases
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'content':
        print(data['content'], end='')

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    # Send chat request
    request = {
        "type": "chat",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True
    }
    ws.send(json.dumps(request))

# Future WebSocket endpoint (not yet implemented)
# ws = websocket.WebSocketApp("ws://38.242.229.78:8001/ws/chat",
#                             on_open=on_open,
#                             on_message=on_message,
#                             on_error=on_error,
#                             on_close=on_close)
# ws.run_forever()
```

## 🔧 Configuration and Customization

### Environment Variables

When running your own instance, you can configure:

```bash
# Security
SECRET_KEY=your-secret-key
API_KEY=your-api-key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Performance
MAX_FILE_SIZE=10485760  # 10MB
CACHE_TTL=3600
ENABLE_REDIS_CACHE=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_PERFORMANCE_MONITORING=true
```

### Custom Model Configuration

```yaml
# For self-hosted deployments
models:
  - name: "custom-llama"
    endpoint: "http://localhost:11434"
    type: "ollama"
    capabilities: ["text", "multimodal"]
  
  - name: "openai-gpt4"
    endpoint: "https://api.openai.com/v1"
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    capabilities: ["text", "images"]
```

## 📞 Support and Resources

### Getting Help

- **Documentation**: http://38.242.229.78:8001/docs
- **Health Status**: http://38.242.229.78:8001/health
- **Performance Metrics**: http://38.242.229.78:8001/api/v1/performance/metrics

### Best Practices

1. **Always check file upload responses** for successful processing
2. **Use streaming for long responses** to improve user experience
3. **Implement proper error handling** with retry logic
4. **Monitor rate limits** and implement backoff strategies
5. **Cache responses** when appropriate to reduce API calls
6. **Use multimodal endpoints** for file-based conversations
7. **Monitor performance metrics** to optimize usage

### Common Integration Patterns

1. **Document Analysis Workflow**: Upload → Process → Chat → Extract insights
2. **Audio Processing Pipeline**: Upload audio → Transcribe → Analyze → Summarize
3. **Multi-file Comparison**: Upload multiple files → Multimodal chat → Compare/contrast
4. **Real-time Streaming**: Send request → Process streaming response → Display incrementally

---

This documentation provides comprehensive coverage of the Autopicker Platform API. For additional examples and advanced use cases, please refer to the interactive documentation at http://38.242.229.78:8001/docs.