# Code Snippets & Examples

Ready-to-use code examples for integrating with the Autopicker Platform across different programming languages and frameworks.

## 🐍 Python Examples

### Basic Chat Client

```python
import requests
import json

class AutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def chat(self, message):
        """Send a simple chat message"""
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": message}]
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def upload_file(self, file_path):
        """Upload a file and return file info"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(f"{self.base_url}/api/v1/upload", files=files)
        response.raise_for_status()
        return response.json()
    
    def analyze_document(self, file_path, question):
        """Upload and analyze a document in one step"""
        # Upload file
        file_info = self.upload_file(file_path)
        
        # Ask question about the file
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/multimodal",
            json={
                "messages": [{"role": "user", "content": question}],
                "file_ids": [file_info["id"]]
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# Usage example
client = AutopickerClient()

# Simple chat
response = client.chat("What is artificial intelligence?")
print(response)

# Document analysis
analysis = client.analyze_document("report.pdf", "What are the key findings?")
print(analysis)
```

### Streaming Responses

```python
import requests
import json

def stream_chat(message, base_url="http://38.242.229.78:8001"):
    """Stream chat responses in real-time"""
    response = requests.post(
        f"{base_url}/api/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": message}],
            "stream": True
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line and line.startswith(b'data: '):
            try:
                chunk = json.loads(line[6:])
                if chunk.get('choices') and chunk['choices'][0]['delta'].get('content'):
                    content = chunk['choices'][0]['delta']['content']
                    print(content, end='', flush=True)
                    yield content
            except json.JSONDecodeError:
                continue

# Usage
print("Streaming response:")
for chunk in stream_chat("Tell me about quantum computing"):
    pass  # Content is printed in real-time
print("\nDone!")
```

### Async Processing

```python
import asyncio
import aiohttp
import aiofiles

class AsyncAutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001"):
        self.base_url = base_url
    
    async def chat(self, message):
        """Async chat request"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": message}]}
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def process_multiple_files(self, file_paths, question):
        """Process multiple files concurrently"""
        # Upload all files concurrently
        upload_tasks = [self.upload_file_async(path) for path in file_paths]
        file_results = await asyncio.gather(*upload_tasks)
        
        # Get file IDs
        file_ids = [result["id"] for result in file_results]
        
        # Analyze all files together
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat/multimodal",
                json={
                    "messages": [{"role": "user", "content": question}],
                    "file_ids": file_ids
                }
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def upload_file_async(self, file_path):
        """Async file upload"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f)
                
                async with session.post(
                    f"{self.base_url}/api/v1/upload",
                    data=data
                ) as response:
                    return await response.json()

# Usage
async def main():
    client = AsyncAutopickerClient()
    
    # Process multiple files
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    result = await client.process_multiple_files(
        files, 
        "Compare these documents and identify key differences"
    )
    print(result)

# Run async function
asyncio.run(main())
```

### Error Handling & Retries

```python
import requests
import time
import random
from functools import wraps

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while x <= retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited
                        wait_time = (backoff_in_seconds * 2 ** x) + random.uniform(0, 1)
                        print(f"Rate limited. Waiting {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                        x += 1
                    else:
                        raise
                except requests.exceptions.RequestException as e:
                    if x == retries:
                        raise
                    wait_time = (backoff_in_seconds * 2 ** x) + random.uniform(0, 1)
                    print(f"Request failed. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    x += 1
        return wrapper
    return decorator

class RobustAutopickerClient:
    def __init__(self, base_url="http://38.242.229.78:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    @retry_with_backoff(retries=3)
    def chat_with_retry(self, message):
        """Chat with automatic retry logic"""
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": message}]},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def validate_file(self, file_path, max_size_mb=10):
        """Validate file before upload"""
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValueError(f"File too large: {file_size / 1024 / 1024:.2f}MB > {max_size_mb}MB")
        
        allowed_extensions = {'.pdf', '.docx', '.txt', '.jpg', '.png', '.mp3', '.wav'}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    @retry_with_backoff(retries=2)
    def upload_with_validation(self, file_path):
        """Upload file with validation and retry"""
        self.validate_file(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(
                f"{self.base_url}/api/v1/upload",
                files=files,
                timeout=60
            )
        
        response.raise_for_status()
        return response.json()

# Usage
client = RobustAutopickerClient()

try:
    response = client.chat_with_retry("Explain machine learning")
    print(response)
    
    file_info = client.upload_with_validation("document.pdf")
    print(f"Uploaded: {file_info['filename']}")
    
except ValueError as e:
    print(f"Validation error: {e}")
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
```

