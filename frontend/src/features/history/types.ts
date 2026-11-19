export interface CitationSource {
  id: string;
  document_id: string;
  document_version?: string | null;
  document_title: string;
  page_number?: number | null;
  snippet: string;
  bbox?: number[] | null;
}

export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'completed' | 'interrupted' | 'error';

export interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources: CitationSource[];
  status: MessageStatus;
  created_at: string;
}

export interface ChatSession {
  id: string;
  workspace_id: string;
  owner_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface CreateSessionPayload {
  workspace_id: string;
  title?: string;
}

export interface PatchSessionPayload {
  title: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  hasMore: boolean;
  limit: number;
  offset: number;
}

export interface ListSessionsParams {
  workspaceId?: string;
  query?: string;
  limit?: number;
  offset?: number;
}
