import { API_BASE, ApiError } from './client.ts';
import { parseSse } from './events.ts';
import type { ChatEvent, ChatRequest } from './types';

async function* stream(path: string, body: ChatRequest, signal?: AbortSignal): AsyncGenerator<ChatEvent> {
  const response = await fetch(API_BASE + path, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail);
  }
  if (!response.body || !response.headers.get('content-type')?.startsWith('text/event-stream')) {
    throw new Error('Máy chủ không trả về luồng SSE.');
  }
  let completed = false;
  for await (const event of parseSse(response.body)) {
    if (event.event === 'error') throw new Error(event.data.message);
    if (event.event === 'done') {
      completed = true;
      yield event;
      return;
    }
    yield event;
  }
  if (!completed) throw new Error('Hội thoại bị gián đoạn trước khi hoàn tất.');
}

// Explicitly separate mock and real transport; never fall back silently.
export const streamMockChat = (body: ChatRequest, signal?: AbortSignal) =>
  stream('/chat/mock/stream', body, signal);
export const streamChat = (sessionId: string, body: ChatRequest, signal?: AbortSignal) =>
  stream('/chat/sessions/' + encodeURIComponent(sessionId) + '/stream', body, signal);
