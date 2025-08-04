export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface AttachedFile {
  id: string;
  name: string;
  type: string;
  size: number;
  uri?: string;
}

export interface FileInfo {
  filename: string;
  size: number;
  created_at: number;
  path: string;
}

export interface AppConfig {
  apiBaseUrl: string;
  maxFileSize: number;
  supportedFileTypes: string[];
}

export type RootTabParamList = {
  Chat: undefined;
  Files: undefined;
  Settings: undefined;
};