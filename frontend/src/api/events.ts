import type { ChatEvent } from './types.ts';

const events = new Set(['status', 'citations', 'token', 'done', 'error']);


function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function validCitation(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return ['id', 'document_id', 'document_version', 'document_title', 'snippet']
    .every(key => typeof value[key] === 'string')
    && Number.isInteger(value.page_number) && Number(value.page_number) >= 1
    && (value.bbox === null || (Array.isArray(value.bbox) && value.bbox.length === 4
      && value.bbox.every(item => typeof item === 'number' && Number.isFinite(item))));
}

function validPayload(event: string, value: unknown): boolean {
  if (!isRecord(value)) return false;
  switch (event) {
    case 'status': return typeof value.stage === 'string' && value.stage.length > 0;
    case 'citations': return Array.isArray(value.citations) && value.citations.every(validCitation);
    case 'token': return typeof value.text === 'string';
    case 'done': return typeof value.message_id === 'string' && value.message_id.length > 0
      && typeof value.provider === 'string' && value.provider.length > 0;
    case 'error': return typeof value.code === 'string' && typeof value.message === 'string';
    default: return false;
  }
}

/** Handles arbitrary UTF-8 byte boundaries and either LF or CRLF framing. */
export async function* parseSse(stream: ReadableStream<Uint8Array>): AsyncGenerator<ChatEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let buffer = '';
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let boundary: RegExpMatchArray | null;
      while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
        const block = buffer.slice(0, boundary.index);
        buffer = buffer.slice(boundary.index! + boundary[0].length);
        let event = 'message';
        const data: string[] = [];
        for (const line of block.split(/\r?\n/)) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
        }
        if (!data.length || !events.has(event)) continue;
        const payload: unknown = JSON.parse(data.join('\n'));
        if (!validPayload(event, payload)) throw new Error('Dữ liệu SSE không hợp lệ.');
        yield { event, data: payload } as ChatEvent;
      }
      if (done) break;
    }
    if (buffer.trim() && !buffer.trim().startsWith(':')) {
      throw new Error('Luồng SSE kết thúc khi sự kiện chưa hoàn tất.');
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
