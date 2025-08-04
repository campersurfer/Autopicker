# Getting Started with Autopicker Platform

This guide will help you integrate the Autopicker Multimodal LLM Platform into your application in under 10 minutes.

## 🚀 Quick Setup

### Step 1: Verify API Access

First, check that the API is accessible:

```bash
curl http://38.242.229.78:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "multimodal-llm-platform-simple"
}
```

### Step 2: Test Basic Chat

```bash
curl -X POST http://38.242.229.78:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Can you help me?"}
    ]
  }'
```

### Step 3: Install Client Libraries

**Python:**
```bash
pip install requests aiohttp  # For basic HTTP requests
```

**Node.js:**
```bash
npm install axios form-data   # For HTTP requests and file uploads
```

**cURL (CLI):**
Already available on most systems.

## 🔧 Basic Integration

### Python Integration

```python
import requests
import json

class AutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def chat(self, message, stream=False):
        """Send a simple chat message"""
        data = {
            "messages": [{"role": "user", "content": message}],
            "stream": stream
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json=data
        )
        
        if stream:
            return self._handle_stream(response)
        else:
            return response.json()["choices"][0]["message"]["content"]
    
    def upload_and_analyze(self, file_path, question):
        """Upload a file and ask a question about it"""
        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": f}
            upload_response = self.session.post(
                f"{self.base_url}/api/v1/upload",
                files=files
            )
        
        file_id = upload_response.json()["id"]
        
        # Ask question about the file
        data = {
            "messages": [{"role": "user", "content": question}],
            "file_ids": [file_id]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/multimodal",
            json=data
        )
        
        return response.json()["choices"][0]["message"]["content"]
    
    def _handle_stream(self, response):
        """Handle streaming responses"""
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                try:
                    chunk = json.loads(line[6:])
                    if chunk.get('choices'):
                        content = chunk['choices'][0]['delta'].get('content', '')
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

# Usage example
client = AutopickerClient()

# Simple chat
response = client.chat("What is machine learning?")
print(response)

# File analysis
analysis = client.upload_and_analyze("report.pdf", "What are the key findings?")
print(analysis)

# Streaming chat
print("Streaming response:")
for chunk in client.chat("Tell me a short story", stream=True):
    print(chunk, end='', flush=True)
print()
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class AutopickerClient {
    constructor(baseUrl = 'http://38.242.229.78:8001') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: 30000
        });
    }

    async chat(message, stream = false) {
        const data = {
            messages: [{ role: 'user', content: message }],
            stream: stream
        };

        const response = await this.client.post('/api/v1/chat/completions', data);
        
        if (stream) {
            return this._handleStream(response);
        } else {
            return response.data.choices[0].message.content;
        }
    }

    async uploadAndAnalyze(filePath, question) {
        // Upload file
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));

        const uploadResponse = await this.client.post('/api/v1/upload', form, {
            headers: form.getHeaders()
        });

        const fileId = uploadResponse.data.id;

        // Ask question about the file
        const chatData = {
            messages: [{ role: 'user', content: question }],
            file_ids: [fileId]
        };

        const response = await this.client.post('/api/v1/chat/multimodal', chatData);
        return response.data.choices[0].message.content;
    }

    async getModels() {
        const response = await this.client.get('/api/v1/models');
        return response.data.data;
    }

    async getHealth() {
        const response = await this.client.get('/health');
        return response.data;
    }
}

// Usage example
async function example() {
    const client = new AutopickerClient();

    try {
        // Check health
        const health = await client.getHealth();
        console.log('API Status:', health.status);

        // Simple chat
        const response = await client.chat('Explain quantum computing briefly');
        console.log('Chat Response:', response);

        // File analysis (assuming you have a file)
        // const analysis = await client.uploadAndAnalyze('document.pdf', 'Summarize this document');
        // console.log('File Analysis:', analysis);

        // List available models
        const models = await client.getModels();
        console.log('Available Models:', models.map(m => m.id));

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

example();
```

