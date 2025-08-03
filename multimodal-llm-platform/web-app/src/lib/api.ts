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

// Streaming response handler
export async function streamChatCompletion(
  endpoint: string,
  data: Record<string, unknown>,
  onChunk: (content: string) => void,
  onError: (error: string) => void,
  onComplete: () => void
) {
  try {
    console.log(`🔄 Starting stream: ${endpoint}`)
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...data, stream: true }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Streaming not supported')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        console.log('🏁 Stream completed')
        onComplete()
        break
      }

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true })
      
      // Process complete lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.trim() === '') continue
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6) // Remove 'data: ' prefix
          
          if (data === '[DONE]') {
            console.log('✅ Stream finished with [DONE]')
            onComplete()
            return
          }

          try {
            const parsed = JSON.parse(data)
            
            if (parsed.error) {
              onError(parsed.error)
              return
            }
            
            const content = parsed.choices?.[0]?.delta?.content
            if (content) {
              onChunk(content)
            }
          } catch {
            console.warn('Failed to parse chunk:', data)
          }
        }
      }
    }
  } catch (error) {
    console.error('❌ Streaming error:', error)
    onError(error instanceof Error ? error.message : 'Streaming failed')
  }
}

export default apiClient