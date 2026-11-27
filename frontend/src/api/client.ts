import type { Health, Workspace } from './types';

export const API_BASE = (import.meta.env?.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

export class ApiError extends Error {
  public status: number;
  public detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
    this.name = 'ApiError';
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE + path, {
    credentials: 'include',
    ...init,
    headers: {
      ...(typeof init?.body === 'string' ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>('/health'),
  listWorkspaces: () => request<Workspace[]>('/workspaces'),
  createWorkspace: (name: string, description = '') =>
    request<Workspace>('/workspaces', { method: 'POST', body: JSON.stringify({ name, description }) }),
  renameWorkspace: (id: string, name: string) =>
    request<Workspace>('/workspaces/' + encodeURIComponent(id), {
      method: 'PATCH', body: JSON.stringify({ name }),
    }),
  deleteWorkspace: (id: string) =>
    request<void>('/workspaces/' + encodeURIComponent(id), { method: 'DELETE' }),
};
