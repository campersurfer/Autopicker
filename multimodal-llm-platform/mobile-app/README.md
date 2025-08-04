# Autopicker Mobile App

A React Native mobile application for the Autopicker Multimodal LLM Platform.

## Features

- 💬 **Chat Interface**: Mobile-optimized chat with AI assistant
- 📁 **File Management**: Upload and manage documents, images, and audio files  
- ⚙️ **Settings**: App configuration and preferences
- 🔄 **Real-time Sync**: Connects to VPS backend for AI processing

## Tech Stack

- **React Native** with Expo SDK 53
- **TypeScript** for type safety
- **React Navigation** for tab navigation
- **React Query** for API state management
- **Expo Document Picker** for file uploads
- **AsyncStorage** for local data persistence

## Getting Started

### Prerequisites
- Node.js 18+
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator or Android Emulator (or physical device with Expo Go)

### Installation

```bash
# Install dependencies
npm install

# Start the development server
npx expo start

# Run on specific platform
npx expo start --ios
npx expo start --android
```

### Building for Production

```bash
# Build for iOS
npx expo build:ios

# Build for Android  
npx expo build:android
```

## Project Structure

```
mobile-app/
├── App.tsx                 # Root component with navigation
├── src/
│   ├── screens/           # Screen components
│   │   ├── ChatScreen.tsx    # Main chat interface
│   │   ├── FilesScreen.tsx   # File management
│   │   └── SettingsScreen.tsx # App settings
│   ├── services/          # API and external services
│   │   └── api.ts           # Backend API client
│   └── types/             # TypeScript type definitions
│       └── index.ts         # Shared interfaces
├── assets/                # Images and static assets
└── app.json              # Expo configuration
```

## Configuration

The app connects to the backend API at `http://38.242.229.78:8001`. Update the `API_BASE_URL` in `src/services/api.ts` if needed.

## Features Overview

### Chat Screen
- Real-time messaging with AI assistant
- File attachment support (documents, images, audio)
- Message history with timestamps
- Loading states and error handling

### Files Screen  
- Upload files up to 10MB
- View uploaded file details
- File type icons and metadata
- Pull-to-refresh functionality

### Settings Screen
- Connection status monitoring
- App preferences (dark mode, notifications)
- Cache management
- About and support information

## API Integration

The mobile app communicates with the backend through REST APIs:

- `POST /api/v1/chat/completions` - Text-only chat
- `POST /api/v1/chat/multimodal-audio` - Chat with file attachments
- `POST /api/v1/upload` - File upload
- `GET /api/v1/files` - List uploaded files
- `GET /health` - Health check

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `npx expo start -c`
2. **Dependency conflicts**: Run `npx expo install --check`
3. **iOS simulator**: Ensure Xcode Command Line Tools are installed
4. **Android emulator**: Verify Android SDK is properly configured

### Development Notes

- Uses React Native 0.79.5 with new architecture enabled
- TypeScript strict mode for better type safety  
- Expo SDK 53 with native module support
- AsyncStorage for persistent local data

## Contributing

1. Follow existing code patterns and naming conventions
2. Add TypeScript types for all new interfaces
3. Test on both iOS and Android platforms
4. Update this README for new features

## License

Part of the Autopicker Multimodal LLM Platform project.