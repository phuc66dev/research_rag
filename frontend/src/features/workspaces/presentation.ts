import type { Workspace } from '../../api/types.ts';

export type WorkspaceSort = 'updated' | 'name';

function searchable(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd')
    .toLocaleLowerCase('vi').trim();
}

export function visibleWorkspaces(items: Workspace[], query: string, sort: WorkspaceSort): Workspace[] {
  const needle = searchable(query);
  return items.filter(item => searchable(`${item.name} ${item.description}`).includes(needle))
    .sort((a, b) => sort === 'name'
      ? a.name.localeCompare(b.name, 'vi') || a.id.localeCompare(b.id)
      : Date.parse(b.updated_at) - Date.parse(a.updated_at) || a.id.localeCompare(b.id));
}

export function workspaceNameError(name: string): string {
  if (!name.trim()) return 'Nhập tên môn học trước khi lưu.';
  if (name.trim().length > 100) return 'Tên môn học tối đa 100 ký tự.';
  return '';
}

export function workspaceError(error: unknown): string {
  if (error && typeof error === 'object') {
    const failure = error as { status?: number; detail?: unknown };
    if (failure.status === 401) {
      return 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại ở tab khác rồi thử lại; nội dung đang nhập vẫn được giữ.';
    }
    if (failure.status === 403) return 'Bạn không có quyền truy cập sổ tay này. Hãy tải lại danh sách.';
    if (failure.status === 404) return 'Sổ tay không còn tồn tại. Hãy tải lại danh sách.';
    if (failure.status === 422) return 'Dữ liệu chưa hợp lệ. Kiểm tra tên và mô tả môn học rồi thử lại.';
    if (failure.detail && typeof failure.detail === 'object' && !Array.isArray(failure.detail)) {
      const detail = failure.detail as { message?: unknown };
      if (typeof detail.message === 'string') return detail.message;
    }
  }
  return 'Không kết nối được dịch vụ. Hãy thử lại; nội dung đang nhập vẫn được giữ.';
}
