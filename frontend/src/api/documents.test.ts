import assert from 'node:assert/strict';
import test from 'node:test';
import { documentError, readySelection, statusLabels } from '../features/documents/presentation.ts';
import type { DocumentItem } from '../features/documents/types.ts';

test('source snapshots exclude processing, failed and deleted documents', () => {
  const items = [
    { id: 'ready', status: 'ready' }, { id: 'pending', status: 'processing' },
    { id: 'failed', status: 'failed' }, { id: 'gone', status: 'deleting' },
  ] as DocumentItem[];
  assert.deepEqual(readySelection(items, ['ready', 'pending', 'failed', 'gone', 'deleted']), ['ready']);
});

test('errors expose useful retry/duplicate/session messages without serializing payloads', () => {
  assert.match(documentError({ detail: { code: 'duplicate_document', message: 'technical' } }), /đã có/);
  assert.match(documentError({ detail: { code: 'unauthorized' } }), /đăng nhập lại/);
  assert.match(documentError('ocr_required'), /chưa hỗ trợ OCR/);
  assert.equal(documentError({ detail: { message: 'Môn không tồn tại' } }), 'Môn không tồn tại');
  assert.match(documentError({ unexpected: true }), /thử lại/);
  assert.equal(statusLabels.ready, 'Sẵn sàng');
});