## 🌐 JavaScript/Node.js Examples

### Basic Client

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

    async chat(message) {
        const response = await this.client.post('/api/v1/chat/completions', {
            messages: [{ role: 'user', content: message }]
        });
        return response.data.choices[0].message.content;
    }

    async uploadFile(filePath) {
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));

        const response = await this.client.post('/api/v1/upload', form, {
            headers: form.getHeaders()
        });
        return response.data;
    }

    async analyzeDocument(filePath, question) {
        // Upload file
        const fileInfo = await this.uploadFile(filePath);
        
        // Analyze with question
        const response = await this.client.post('/api/v1/chat/multimodal', {
            messages: [{ role: 'user', content: question }],
            file_ids: [fileInfo.id]
        });
        
        return response.data.choices[0].message.content;
    }

    async streamChat(message, onChunk) {
        const response = await this.client.post('/api/v1/chat/completions', {
            messages: [{ role: 'user', content: message }],
            stream: true
        }, {
            responseType: 'stream'
        });

        response.data.on('data', (chunk) => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.choices && data.choices[0].delta.content) {
                            onChunk(data.choices[0].delta.content);
                        }
                    } catch (e) {
                        // Ignore parsing errors
                    }
                }
            }
        });
    }
}

// Usage examples
async function examples() {
    const client = new AutopickerClient();

    try {
        // Simple chat
        const response = await client.chat('What is machine learning?');
        console.log('Chat response:', response);

        // Document analysis
        const analysis = await client.analyzeDocument('report.pdf', 'Summarize the key findings');
        console.log('Document analysis:', analysis);

        // Streaming chat
        console.log('Streaming response:');
        await client.streamChat('Tell me about quantum computing', (chunk) => {
            process.stdout.write(chunk);
        });
        console.log('\nDone!');

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

examples();
```

### Express.js API Wrapper

```javascript
const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const app = express();
const upload = multer({ dest: 'uploads/' });

const AUTOPICKER_BASE_URL = 'http://38.242.229.78:8001';

app.use(express.json());

// Simple chat endpoint
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        const response = await axios.post(`${AUTOPICKER_BASE_URL}/api/v1/chat/completions`, {
            messages: [{ role: 'user', content: message }]
        });
        
        res.json({ response: response.data.choices[0].message.content });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// File upload and analysis
app.post('/api/analyze', upload.single('file'), async (req, res) => {
    try {
        const { question = 'Analyze this document' } = req.body;
        const filePath = req.file.path;
        
        // Upload to Autopicker
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));
        
        const uploadResponse = await axios.post(`${AUTOPICKER_BASE_URL}/api/v1/upload`, form, {
            headers: form.getHeaders()
        });
        
        // Analyze document
        const analysisResponse = await axios.post(`${AUTOPICKER_BASE_URL}/api/v1/chat/multimodal`, {
            messages: [{ role: 'user', content: question }],
            file_ids: [uploadResponse.data.id]
        });
        
        // Cleanup temp file
        fs.unlinkSync(filePath);
        
        res.json({
            filename: req.file.originalname,
            analysis: analysisResponse.data.choices[0].message.content
        });
        
    } catch (error) {
        // Cleanup temp file on error
        if (req.file) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ error: error.message });
    }
});

// Streaming chat endpoint
app.post('/api/chat/stream', (req, res) => {
    const { message } = req.body;
    
    res.writeHead(200, {
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked'
    });
    
    axios.post(`${AUTOPICKER_BASE_URL}/api/v1/chat/completions`, {
        messages: [{ role: 'user', content: message }],
        stream: true
    }, {
        responseType: 'stream'
    }).then(response => {
        response.data.on('data', (chunk) => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.choices && data.choices[0].delta.content) {
                            res.write(data.choices[0].delta.content);
                        }
                    } catch (e) {
                        // Ignore parsing errors
                    }
                }
            }
        });
        
        response.data.on('end', () => {
            res.end();
        });
    }).catch(error => {
        res.write(`Error: ${error.message}`);
        res.end();
    });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

## ⚛️ React Examples

