import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatRequest {
  messages: ChatMessage[]
  fileIds?: string[]
  model?: string
  temperature?: number
  max_tokens?: number
}

interface ChatResponse {
  id: string
  object: string
  model: string
  choices: Array<{
    index: number
    message: {
      role: string
      content: string
    }
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  files_processed?: number
}

export function useChatMutation() {
  return useMutation<ChatResponse, Error, ChatRequest>({
    mutationFn: async (request) => {
      const endpoint = request.fileIds && request.fileIds.length > 0 
        ? '/api/v1/chat/multimodal-audio'
        : '/api/v1/chat/completions'
      
      const response = await apiClient.post(endpoint, request)
      return response.data
    },
  })
}