### React Integration

```jsx
import React, { useState, useRef } from 'react';
import axios from 'axios';

const AutopickerChat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const fileInputRef = useRef(null);

    const apiClient = axios.create({
        baseURL: 'http://38.242.229.78:8001',
        timeout: 30000
    });

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiClient.post('/api/v1/upload', formData);
            setUploadedFiles(prev => [...prev, {
                id: response.data.id,
                name: file.name,
                type: response.data.file_type
            }]);
        } catch (error) {
            console.error('Upload failed:', error);
            alert('File upload failed');
        }
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const endpoint = uploadedFiles.length > 0 ? '/api/v1/chat/multimodal' : '/api/v1/chat/completions';
            const data = {
                messages: [...messages, userMessage],
                ...(uploadedFiles.length > 0 && { file_ids: uploadedFiles.map(f => f.id) })
            };

            const response = await apiClient.post(endpoint, data);
            const assistantMessage = {
                role: 'assistant',
                content: response.data.choices[0].message.content
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat failed:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, there was an error processing your request.'
            }]);
        }

        setLoading(false);
    };

    const removeFile = (fileId) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    return (
        <div className="autopicker-chat" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <h2>Autopicker AI Chat</h2>
            
            {/* File Upload Section */}
            <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                />
                <button
                    onClick={() => fileInputRef.current?.click()}
                    style={{ marginRight: '10px', padding: '5px 10px' }}
                >
                    Upload File
                </button>
                
                {uploadedFiles.map(file => (
                    <span key={file.id} style={{ 
                        display: 'inline-block', 
                        margin: '2px', 
                        padding: '2px 8px', 
                        backgroundColor: '#007bff', 
                        color: 'white', 
                        borderRadius: '3px', 
                        fontSize: '12px' 
                    }}>
                        {file.name} ({file.type})
                        <button
                            onClick={() => removeFile(file.id)}
                            style={{ 
                                marginLeft: '5px', 
                                background: 'none', 
                                border: 'none', 
                                color: 'white', 
                                cursor: 'pointer' 
                            }}
                        >
                            ×
                        </button>
                    </span>
                ))}
            </div>

            {/* Messages */}
            <div style={{ 
                height: '400px', 
                overflowY: 'auto', 
                border: '1px solid #ddd', 
                padding: '10px', 
                marginBottom: '10px',
                backgroundColor: 'white'
            }}>
                {messages.map((msg, index) => (
                    <div key={index} style={{ 
                        marginBottom: '10px',
                        padding: '8px',
                        backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
                        borderRadius: '5px'
                    }}>
                        <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong> {msg.content}
                    </div>
                ))}
                {loading && (
                    <div style={{ padding: '8px', fontStyle: 'italic', color: '#666' }}>
                        AI is thinking...
                    </div>
                )}
            </div>

            {/* Input */}
            <div style={{ display: 'flex', gap: '10px' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your message..."
                    style={{ 
                        flex: 1, 
                        padding: '8px', 
                        border: '1px solid #ddd', 
                        borderRadius: '4px' 
                    }}
                    disabled={loading}
                />
                <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    style={{ 
                        padding: '8px 16px', 
                        backgroundColor: '#007bff', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '4px',
                        cursor: loading ? 'not-allowed' : 'pointer'
                    }}
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default AutopickerChat;
```

## 🔗 Common Integration Patterns

### 1. Document Analysis Service

