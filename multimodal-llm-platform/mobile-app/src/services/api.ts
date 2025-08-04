import axios from 'axios';

// Configuration - in a real app, this would come from environment variables
const API_BASE_URL = 'http://38.242.229.78:8001';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`📱 Mobile API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Mobile API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ Mobile API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Mobile API Response Error:', error.response?.data || error.message);
    
    // Handle specific error cases
    if (error.response?.status === 503) {
      throw new Error('AI service is temporarily unavailable. Please try again in a moment.');
    } else if (error.response?.status === 413) {
      throw new Error('File is too large. Please upload a smaller file.');
    } else if (error.response?.status === 429) {
      throw new Error('Too many requests. Please wait a moment before trying again.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timed out. Please try again.');
    }
    
    return Promise.reject(error);
  }
);

// Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  fileIds?: string[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  id: string;
  object: string;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  files_processed?: number;
}

export interface UploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  size: number;
  mime_type: string;
  content_preview?: string;
  file_type?: string;
}

// API functions
export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const endpoint = request.fileIds && request.fileIds.length > 0 
      ? '/api/v1/chat/multimodal-audio'
      : '/api/v1/chat/completions';
    
    const response = await apiClient.post(endpoint, request);
    return response.data;
  },
  
  uploadFile: async (fileUri: string, fileName: string, mimeType: string): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: mimeType,
    } as any);
    
    const response = await apiClient.post('/api/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  getFiles: async () => {
    const response = await apiClient.get('/api/v1/files');
    return response.data;
  },
  
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;