'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChartBarIcon, ChatBubbleLeftRightIcon, DocumentTextIcon, Cog6ToothIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Chat', href: '/', icon: ChatBubbleLeftRightIcon },
  { name: 'Files', href: '/files', icon: DocumentTextIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Monitoring', href: '/monitoring', icon: ComputerDesktopIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">ML</span>
              </div>
              <span className="ml-2 text-xl font-semibold text-gray-900">
                Multimodal LLM Platform
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-8">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <item.icon className="w-5 h-5 mr-2" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}