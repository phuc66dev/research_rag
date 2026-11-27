# Kế hoạch triển khai Tài liệu/Retrieval — Bảo

Ngày bắt đầu: 26/11/2026. Nguồn phạm vi: MODULE-OWNERSHIP.md mục 3 và 8.

## Hiện trạng và phạm vi

Auth/current user và history service đã có code. API document còn là stub; workspace chưa có
owner. Frontend có app shell với ô trống cho tài liệu. Không sửa prototype để giả tích hợp.
Phạm vi demo: PDF có text, tối đa 50 MiB; không OCR/DOCX/TXT/Drive/LLM.

## Thứ tự và nghiệm thu

1. Nền dữ liệu: Base chung, migration bổ sung document/chunk/job; không xóa DB cũ.
2. Upload/list/status/file/delete/retry: lấy user từ auth; hash trùng trong cùng workspace;
   giới hạn dung lượng phía server, tên/path do server kiểm soát, dữ liệu bền vững.
3. Worker: hàng đợi trong DB, claim có điều kiện, lease/attempt để thử lại và phục hồi;
   PDF thật → text NFC → chunk theo trang → embedding → index. Lỗi không thành ready.
4. Retrieval: nhận user/workspace/tập document từ server; kiểm tra toàn bộ nguồn ready/owner;
   trả chunk ID, version SHA-256, trang từ 1, bbox=null; không sinh câu trả lời.
5. React: bộ chọn môn/upload/bảng trạng thái/error/retry/delete; component nguồn dùng props;
   gắn vào slot tài liệu bằng thay đổi tích hợp tối thiểu. Giữ thiết kế sản phẩm.
6. Kiểm thử: PDF thật, input lỗi/trùng/limit, persistence/retry/delete/job cũ, hai user,
   scope search, citation invalidation; backend/frontend checks, OpenAPI và DOM nếu có công cụ.

## Điểm giao tiếp

- Phú: dùng get_current_user và history_service.cleanup_citations_for_document có sẵn.
- Phúc: cần workspace.owner_id và kiểm tra quyền workspace. Khi chưa có, document API phải
  từ chối thao tác cần quyền workspace; fixture quyền chỉ dùng trong test.
  Người giao việc đã cho phép bổ sung tối thiểu owner filtering/migration cho workspace trong
  phiên này. Bao gồm các consumer history và luồng xóa tài liệu/lịch sử khi xóa workspace.
- Phú: app shell/API client hiện có được dùng làm điểm gắn, không thay nghiệp vụ auth/history.
- Search/component nguồn bàn giao cho Phúc; generation/chat và popup citation thuộc Phúc.
- Chưa cho phép commit/push/PR/merge, triển khai công khai hoặc gọi API tốn phí.

## File dự kiến

backend/app/{api/documents.py,models/document.py,schemas/document.py,repositories/documents.py},
backend/app/services/{documents/,retrieval/}, core/database.py, main.py, migration/script,
backend/tests/{documents/,retrieval/}, backend dependency/lock,
frontend/src/{api/documents.ts,features/documents/}, điểm gắn app shell/client tối thiểu,
contracts/{retrieval.md,openapi.json}, tài liệu vận hành module.

## Kiểm tra và bàn giao

Chạy pytest backend, Ruff check/format, frontend test/build và export OpenAPI sau thay đổi.
Ghi kết quả thực tế, giới hạn chất lượng retrieval, dependency/migration, cách chạy worker,
phần chưa tích hợp với module khác và nhánh Git vào báo cáo cuối.

## Kết quả phiên triển khai

Đã triển khai các bước 1–6 trong phạm vi demo PDF có text. Quyền workspace tối thiểu được
người giao việc cho phép bổ sung trong phiên. Kết quả kiểm tra, danh sách nhóm file và phần
consumer cần tiếp nối nằm trong [biên bản bàn giao](BAO-DOCUMENTS.md#biên-bản-bàn-giao--26112026).
Không coi chat generation/popup của Phúc, OCR hoặc đánh giá tập chuẩn PRD là đã hoàn tất.
