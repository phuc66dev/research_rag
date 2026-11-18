import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseSse } from './events.ts';

function source(text: string, chunkSize = 1): ReadableStream<Uint8Array> {
  const bytes = new TextEncoder().encode(text);
  return new ReadableStream({
    start(controller) {
      for (let i = 0; i < bytes.length; i += chunkSize) controller.enqueue(bytes.slice(i, i + chunkSize));
      controller.close();
    },
  });
}

test('preserves Vietnamese text across byte and CRLF boundaries', async () => {
  const wire = ': heartbeat\r\nevent: token\r\ndata: {"text":"Tiếng Việt có dấu"}\r\n\r\n';
  const received = [];
  for await (const event of parseSse(source(wire))) received.push(event);
  assert.deepEqual(received, [{event:'token', data:{text:'Tiếng Việt có dấu'}}]);
});

test('joins multiline data without losing event boundaries', async () => {
  const wire = 'event: token\ndata: {"text":\ndata: "Xin chào"}\n\nevent: done\ndata: {"message_id":"m1","provider":"mock"}\n\n';
  const received = [];
  for await (const event of parseSse(source(wire, 7))) received.push(event);
  assert.equal(received.length, 2);
  assert.equal(received[0].event, 'token');
  assert.equal(received[1].event, 'done');
});

test('reports invalid JSON instead of showing corrupted model output', async () => {
  await assert.rejects(async () => {
    for await (const event of parseSse(source('event: token\ndata: {broken}\n\n'))) void event;
  });
});

test('reports a connection ending inside an unfinished event', async () => {
  await assert.rejects(async () => {
    for await (const event of parseSse(source('event: token\ndata: {"text":"Chưa đủ"}'))) void event;
  });
});

test('rejects completion and other known events with missing required fields', async () => {
  for (const [event, data] of [
    ['done', {}],
    ['token', { text: 7 }],
    ['status', []],
    ['citations', { citations: [{ page_number: 0 }] }],
    ['error', { code: 'failure' }],
  ]) {
    await assert.rejects(async () => {
      for await (const item of parseSse(source('event: ' + event + '\ndata: ' + JSON.stringify(data) + '\n\n'))) void item;
    });
  }
});
