import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { chatAPI, UploadResponse } from '../services/api';
import { FileInfo } from '../types';

interface FileItemProps {
  file: FileInfo;
  onPress: () => void;
  onDelete: () => void;
}

function FileItem({ file, onPress, onDelete }: FileItemProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return '📄';
      case 'doc':
      case 'docx': return '📝';
      case 'xls':
      case 'xlsx': return '📊';
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif': return '🖼️';
      case 'mp3':
      case 'wav':
      case 'aac': return '🎵';
      case 'mp4':
      case 'mov':
      case 'avi': return '🎬';
      default: return '📁';
    }
  };

  return (
    <TouchableOpacity style={styles.fileItem} onPress={onPress}>
      <View style={styles.fileIcon}>
        <Text style={styles.fileIconText}>{getFileIcon(file.filename)}</Text>
      </View>
      
      <View style={styles.fileInfo}>
        <Text style={styles.fileName} numberOfLines={2}>
          {file.filename}
        </Text>
        <Text style={styles.fileDetails}>
          {formatFileSize(file.size)} • {formatDate(file.created_at)}
        </Text>
      </View>
      
      <TouchableOpacity
        style={styles.deleteButton}
        onPress={onDelete}
      >
        <Text style={styles.deleteButtonText}>🗑️</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );
}

export default function FilesScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: files,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['files'],
    queryFn: async () => {
      const response = await chatAPI.getFiles();
      return response.files || [];
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: DocumentPicker.DocumentPickerAsset): Promise<UploadResponse> => {
      if (!file.uri || !file.name || !file.mimeType) {
        throw new Error('Invalid file data');
      }
      return chatAPI.uploadFile(file.uri, file.name, file.mimeType);
    },
    onSuccess: (data) => {
      setUploading(false);
      queryClient.invalidateQueries({ queryKey: ['files'] });
      
      Alert.alert(
        'Upload Successful',
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

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const handleFilePress = (file: FileInfo) => {
    Alert.alert(
      file.filename,
      `Size: ${formatFileSize(file.size)}\nUploaded: ${new Date(file.created_at * 1000).toLocaleString()}\nPath: ${file.path}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Use in Chat', onPress: () => handleUseInChat(file) },
      ]
    );
  };

  const handleUseInChat = (file: FileInfo) => {
    // TODO: Navigate to chat with file attached
    Alert.alert(
      'Coming Soon',
      'File selection for chat will be available soon!',
      [{ text: 'OK' }]
    );
  };

  const handleDeleteFile = (file: FileInfo) => {
    Alert.alert(
      'Delete File',
      `Are you sure you want to delete "${file.filename}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: () => confirmDeleteFile(file)
        },
      ]
    );
  };

  const confirmDeleteFile = async (file: FileInfo) => {
    // TODO: Implement file deletion API
    Alert.alert(
      'Feature Coming Soon',
      'File deletion will be available in a future update.',
      [{ text: 'OK' }]
    );
  };

  const handleUploadFile = async () => {
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
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const renderFile = ({ item }: { item: FileInfo }) => (
    <FileItem
      file={item}
      onPress={() => handleFilePress(item)}
      onDelete={() => handleDeleteFile(item)}
    />
  );

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>Failed to load files</Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]} 
          onPress={handleUploadFile}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.uploadButtonText}>📤 Upload File</Text>
          )}
        </TouchableOpacity>
      </View>

      {files && files.length > 0 ? (
        <FlatList
          data={files}
          keyExtractor={(item) => item.path}
          renderItem={renderFile}
          style={styles.filesList}
          contentContainerStyle={styles.filesContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor="#007AFF"
            />
          }
        />
      ) : (
        <View style={styles.centerContent}>
          {isLoading ? (
            <Text style={styles.loadingText}>Loading files...</Text>
          ) : (
            <>
              <Text style={styles.emptyStateTitle}>No files uploaded</Text>
              <Text style={styles.emptyStateText}>
                Upload documents, images, or audio files to get started
              </Text>
              <TouchableOpacity style={styles.primaryButton} onPress={handleUploadFile}>
                <Text style={styles.primaryButtonText}>Upload Your First File</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
  },
  uploadButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  uploadButtonDisabled: {
    backgroundColor: '#C0C0C0',
  },
  filesList: {
    flex: 1,
  },
  filesContent: {
    padding: 16,
  },
  fileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginBottom: 8,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  fileIcon: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  fileIconText: {
    fontSize: 24,
  },
  fileInfo: {
    flex: 1,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#000000',
    marginBottom: 4,
  },
  fileDetails: {
    fontSize: 14,
    color: '#666666',
  },
  deleteButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 20,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#666666',
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    marginBottom: 16,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});