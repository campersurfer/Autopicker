import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

interface UploadResponse {
  id: string
  filename: string
  original_filename: string
  size: number
  mime_type: string
  content_preview?: string
  file_type?: string
}

export function useUploadMutation() {
  return useMutation<UploadResponse, Error, File>({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await apiClient.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      return response.data
    },
  })
}