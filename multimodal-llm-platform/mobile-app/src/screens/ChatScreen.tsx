import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { chatAPI, ChatRequest, ChatResponse, UploadResponse } from '../services/api';
import { Message, AttachedFile } from '../types';

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  return (
    <View style={[
      styles.messageBubble,
      isUser ? styles.userBubble : styles.assistantBubble
    ]}>
      <Text style={[
        styles.messageText,
        isUser ? styles.userText : styles.assistantText
      ]}>
        {message.content}
      </Text>
      <Text style={styles.timestamp}>
        {new Date(message.timestamp).toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        })}
      </Text>
    </View>
  );
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. I can help you with questions, analyze documents, transcribe audio, and more. How can I help you today?',
      timestamp: new Date(),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  
  const flatListRef = useRef<FlatList>(null);
  const queryClient = useQueryClient();

  // Scroll to bottom when new messages are added
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, []);

  const chatMutation = useMutation({
    mutationFn: async (request: ChatRequest): Promise<ChatResponse> => {
      return chatAPI.sendMessage(request);
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: data.id,
        role: 'assistant',
        content: data.choices[0]?.message?.content || 'Sorry, I couldn\'t generate a response.',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      scrollToBottom();
    },
    onError: (error: any) => {
      console.error('Chat error:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to send message. Please try again.',
        [{ text: 'OK' }]
      );
      
      // Remove the loading message on error
      setMessages(prev => prev.filter(msg => msg.id !== 'loading'));
    },
  });

  const handleSendMessage = useCallback(async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    // Add user message and loading indicator
    const loadingMessage: Message = {
      id: 'loading',
      role: 'assistant',
      content: 'Thinking...',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputText('');
    scrollToBottom();

    // Prepare chat request
    const chatRequest: ChatRequest = {
      messages: [...messages, userMessage].map(msg => ({
        role: msg.role,
        content: msg.content,
      })),
      fileIds: attachedFiles.length > 0 ? attachedFiles.map(f => f.id) : undefined,
      model: 'auto',
      temperature: 0.7,
      max_tokens: 1000,
    };

    chatMutation.mutate(chatRequest);
  }, [inputText, messages, attachedFiles, chatMutation, scrollToBottom]);

  const uploadMutation = useMutation({
    mutationFn: async (file: DocumentPicker.DocumentPickerAsset): Promise<UploadResponse> => {
      if (!file.uri || !file.name || !file.mimeType) {
        throw new Error('Invalid file data');
      }
      return chatAPI.uploadFile(file.uri, file.name, file.mimeType);
    },
    onSuccess: (data, file) => {
      const attachedFile: AttachedFile = {
        id: data.id,
        name: data.original_filename,
        type: data.mime_type,
        size: data.size,
        uri: file.uri,
      };
      
      setAttachedFiles(prev => [...prev, attachedFile]);
      setUploading(false);
      
      Alert.alert(
        'File Uploaded',
        `"${data.original_filename}" has been uploaded successfully!`,
        [{ text: 'OK' }]
      );
    },
    onError: (error: any) => {
      console.error('Upload error:', error);
      setUploading(false);
      Alert.alert(
        'Upload Failed',
        error.message || 'Failed to upload file. Please try again.',
        [{ text: 'OK' }]
      );
    },
  });

  const handleAddFile = useCallback(async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['*/*'], // Allow all file types
        copyToCacheDirectory: true,
        multiple: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const file = result.assets[0];
        
        // Check file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size && file.size > maxSize) {
          Alert.alert(
            'File Too Large',
            'Please select a file smaller than 10MB.',
            [{ text: 'OK' }]
          );
          return;
        }

        setUploading(true);
        uploadMutation.mutate(file);
      }
    } catch (error) {
      console.error('Document picker error:', error);
      Alert.alert(
        'Error',
        'Failed to select file. Please try again.',
        [{ text: 'OK' }]
      );
    }
  }, [uploadMutation]);

  const renderMessage = ({ item }: { item: Message }) => (
    <MessageBubble message={item} />
  );

  const isLoading = chatMutation.isPending;

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        {/* Messages List */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          style={styles.messagesList}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollToBottom}
        />

        {/* Attached Files Indicator */}
        {attachedFiles.length > 0 && (
          <View style={styles.attachedFilesContainer}>
            <View style={styles.attachedFilesList}>
              {attachedFiles.map((file, index) => (
                <View key={file.id} style={styles.attachedFileItem}>
                  <Text style={styles.attachedFileName} numberOfLines={1}>
                    📎 {file.name}
                  </Text>
                  <TouchableOpacity
                    onPress={() => setAttachedFiles(prev => prev.filter(f => f.id !== file.id))}
                    style={styles.removeFileButton}
                  >
                    <Text style={styles.removeFileText}>×</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>
            <TouchableOpacity
              onPress={() => setAttachedFiles([])}
              style={styles.clearFilesButton}
            >
              <Text style={styles.clearFilesText}>Clear All</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <TouchableOpacity
            style={styles.attachButton}
            onPress={handleAddFile}
            disabled={isLoading || uploading}
          >
            {uploading ? (
              <ActivityIndicator size="small" color="#007AFF" />
            ) : (
              <Text style={styles.attachButtonText}>📎</Text>
            )}
          </TouchableOpacity>
          
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type your message..."
            placeholderTextColor="#999"
            multiline
            maxLength={2000}
            editable={!isLoading}
            onSubmitEditing={handleSendMessage}
            blurOnSubmit={false}
          />
          
          <TouchableOpacity
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
            onPress={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <Text style={styles.sendButtonText}>➤</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '80%',
    marginVertical: 4,
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#E9ECEF',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userText: {
    color: '#FFFFFF',
  },
  assistantText: {
    color: '#000000',
  },
  timestamp: {
    fontSize: 11,
    opacity: 0.6,
    marginTop: 4,
  },
  attachedFilesContainer: {
    backgroundColor: '#E3F2FD',
    marginHorizontal: 16,
    marginBottom: 8,
    padding: 8,
    borderRadius: 8,
  },
  attachedFilesList: {
    marginBottom: 8,
  },
  attachedFileItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 6,
    marginBottom: 4,
    borderRadius: 6,
  },
  attachedFileName: {
    flex: 1,
    fontSize: 13,
    color: '#1976D2',
  },
  removeFileButton: {
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeFileText: {
    fontSize: 16,
    color: '#FF3B30',
    fontWeight: 'bold',
  },
  clearFilesButton: {
    alignSelf: 'flex-end',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  clearFilesText: {
    fontSize: 12,
    color: '#1976D2',
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  attachButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  attachButtonText: {
    fontSize: 18,
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#FFFFFF',
    textAlignVertical: 'top',
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#C0C0C0',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
});