### Chat Component with File Upload

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

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await apiClient.post('/api/v1/upload', formData);
            setUploadedFiles(prev => [...prev, {
                id: response.data.id,
                name: file.name,
                type: response.data.file_type
            }]);
        } catch (error) {
            console.error('Upload failed:', error);
            alert('File upload failed');
        } finally {
            setLoading(false);
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
        } finally {
            setLoading(false);
        }
    };

    const removeFile = (fileId) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    return (
        <div className="max-w-4xl mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Autopicker AI Chat</h1>
            
            {/* File Upload Section */}
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    className="hidden"
                />
                <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                    {loading ? 'Uploading...' : 'Upload File'}
                </button>
                
                {uploadedFiles.length > 0 && (
                    <div className="mt-2">
                        {uploadedFiles.map(file => (
                            <span key={file.id} className="inline-block m-1 px-3 py-1 bg-blue-100 rounded-full text-sm">
                                {file.name} ({file.type})
                                <button
                                    onClick={() => removeFile(file.id)}
                                    className="ml-2 text-red-500 hover:text-red-700"
                                >
                                    ×
                                </button>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Messages */}
            <div className="h-96 overflow-y-auto border rounded-lg p-4 mb-4 bg-white">
                {messages.map((msg, index) => (
                    <div key={index} className={`mb-4 p-3 rounded-lg ${
                        msg.role === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-100 mr-8'
                    }`}>
                        <div className="font-semibold text-sm mb-1">
                            {msg.role === 'user' ? 'You' : 'AI'}
                        </div>
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                ))}
                {loading && (
                    <div className="text-center text-gray-500">
                        AI is thinking...
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your message..."
                    className="flex-1 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                />
                <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default AutopickerChat;
```

### Streaming Response Hook

```jsx
import { useState, useCallback } from 'react';

export const useAutopickerStream = (baseUrl = 'http://38.242.229.78:8001') => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamedContent, setStreamedContent] = useState('');

    const streamChat = useCallback(async (message, onChunk) => {
        setIsStreaming(true);
        setStreamedContent('');

        try {
            const response = await fetch(`${baseUrl}/api/v1/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: [{ role: 'user', content: message }],
                    stream: true
                })
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.choices && data.choices[0].delta.content) {
                                const content = data.choices[0].delta.content;
                                setStreamedContent(prev => prev + content);
                                onChunk?.(content);
                            }
                        } catch (e) {
                            // Ignore parsing errors
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Streaming error:', error);
        } finally {
            setIsStreaming(false);
        }
    }, [baseUrl]);

    return { streamChat, isStreaming, streamedContent };
};

// Usage in component
const StreamingChatComponent = () => {
    const { streamChat, isStreaming, streamedContent } = useAutopickerStream();
    const [input, setInput] = useState('');

    const handleSend = () => {
        streamChat(input, (chunk) => {
            console.log('Received chunk:', chunk);
        });
        setInput('');
    };

    return (
        <div>
            <div className="h-64 overflow-y-auto border p-4 mb-4">
                {streamedContent && (
                    <div className="whitespace-pre-wrap">{streamedContent}</div>
                )}
                {isStreaming && (
                    <div className="text-gray-500">AI is responding...</div>
                )}
            </div>
            <div className="flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 p-2 border rounded"
                    disabled={isStreaming}
                />
                <button 
                    onClick={handleSend}
                    disabled={isStreaming || !input.trim()}
                    className="px-4 py-2 bg-blue-500 text-white rounded"
                >
                    Send
                </button>
            </div>
        </div>
    );
};
```

## 🐹 Go Examples

### Basic Go Client

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
    "os"
    "path/filepath"
    "time"
)

type AutopickerClient struct {
    BaseURL string
    Client  *http.Client
}

type ChatMessage struct {
    Role    string `json:"role"`
    Content string `json:"content"`
}

type ChatRequest struct {
    Messages []ChatMessage `json:"messages"`
    Stream   bool          `json:"stream,omitempty"`
}

type ChatResponse struct {
    Choices []struct {
        Message struct {
            Content string `json:"content"`
        } `json:"message"`
    } `json:"choices"`
}

type UploadResponse struct {
    ID       string `json:"id"`
    Filename string `json:"filename"`
    FileType string `json:"file_type"`
}

func NewAutopickerClient(baseURL string) *AutopickerClient {
    return &AutopickerClient{
        BaseURL: baseURL,
        Client: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *AutopickerClient) Chat(message string) (string, error) {
    req := ChatRequest{
        Messages: []ChatMessage{
            {Role: "user", Content: message},
        },
    }

    jsonData, err := json.Marshal(req)
    if err != nil {
        return "", err
    }

    resp, err := c.Client.Post(
        c.BaseURL+"/api/v1/chat/completions",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    var chatResp ChatResponse
    if err := json.NewDecoder(resp.Body).Decode(&chatResp); err != nil {
        return "", err
    }

    if len(chatResp.Choices) == 0 {
        return "", fmt.Errorf("no response choices")
    }

    return chatResp.Choices[0].Message.Content, nil
}

func (c *AutopickerClient) UploadFile(filePath string) (*UploadResponse, error) {
    file, err := os.Open(filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()

    var b bytes.Buffer
    writer := multipart.NewWriter(&b)
    
    part, err := writer.CreateFormFile("file", filepath.Base(filePath))
    if err != nil {
        return nil, err
    }
    
    _, err = io.Copy(part, file)
    if err != nil {
        return nil, err
    }
    
    writer.Close()

    resp, err := c.Client.Post(
        c.BaseURL+"/api/v1/upload",
        writer.FormDataContentType(),
        &b,
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var uploadResp UploadResponse
    if err := json.NewDecoder(resp.Body).Decode(&uploadResp); err != nil {
        return nil, err
    }

    return &uploadResp, nil
}

func (c *AutopickerClient) AnalyzeDocument(filePath, question string) (string, error) {
    // Upload file
    uploadResp, err := c.UploadFile(filePath)
    if err != nil {
        return "", err
    }

    // Analyze with multimodal endpoint
    req := struct {
        Messages []ChatMessage `json:"messages"`
        FileIDs  []string      `json:"file_ids"`
    }{
        Messages: []ChatMessage{
            {Role: "user", Content: question},
        },
        FileIDs: []string{uploadResp.ID},
    }

    jsonData, err := json.Marshal(req)
    if err != nil {
        return "", err
    }

    resp, err := c.Client.Post(
        c.BaseURL+"/api/v1/chat/multimodal",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    var chatResp ChatResponse
    if err := json.NewDecoder(resp.Body).Decode(&chatResp); err != nil {
        return "", err
    }

    if len(chatResp.Choices) == 0 {
        return "", fmt.Errorf("no response choices")
    }

    return chatResp.Choices[0].Message.Content, nil
}

func main() {
    client := NewAutopickerClient("http://38.242.229.78:8001")

    // Simple chat
    response, err := client.Chat("What is machine learning?")
    if err != nil {
        fmt.Printf("Chat error: %v\n", err)
        return
    }
    fmt.Printf("Chat response: %s\n", response)

    // Document analysis
    analysis, err := client.AnalyzeDocument("report.pdf", "What are the key findings?")
    if err != nil {
        fmt.Printf("Analysis error: %v\n", err)
        return
    }
    fmt.Printf("Document analysis: %s\n", analysis)
}
```

## 🔧 Utility Scripts

### Batch Processing Script (Python)

```python
#!/usr/bin/env python3
"""
Batch processing script for multiple documents
Usage: python batch_process.py --files "*.pdf" --question "Summarize this document"
"""

import argparse
import glob
import asyncio
import aiohttp
import json
from pathlib import Path

async def process_file_batch(files, question, base_url="http://38.242.229.78:8001"):
    """Process multiple files concurrently"""
    async with aiohttp.ClientSession() as session:
        # Upload all files
        upload_tasks = []
        for file_path in files:
            upload_tasks.append(upload_file_async(session, file_path, base_url))
        
        file_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
        
        # Process successful uploads
        successful_uploads = []
        for i, result in enumerate(file_results):
            if isinstance(result, Exception):
                print(f"Failed to upload {files[i]}: {result}")
            else:
                successful_uploads.append(result)
        
        if not successful_uploads:
            print("No files uploaded successfully")
            return
        
        # Analyze all files together
        file_ids = [result["id"] for result in successful_uploads]
        
        analysis_data = {
            "messages": [{"role": "user", "content": question}],
            "file_ids": file_ids
        }
        
        async with session.post(
            f"{base_url}/api/v1/chat/multimodal",
            json=analysis_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                analysis = result["choices"][0]["message"]["content"]
                
                print(f"\n{'='*60}")
                print(f"BATCH ANALYSIS RESULTS")
                print(f"{'='*60}")
                print(f"Files processed: {len(successful_uploads)}")
                print(f"Question: {question}")
                print(f"{'='*60}")
                print(analysis)
                print(f"{'='*60}")
                
                return analysis
            else:
                print(f"Analysis failed: {response.status}")

async def upload_file_async(session, file_path, base_url):
    """Upload a single file asynchronously"""
    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=Path(file_path).name)
        
        async with session.post(f"{base_url}/api/v1/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"Uploaded: {file_path} -> {result['id']}")
                return result
            else:
                raise Exception(f"Upload failed with status {response.status}")

def main():
    parser = argparse.ArgumentParser(description="Batch process documents with Autopicker")
    parser.add_argument("--files", required=True, help="File pattern (e.g., '*.pdf' or 'doc1.pdf,doc2.pdf')")
    parser.add_argument("--question", default="Analyze and summarize these documents", help="Question to ask about the documents")
    parser.add_argument("--base-url", default="http://38.242.229.78:8001", help="Autopicker API base URL")
    
    args = parser.parse_args()
    
    # Parse file patterns
    if "," in args.files:
        files = [f.strip() for f in args.files.split(",")]
    else:
        files = glob.glob(args.files)
    
    if not files:
        print(f"No files found matching pattern: {args.files}")
        return
    
    print(f"Found {len(files)} files to process:")
    for f in files:
        print(f"  - {f}")
    
    # Run batch processing
    asyncio.run(process_file_batch(files, args.question, args.base_url))

if __name__ == "__main__":
    main()
```

### Health Check Script (Shell)

```bash
#!/bin/bash
# Health check script for Autopicker Platform
# Usage: ./health_check.sh

BASE_URL="http://38.242.229.78:8001"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Autopicker Platform Health Check"
echo "=================================="

# Basic health check
echo -n "🏥 Basic Health: "
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/health")
HTTP_CODE="${HEALTH_RESPONSE: -3}"
HEALTH_BODY="${HEALTH_RESPONSE%???}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Healthy${NC}"
    STATUS=$(echo "$HEALTH_BODY" | jq -r '.status // "unknown"')
    SERVICE=$(echo "$HEALTH_BODY" | jq -r '.service // "unknown"')
    echo "   Status: $STATUS"
    echo "   Service: $SERVICE"
else
    echo -e "${RED}❌ Failed (HTTP $HTTP_CODE)${NC}"
    exit 1
fi

# System metrics
echo -n "📊 System Metrics: "
METRICS_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/monitoring/health")
HTTP_CODE="${METRICS_RESPONSE: -3}"
METRICS_BODY="${METRICS_RESPONSE%???}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Available${NC}"
    
    CPU=$(echo "$METRICS_BODY" | jq -r '.system_metrics.cpu_percent // "N/A"')
    MEMORY=$(echo "$METRICS_BODY" | jq -r '.system_metrics.memory_percent // "N/A"')
    DISK=$(echo "$METRICS_BODY" | jq -r '.system_metrics.disk_usage_percent // "N/A"')
    
    echo "   CPU Usage: ${CPU}%"
    echo "   Memory Usage: ${MEMORY}%"
    echo "   Disk Usage: ${DISK}%"
    
    # Warn if high usage
    if (( $(echo "$CPU > 80" | bc -l) )); then
        echo -e "   ${YELLOW}⚠️  High CPU usage${NC}"
    fi
    if (( $(echo "$MEMORY > 80" | bc -l) )); then
        echo -e "   ${YELLOW}⚠️  High memory usage${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Unavailable (HTTP $HTTP_CODE)${NC}"
fi

# Test basic chat
echo -n "💬 Chat Endpoint: "
CHAT_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Hello"}]}')
HTTP_CODE="${CHAT_RESPONSE: -3}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed (HTTP $HTTP_CODE)${NC}"
fi

# Test file upload
echo -n "📁 Upload Endpoint: "
# Create a small test file
echo "Test file content" > /tmp/test_file.txt

UPLOAD_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/upload" \
    -F "file=@/tmp/test_file.txt")
HTTP_CODE="${UPLOAD_RESPONSE: -3}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed (HTTP $HTTP_CODE)${NC}"
fi

# Cleanup
rm -f /tmp/test_file.txt

# Performance test
echo -n "⚡ Response Time: "
START_TIME=$(date +%s%N)
curl -s "$BASE_URL/health" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

if [ "$RESPONSE_TIME" -lt 1000 ]; then
    echo -e "${GREEN}✅ ${RESPONSE_TIME}ms${NC}"
elif [ "$RESPONSE_TIME" -lt 3000 ]; then
    echo -e "${YELLOW}⚠️  ${RESPONSE_TIME}ms (slow)${NC}"
else
    echo -e "${RED}❌ ${RESPONSE_TIME}ms (very slow)${NC}"
fi

echo ""
echo "🎯 Summary:"
echo "   API is $([ "$HTTP_CODE" -eq 200 ] && echo -e "${GREEN}accessible${NC}" || echo -e "${RED}not accessible${NC}")"
echo "   Response time: ${RESPONSE_TIME}ms"
echo "   For detailed metrics: $BASE_URL/api/v1/performance/metrics"
echo "   Interactive docs: $BASE_URL/docs"
```

These code snippets provide comprehensive examples for integrating with the Autopicker Platform across different programming languages and use cases. Each example includes error handling, best practices, and real-world usage patterns.