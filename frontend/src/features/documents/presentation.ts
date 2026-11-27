import type { DocumentItem } from './types.ts';

export const statusLabels: Record<DocumentItem['status'], string> = {
  queued: 'Chờ xử lý', processing: 'Đang đọc và lập chỉ mục', ready: 'Sẵn sàng',
  failed: 'Xử lý thất bại', deleting: 'Đang xóa — có thể thử xóa lại',
};

const errors: Record<string, string> = {
  source_access_revoked: 'Không còn quyền xử lý nguồn này. Hãy kiểm tra lại sổ tay và tài khoản.',
  document_limit: 'Sổ tay đã đạt giới hạn số tài liệu. Hãy xóa nguồn không cần dùng hoặc chọn môn khác.',
  duplicate_document: 'Tệp này đã có trong sổ tay. Bạn có thể dùng tài liệu hiện có.',
  file_too_large: 'Tệp vượt quá 50 MiB. Hãy chọn tệp nhỏ hơn.',
  unsupported_type: 'Bản demo chỉ hỗ trợ PDF có văn bản.',
  invalid_pdf: 'Không đọc được cấu trúc PDF. Hãy kiểm tra hoặc xuất lại tệp.',
  encrypted_pdf: 'PDF được mã hóa. Hãy tải bản không có mật khẩu.',
  ocr_required: 'PDF có trang không đọc được văn bản. Bản demo chưa hỗ trợ OCR.',
  no_text: 'PDF không có văn bản có thể trích xuất.',
  page_limit: 'PDF vượt quá giới hạn số trang hoặc không có trang.',
  page_content_limit: 'Trang PDF quá lớn để xử lý trong bản demo.',
  chunk_limit: 'Nội dung PDF vượt quá giới hạn xử lý của bản demo.',
  embedding_unavailable: 'Chưa tải hoặc chạy được model tìm kiếm. Kiểm tra mạng/model rồi thử lại.',
  processing_timeout: 'Xử lý quá thời gian cho phép. Bạn có thể thử lại.',
  processing_interrupted: 'Xử lý bị gián đoạn khi dịch vụ dừng. Bạn có thể thử lại.',
  processing_failed: 'Không xử lý được tài liệu. Bạn có thể thử lại hoặc chọn bản PDF khác.',
  unauthorized: 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại; tệp bạn chọn vẫn được giữ.',
};

export function documentError(error: unknown): string {
  if (typeof error === 'string') return errors[error] || error;
  if (error && typeof error === 'object') {
    if ('detail' in error) return documentError(error.detail);
    if ('code' in error && typeof error.code === 'string' && errors[error.code]) {
      return errors[error.code];
    }
    if ('message' in error && typeof error.message === 'string') return error.message;
  }
  return 'Không kết nối được dịch vụ. Hãy thử lại; dữ liệu đã chọn vẫn được giữ.';
}

export function readySelection(items: DocumentItem[], selectedIds: string[]): string[] {
  const ready = new Set(items.filter(item => item.status === 'ready').map(item => item.id));
  return selectedIds.filter(id => ready.has(id));
}
