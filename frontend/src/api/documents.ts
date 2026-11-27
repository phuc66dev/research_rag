import { API_BASE, request } from './client';
import type { DocumentItem, SourceChunk } from '../features/documents/types';

const id = encodeURIComponent;

export const documentsApi = {
  list: (workspaceId: string, signal?: AbortSignal) =>
    request<DocumentItem[]>(`/workspaces/${id(workspaceId)}/documents`, { signal }),
  upload: (workspaceId: string, file: File, signal?: AbortSignal) =>
    request<DocumentItem>(`/workspaces/${id(workspaceId)}/documents?filename=${id(file.name)}`, {
      method: 'POST', body: file, headers: { 'Content-Type': 'application/pdf' }, signal,
    }),
  status: (documentId: string) => request<DocumentItem>(`/documents/${id(documentId)}/status`),
  retry: (documentId: string) => request<DocumentItem>(`/documents/${id(documentId)}/retry`, {
    method: 'POST',
  }),
  delete: (documentId: string) => request<void>(`/documents/${id(documentId)}`, { method: 'DELETE' }),
  fileUrl: (documentId: string) => `${API_BASE}/documents/${id(documentId)}/file`,
  search: (workspaceId: string, documentIds: string[], query: string, limit = 6) =>
    request<SourceChunk[]>(`/workspaces/${id(workspaceId)}/sources/search`, {
      method: 'POST', body: JSON.stringify({ document_ids: documentIds, query, limit }),
    }),
};
