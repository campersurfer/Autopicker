# Multimodal LLM Platform - Web Application

A modern React/Next.js frontend for the Multimodal LLM Platform, featuring a clean chat interface with file upload capabilities and smart routing integration.

## Features

### 🎯 Smart Chat Interface
- Clean, responsive chat UI with message bubbles
- Real-time conversation with AI models
- Automatic model selection based on request complexity
- Message timestamps and user/assistant avatars

### 📁 File Upload & Processing
- Drag-and-drop file upload with progress indicators
- Support for multiple file types:
  - **Documents**: PDF, DOCX, TXT, MD
  - **Spreadsheets**: XLSX, XLS, CSV
  - **Images**: JPG, PNG, GIF, WebP
  - **Audio**: MP3, WAV, M4A, OGG
- File preview and management
- Automatic file content extraction and analysis

### 🧠 Smart Routing Integration
- Automatic model selection (`model: "auto"`)
- Complexity analysis based on message length and file types
- Real-time routing decisions with transparency

### 🎨 Modern UI/UX
- Built with Tailwind CSS for consistent styling
- Responsive design that works on all devices
- Clean navigation with multiple sections
- Loading states and error handling

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS
- **State Management**: React Query (@tanstack/react-query)
- **HTTP Client**: Axios
- **Icons**: Heroicons
- **File Upload**: react-dropzone

## Pages

### 💬 Chat (/)
Main chat interface with file upload capabilities

### 📂 Files (/files)
File manager to view and manage uploaded files

### 📊 Analytics (/analytics)
Usage statistics and performance metrics (placeholder)

### ⚙️ Settings (/settings)
Configuration and preferences

## Getting Started

First, install dependencies:

```bash
npm install
```

Create a `.env.local` file:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://38.242.229.78:8001

# For local development:
# NEXT_PUBLIC_API_URL=http://localhost:8001
```

Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## API Integration

The frontend integrates with the Multimodal LLM Platform API:

- **Chat Endpoint**: `/api/v1/chat/completions` for text-only chat
- **Multimodal Chat**: `/api/v1/chat/multimodal-audio` for file-enabled chat
- **File Upload**: `/api/v1/upload` for file processing
- **Complexity Analysis**: `/api/v1/analyze-complexity` for routing insights

## Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Architecture

```
src/
├── app/                 # Next.js App Router pages
│   ├── layout.tsx      # Root layout with navigation
│   ├── page.tsx        # Home page (chat interface)
│   ├── providers.tsx   # React Query setup
│   └── */              # Additional pages
├── components/         # Reusable UI components
│   ├── ChatInterface.tsx
│   ├── FileUpload.tsx
│   ├── MessageBubble.tsx
│   └── Navigation.tsx
├── hooks/             # Custom React hooks
│   ├── useChatMutation.ts
│   └── useUploadMutation.ts
└── lib/              # Utilities and configuration
    └── api.ts        # Axios configuration
```

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Implement proper error handling
4. Add loading states for async operations
5. Test responsive design on different screen sizes
