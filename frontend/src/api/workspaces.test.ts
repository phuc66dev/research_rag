import assert from 'node:assert/strict';
import test from 'node:test';
import type { Workspace } from './types.ts';
import { visibleWorkspaces, workspaceError, workspaceNameError } from '../features/workspaces/presentation.ts';

const courses: Workspace[] = [
  { id: 'a', name: 'Cơ sở dữ liệu', description: 'Chuẩn hóa và đại số quan hệ',
    updated_at: '2026-11-26T10:00:00Z', document_count: 3, created_at: '2026-11-26T10:00:00Z' },
  { id: 'b', name: 'Đại số tuyến tính', description: 'Ma trận và không gian vector',
    updated_at: '2026-11-26T10:00:00.900Z', document_count: 0, created_at: '2026-11-26T10:00:00Z' },
];

test('search finds Vietnamese names and descriptions with or without accents', () => {
  assert.deepEqual(visibleWorkspaces(courses, 'CO SO DU LIEU', 'updated').map(item => item.id), ['a']);
  assert.deepEqual(visibleWorkspaces(courses, 'dai so tuyen', 'updated').map(item => item.id), ['b']);
  assert.equal(visibleWorkspaces(courses, 'chuan hoa', 'updated')[0].document_count, 3);
  assert.deepEqual(visibleWorkspaces(courses, 'không có môn này', 'updated'), []);
});

test('sort handles subsecond timestamps without changing the server result array', () => {
  assert.deepEqual(visibleWorkspaces(courses, '', 'updated').map(item => item.id), ['b', 'a']);
  assert.deepEqual(visibleWorkspaces(courses, '', 'name').map(item => item.id), ['a', 'b']);
  assert.deepEqual(courses.map(item => item.id), ['a', 'b']);
});

test('name validation rejects whitespace and oversized names while accepting Vietnamese input', () => {
  assert.ok(workspaceNameError('   '));
  assert.ok(workspaceNameError('a'.repeat(101)));
  assert.equal(workspaceNameError('  Cơ sở dữ liệu  '), '');
});

test('request failures guide recovery without exposing raw transport or validation details', () => {
  assert.match(workspaceError({ status: 401 }), /tab khác/);
  assert.match(workspaceError({ status: 403 }), /không có quyền/);
  assert.match(workspaceError({ status: 404 }), /không còn tồn tại/);
  assert.match(workspaceError({ status: 422, detail: [{ input: 'private' }] }), /chưa hợp lệ/);
  assert.equal(workspaceError({ detail: { message: 'Sổ tay đang được xóa.' } }), 'Sổ tay đang được xóa.');
  assert.match(workspaceError(new TypeError('raw network stack')), /nội dung đang nhập vẫn được giữ/);
});