```python
class DocumentAnalyzer:
    def __init__(self):
        self.client = AutopickerClient()
    
    def analyze_document(self, file_path, analysis_type="summary"):
        prompts = {
            "summary": "Provide a comprehensive summary of this document",
            "key_points": "Extract the key points and main findings",
            "action_items": "List any action items or recommendations",
            "questions": "Generate important questions based on this content"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        return self.client.upload_and_analyze(file_path, prompt)
    
    def compare_documents(self, file_paths, comparison_criteria):
        # Upload all files
        file_ids = []
        for path in file_paths:
            with open(path, "rb") as f:
                upload_response = requests.post(
                    "http://38.242.229.78:8001/api/v1/upload",
                    files={"file": f}
                )
                file_ids.append(upload_response.json()["id"])
        
        # Compare documents
        data = {
            "messages": [{"role": "user", "content": f"Compare these documents based on: {comparison_criteria}"}],
            "file_ids": file_ids
        }
        
        response = requests.post(
            "http://38.242.229.78:8001/api/v1/chat/multimodal",
            json=data
        )
        
        return response.json()["choices"][0]["message"]["content"]

# Usage
analyzer = DocumentAnalyzer()
summary = analyzer.analyze_document("contract.pdf", "key_points")
comparison = analyzer.compare_documents(["proposal_a.pdf", "proposal_b.pdf"], "cost and timeline")
```

### 2. Audio Processing Pipeline

```python
class AudioProcessor:
    def __init__(self):
        self.client = AutopickerClient()
    
    def process_audio_workflow(self, audio_file_path, analysis_prompt):
        # Upload audio file
        with open(audio_file_path, "rb") as f:
            upload_response = requests.post(
                "http://38.242.229.78:8001/api/v1/upload",
                files={"file": f}
            )
        
        file_id = upload_response.json()["id"]
        
        # Get transcription explicitly
        transcribe_response = requests.post(
            f"http://38.242.229.78:8001/api/v1/transcribe/{file_id}"
        )
        transcription_data = transcribe_response.json()
        
        # Analyze transcription
        analysis_data = {
            "messages": [{"role": "user", "content": analysis_prompt}],
            "file_ids": [file_id]
        }
        
        analysis_response = requests.post(
            "http://38.242.229.78:8001/api/v1/chat/multimodal-audio",
            json=analysis_data
        )
        
        return {
            "transcription": transcription_data["transcription"],
            "language": transcription_data["language"],
            "duration": transcription_data["duration"],
            "analysis": analysis_response.json()["choices"][0]["message"]["content"]
        }

# Usage
processor = AudioProcessor()
result = processor.process_audio_workflow(
    "meeting.mp3", 
    "Summarize the main topics and decisions made in this meeting"
)
```

### 3. Batch Processing System

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class BatchProcessor:
    def __init__(self, max_concurrent=5):
        self.base_url = "http://38.242.229.78:8001"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_files_batch(self, file_paths, prompt_template):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._process_single_file(session, path, prompt_template)
                for path in file_paths
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful results
            successful_results = [
                result for result in results 
                if not isinstance(result, Exception)
            ]
            
            return successful_results
    
    async def _process_single_file(self, session, file_path, prompt_template):
        async with self.semaphore:
            try:
                # Upload file
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f)
                    
                    async with session.post(f"{self.base_url}/api/v1/upload", data=data) as response:
                        upload_result = await response.json()
                        file_id = upload_result["id"]
                
                # Process with AI
                chat_data = {
                    "messages": [{"role": "user", "content": prompt_template}],
                    "file_ids": [file_id]
                }
                
                async with session.post(f"{self.base_url}/api/v1/chat/multimodal", json=chat_data) as response:
                    chat_result = await response.json()
                    
                    return {
                        "file_path": file_path,
                        "file_id": file_id,
                        "analysis": chat_result["choices"][0]["message"]["content"]
                    }
            
            except Exception as e:
                return {
                    "file_path": file_path,
                    "error": str(e)
                }

# Usage
async def process_documents():
    processor = BatchProcessor(max_concurrent=3)
    
    file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf", "doc4.pdf"]
    prompt = "Analyze this document and extract the main insights and recommendations"
    
    results = await processor.process_files_batch(file_paths, prompt)
    
    for result in results:
        if "error" in result:
            print(f"Error processing {result['file_path']}: {result['error']}")
        else:
            print(f"Processed {result['file_path']}:")
            print(result["analysis"][:200] + "...")
            print("-" * 50)

