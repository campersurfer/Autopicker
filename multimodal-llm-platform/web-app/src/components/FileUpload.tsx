'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { DocumentTextIcon, PhotoIcon, MusicalNoteIcon, FilmIcon, DocumentIcon } from '@heroicons/react/24/outline'
import { useUploadMutation } from '@/hooks/useUploadMutation'

interface AttachedFile {
  id: string
  name: string
  type: string
  size: number
}

interface FileUploadProps {
  onFilesUploaded: (files: AttachedFile[]) => void
}

export function FileUpload({ onFilesUploaded }: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<AttachedFile[]>([])
  const uploadMutation = useUploadMutation()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const uploadPromises = acceptedFiles.map(async (file) => {
      try {
        const response = await uploadMutation.mutateAsync(file)
        return {
          id: response.id,
          name: response.original_filename,
          type: response.file_type || 'unknown',
          size: response.size,
        }
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error)
        return null
      }
    })

    const results = await Promise.all(uploadPromises)
    const successfulUploads = results.filter(Boolean) as AttachedFile[]
    
    setUploadedFiles(prev => [...prev, ...successfulUploads])
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
      case 'docx':
      case 'text':
        return <DocumentTextIcon className="w-8 h-8" />
      case 'image':
        return <PhotoIcon className="w-8 h-8" />
      case 'audio':
        return <MusicalNoteIcon className="w-8 h-8" />
      case 'video':
        return <FilmIcon className="w-8 h-8" />
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

  const handleAddFiles = () => {
    if (uploadedFiles.length > 0) {
      onFilesUploaded(uploadedFiles)
      setUploadedFiles([])
    }
  }

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-2">
          <DocumentIcon className="w-12 h-12 text-gray-400 mx-auto" />
          
          {isDragActive ? (
            <p className="text-blue-600 font-medium">Drop files here...</p>
          ) : (
            <>
              <p className="text-gray-600">
                <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
              </p>
              <p className="text-sm text-gray-500">
                PDF, DOCX, TXT, Images, Audio, and more (max 50MB)
              </p>
            </>
          )}
        </div>
      </div>

      {/* Supported File Types */}
      <div className="text-sm text-gray-600">
        <p className="font-medium mb-2">Supported file types:</p>
        <div className="grid grid-cols-2 gap-2">
          <div>📄 Documents: PDF, DOCX, TXT, MD</div>
          <div>📊 Spreadsheets: XLSX, XLS, CSV</div>
          <div>🖼️ Images: JPG, PNG, GIF, WebP</div>
          <div>🎵 Audio: MP3, WAV, M4A, OGG</div>
        </div>
      </div>

      {/* Upload Progress */}
      {uploadMutation.isPending && (
        <div className="text-center py-4">
          <div className="inline-flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">Uploading files...</span>
          </div>
        </div>
      )}

      {/* Uploaded Files Preview */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Uploaded Files:</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {uploadedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg border"
              >
                <div className="text-gray-500 flex-shrink-0">
                  {getFileIcon(file.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {file.type} • {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
            ))}
          </div>
          
          <button
            onClick={handleAddFiles}
            className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add {uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''} to chat
          </button>
        </div>
      )}

      {/* Upload Error */}
      {uploadMutation.isError && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="font-medium">Upload failed</p>
          <p>Please try again or check your file size and format.</p>
        </div>
      )}
    </div>
  )
}