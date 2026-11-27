import assert from 'node:assert/strict';
import test from 'node:test';
import { streamChat } from './chat.ts';

const body = { workspace_id: 'workspace', document_ids: ['source'], query: 'Câu hỏi' };
const encode = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;

test('authenticated chat preserves source snapshot and consumes done', async () => {
  const original = globalThis.fetch;
  let sent: RequestInit | undefined;
  globalThis.fetch = async (url, init) => {
    assert.equal(url, '/api/v1/chat/sessions/session%2Fid/stream');
    sent = init;
    return new Response(encode('token', { text: 'Tiếng Việt' }) + encode('done', {
      message_id: 'stored-answer', provider: 'openai-compatible', mock: false,
    }), { headers: { 'Content-Type': 'text/event-stream' } });
  };
  try {
    const events = [];
    for await (const event of streamChat('session/id', body)) events.push(event);
    assert.equal(sent?.credentials, 'include');
    assert.deepEqual(JSON.parse(sent?.body as string), body);
    assert.deepEqual(events.map(event => event.event), ['token', 'done']);
  } finally { globalThis.fetch = original; }
});

test('missing done and provider error never become completed', async () => {
  const original = globalThis.fetch;
  try {
    for (const [payload, expected] of [
      [encode('token', { text: 'Partial' }), /gián đoạn/],
      [encode('error', { code: 'provider_unavailable', message: 'AI unavailable' }), /AI unavailable/],
    ] as const) {
      globalThis.fetch = async () => new Response(payload, { headers: { 'Content-Type': 'text/event-stream' } });
      await assert.rejects(async () => { for await (const _event of streamChat('id', body)) { /* Consume. */ } }, expected);
    }
  } finally { globalThis.fetch = original; }
});

test('abort signal is forwarded and no retry occurs', async () => {
  const original = globalThis.fetch;
  const controller = new AbortController(); controller.abort();
  let calls = 0;
  globalThis.fetch = async (_url, init) => {
    calls += 1; assert.equal(init?.signal, controller.signal);
    throw new DOMException('Stopped', 'AbortError');
  };
  try {
    await assert.rejects(async () => { for await (const _event of streamChat('id', body, controller.signal)) { /* Consume. */ } }, { name: 'AbortError' });
    assert.equal(calls, 1);
  } finally { globalThis.fetch = original; }
});
