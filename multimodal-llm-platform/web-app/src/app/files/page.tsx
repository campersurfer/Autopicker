import { FileManager } from '@/components/FileManager'

export default function FilesPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">File Manager</h1>
        <p className="text-gray-600 mt-2">
          View and manage your uploaded files
        </p>
      </div>
      
      <FileManager />
    </div>
  )
}