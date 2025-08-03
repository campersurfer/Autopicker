import axios from 'axios'

// Get API URL from environment variable or default to local VPS
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://38.242.229.78:8001'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for file uploads and processing
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('❌ API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message)
    
    // Handle specific error cases
    if (error.response?.status === 503) {
      throw new Error('AI service is temporarily unavailable. Please try again in a moment.')
    } else if (error.response?.status === 413) {
      throw new Error('File is too large. Please upload a smaller file.')
    } else if (error.response?.status === 429) {
      throw new Error('Too many requests. Please wait a moment before trying again.')
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timed out. Please try again.')
    }
    
    return Promise.reject(error)
  }
)

export default apiClient