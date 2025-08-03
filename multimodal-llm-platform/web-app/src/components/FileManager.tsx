'use client'

import { useState, useEffect } from 'react'
import { DocumentTextIcon, PhotoIcon, MusicalNoteIcon, DocumentIcon, TrashIcon } from '@heroicons/react/24/outline'
import { apiClient } from '@/lib/api'

interface FileItem {
  filename: string
  size: number
  created_at: number
  path: string
}

export function FileManager() {
  const [files, setFiles] = useState<FileItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/files')
      setFiles(response.data.files || [])
      setError(null)
    } catch (err) {
      console.error('Failed to fetch files:', err)
      setError('Failed to load files')
    } finally {
      setLoading(false)
    }
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    
    switch (ext) {
      case 'pdf':
      case 'docx':
      case 'txt':
      case 'md':
        return <DocumentTextIcon className="w-8 h-8" />
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'webp':
        return <PhotoIcon className="w-8 h-8" />
      case 'mp3':
      case 'wav':
      case 'm4a':
      case 'ogg':
        return <MusicalNoteIcon className="w-8 h-8" />
      default:
        return <DocumentIcon className="w-8 h-8" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString() + ' ' + 
           new Date(timestamp * 1000).toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">Loading files...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={fetchFiles}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="text-center py-12">
        <DocumentIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 mb-4">No files uploaded yet</p>
        <p className="text-sm text-gray-500">Upload files through the chat interface to see them here</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {files.length} file{files.length !== 1 ? 's' : ''}
          </h3>
          <button
            onClick={fetchFiles}
            className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {files.map((file, index) => (
          <div key={index} className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center space-x-4">
              <div className="text-gray-500 flex-shrink-0">
                {getFileIcon(file.filename)}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.filename}
                </p>
                <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                  <span>{formatFileSize(file.size)}</span>
                  <span>•</span>
                  <span>{formatDate(file.created_at)}</span>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  className="text-gray-400 hover:text-red-500 transition-colors"
                  title="Delete file"
                  onClick={() => {
                    // TODO: Implement file deletion
                    alert('File deletion will be implemented in a future update')
                  }}
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}