# Run the batch processing
asyncio.run(process_documents())
```

## 🛡️ Error Handling and Best Practices

### Robust Error Handling

```python
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RobustAutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001", api_key=None):
        self.base_url = base_url
        self.session = self._create_session_with_retries()
        
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
    
    def _create_session_with_retries(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def chat_with_retry(self, message, max_retries=3):
        """Chat with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                data = {
                    "messages": [{"role": "user", "content": message}]
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json=data,
                    timeout=30
                )
                
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limited. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Request failed. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        
        raise Exception(f"Failed after {max_retries} attempts")
    
    def upload_with_validation(self, file_path, max_size_mb=10):
        """Upload file with size validation"""
        import os
        
        # Check file size
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValueError(f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({max_size_mb}MB)")
        
        # Check file type
        allowed_extensions = {
            '.pdf', '.docx', '.txt', '.md', '.xlsx', '.xls', '.csv',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp3', '.wav', '.m4a', '.ogg', '.flac',
            '.py', '.js', '.html', '.css', '.json'
        }
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"File type {file_ext} not supported")
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = self.session.post(
                    f"{self.base_url}/api/v1/upload",
                    files=files,
                    timeout=60  # Longer timeout for uploads
                )
                
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")

# Usage
client = RobustAutopickerClient()

try:
    # Robust chat
    response = client.chat_with_retry("Explain machine learning")
    print(response)
    
    # Safe file upload
    file_info = client.upload_with_validation("document.pdf")
    print(f"Uploaded: {file_info['filename']}")
    
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

### Rate Limit Monitoring

```python
class RateLimitAwareClient:
    def __init__(self, base_url="http://38.242.229.78:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.rate_limit_info = {}
    
    def _update_rate_limit_info(self, response):
        """Extract rate limit info from response headers"""
        self.rate_limit_info = {
            'limit': response.headers.get('X-RateLimit-Limit', 'Unknown'),
            'remaining': response.headers.get('X-RateLimit-Remaining', 'Unknown'),
            'reset': response.headers.get('X-RateLimit-Reset', 'Unknown')
        }
    
    def chat(self, message):
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": message}]}
        )
        
        self._update_rate_limit_info(response)
        
        if response.status_code == 429:
            reset_time = int(self.rate_limit_info.get('reset', 0))
            wait_time = max(0, reset_time - int(time.time()))
            raise Exception(f"Rate limit exceeded. Reset in {wait_time} seconds")
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def get_rate_limit_status(self):
        """Get current rate limit status"""
        return self.rate_limit_info

# Usage
client = RateLimitAwareClient()
response = client.chat("Hello!")
print(f"Rate limit status: {client.get_rate_limit_status()}")
```

## 🎯 Next Steps

After completing this basic integration:

1. **Explore Advanced Features**: Try multimodal processing with different file types
2. **Implement Streaming**: Add real-time response streaming for better UX
3. **Add Monitoring**: Integrate performance and health monitoring
4. **Scale Up**: Implement batch processing for multiple files
5. **Customize**: Adapt the examples to your specific use case

## 📚 Additional Resources

- **Full API Documentation**: [API Reference](../api/README.md)
- **OpenAPI Specification**: [OpenAPI YAML](../api/openapi.yaml)
- **Interactive Docs**: http://38.242.229.78:8001/docs
- **Health Monitoring**: http://38.242.229.78:8001/api/v1/monitoring/health

## 🆘 Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the API server is running at the correct URL
2. **File Upload Fails**: Verify file size is under 10MB and file type is supported
3. **Rate Limit Errors**: Implement backoff and retry logic
4. **Timeout Errors**: Increase timeout values for large file processing

### Getting Help

If you encounter issues:
1. Check the health endpoint: `http://38.242.229.78:8001/health`
2. Verify your request format matches the examples
3. Check the interactive documentation for parameter details
4. Monitor rate limits and implement appropriate delays

This should get you started with integrating the Autopicker Platform into your application!