import { useState, useCallback } from 'react'
import { streamChatCompletion } from '@/lib/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface StreamingChatRequest {
  messages: ChatMessage[]
  fileIds?: string[]
  model?: string
  temperature?: number
  max_tokens?: number
}

export function useStreamingChat() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const streamChat = useCallback(async (
    request: StreamingChatRequest,
    onChunk: (content: string) => void,
    onComplete: (finalContent: string) => void
  ) => {
    setIsStreaming(true)
    setError(null)

    let accumulatedContent = ''

    const endpoint = request.fileIds && request.fileIds.length > 0 
      ? '/api/v1/chat/multimodal-audio'
      : '/api/v1/chat/completions'

    await streamChatCompletion(
      endpoint,
      request as unknown as Record<string, unknown>,
      (chunk: string) => {
        accumulatedContent += chunk
        onChunk(chunk)
      },
      (error: string) => {
        setError(error)
        setIsStreaming(false)
      },
      () => {
        setIsStreaming(false)
        onComplete(accumulatedContent)
      }
    )
  }, [])

  return {
    streamChat,
    isStreaming,
    error,
  }
}