'use client'

import { useEffect, useState } from 'react'
import { ComputerDesktopIcon } from '@heroicons/react/24/outline'

interface StreamingMessageProps {
  content: string
  isStreaming: boolean
  timestamp: Date
}

export function StreamingMessage({ content, isStreaming, timestamp }: StreamingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('')
  const [showCursor, setShowCursor] = useState(true)

  // Update displayed content when new content arrives
  useEffect(() => {
    setDisplayedContent(content)
  }, [content])

  // Cursor blinking effect
  useEffect(() => {
    if (!isStreaming) {
      setShowCursor(false)
      return
    }

    const interval = setInterval(() => {
      setShowCursor(prev => !prev)
    }, 530)

    return () => clearInterval(interval)
  }, [isStreaming])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="flex max-w-3xl">
        {/* Avatar */}
        <div className="flex-shrink-0 mr-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-600">
            <ComputerDesktopIcon className="w-5 h-5" />
          </div>
        </div>

        {/* Message Content */}
        <div className="flex flex-col items-start">
          <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-white border border-gray-200 text-gray-900">
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {displayedContent}
              {isStreaming && (
                <span 
                  className={`inline-block w-2 h-5 bg-blue-600 ml-1 transition-opacity duration-100 ${
                    showCursor ? 'opacity-100' : 'opacity-0'
                  }`}
                  style={{ animation: showCursor ? 'none' : undefined }}
                />
              )}
            </div>
          </div>
          
          {/* Timestamp and streaming indicator */}
          <div className="text-xs text-gray-500 mt-1 ml-2 flex items-center space-x-2">
            <span>{formatTime(timestamp)}</span>
            {isStreaming && (
              <>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"></div>
                    <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-blue-600">streaming</span>
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}