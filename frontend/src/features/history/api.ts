import { API_BASE, request } from '../../api/client';
import type {
  ChatMessage,
  ChatSession,
  ChatSessionDetail,
  CreateSessionPayload,
  ListSessionsParams,
  PaginatedResult,
  PatchSessionPayload,
} from './types';

async function requestPaginated<T>(path: string): Promise<PaginatedResult<T>> {
  const response = await fetch(API_BASE + path, {
    credentials: 'include',
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Lỗi truy xuất dữ liệu.');
  }
  const items: T[] = await response.json();
  const totalHeader = response.headers.get('X-Total-Count');
  const hasMoreHeader = response.headers.get('X-Has-More');
  const limitHeader = response.headers.get('X-Limit');
  const offsetHeader = response.headers.get('X-Offset');

  const limit = limitHeader ? parseInt(limitHeader, 10) : items.length;
  const offset = offsetHeader ? parseInt(offsetHeader, 10) : 0;
  const total = totalHeader ? parseInt(totalHeader, 10) : items.length;
  const hasMore = hasMoreHeader !== null ? hasMoreHeader === 'true' : offset + items.length < total;

  return { items, total, hasMore, limit, offset };
}

export const historyApi = {
  /**
   * List sessions in a specific workspace with pagination.
   */
  listWorkspaceSessions: (
    workspaceId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<PaginatedResult<ChatSession>> => {
    const sp = new URLSearchParams();
    if (params?.limit !== undefined) sp.set('limit', String(params.limit));
    if (params?.offset !== undefined) sp.set('offset', String(params.offset));
    const qs = sp.toString();
    return requestPaginated<ChatSession>(
      `/workspaces/${encodeURIComponent(workspaceId)}/sessions${qs ? `?${qs}` : ''}`
    );
  },

  /**
   * List all sessions owned by user, with optional workspace filter, search query, and pagination.
   */
  listAllSessions: (params?: ListSessionsParams): Promise<PaginatedResult<ChatSession>> => {
    const sp = new URLSearchParams();
    if (params?.workspaceId && params.workspaceId !== 'all') {
      sp.set('workspace_id', params.workspaceId);
    }
    if (params?.query?.trim()) {
      sp.set('query', params.query.trim());
    }
    if (params?.limit !== undefined) {
      sp.set('limit', String(params.limit));
    }
    if (params?.offset !== undefined) {
      sp.set('offset', String(params.offset));
    }
    const qs = sp.toString();
    return requestPaginated<ChatSession>(`/chat/sessions${qs ? `?${qs}` : ''}`);
  },

  /**
   * Create a new chat session.
   */
  createSession: (payload: CreateSessionPayload): Promise<ChatSession> => {
    return request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Get full session detail with messages and citations.
   */
  getSessionDetail: (sessionId: string): Promise<ChatSessionDetail> => {
    return request<ChatSessionDetail>(`/chat/sessions/${encodeURIComponent(sessionId)}`);
  },

  /**
   * Rename session title.
   */
  renameSession: (sessionId: string, title: string): Promise<ChatSession> => {
    const payload: PatchSessionPayload = { title };
    return request<ChatSession>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete a session and its message history.
   */
  deleteSession: (sessionId: string): Promise<void> => {
    return request<void>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
  },

  /**
   * List messages for a session with pagination.
   */
  listMessages: (
    sessionId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<PaginatedResult<ChatMessage>> => {
    const sp = new URLSearchParams();
    if (params?.limit !== undefined) sp.set('limit', String(params.limit));
    if (params?.offset !== undefined) sp.set('offset', String(params.offset));
    const qs = sp.toString();
    return requestPaginated<ChatMessage>(
      `/chat/sessions/${encodeURIComponent(sessionId)}/messages${qs ? `?${qs}` : ''}`
    );
  },
};
