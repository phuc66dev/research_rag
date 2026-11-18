# Làm việc nhóm — EduRAG-VN

> Phân công theo module có hiệu lực từ 18/11/2026. Các phân công theo tầng kỹ thuật trước đây đã hủy.
> Bản chi tiết và điểm cân bằng: [MODULE-OWNERSHIP.md](MODULE-OWNERSHIP.md).

## Chủ module

| Thành viên | Phần xuyên suốt frontend–backend | Người review chính |
| --- | --- | --- |
| Phúc | Sổ tay môn học, Không gian học tập/chat, LLM/SSE/citation | Bảo |
| Bảo | Tài liệu của tôi, upload/extraction/chunking, embedding/index/retrieval | Phú |
| Phú | Lịch sử AI, Authentication/Authorization nền tảng, app shell/tài khoản | Phúc |

Mỗi người có 30 điểm công việc đề xuất, gồm triển khai, kiểm thử, tích hợp và tài liệu.
Điểm không tương đương số giờ; theo dõi khối lượng thực để điều chỉnh task độc lập.
Phú cung cấp current user/permission primitives; mỗi chủ module phải bảo vệ resource của mình.

## Baseline trước khi code

1. Review bộ khung, tạo GitHub repository rỗng và mời thành viên.
2. Kiểm tra không có bí mật, tạo initial commit và push main khi được giao.
3. Mỗi người clone riêng; không dùng Drive để đồng bộ thư mục đang code.
4. Chốt ORM Base, auth context, app shell, interface retrieval và interface lưu hội thoại.
5. Chọn issue nhỏ, ghi owner/file/đầu vào/đầu ra/cách kiểm tra.
6. Bật PR review/status checks nếu repository hỗ trợ; không coi file AGENTS là cơ chế khóa file.

Bootstrap Git cục bộ chưa có remote/commit ở thời điểm tạo. Kiểm tra thực trạng trước thao tác,
không giả định origin/main tồn tại hoặc ghi đè thay đổi đang có.

## Nhánh theo module và nhiệm vụ

Ví dụ: feat/phuc-workspaces, feat/bao-documents-upload, feat/phu-auth,
feat/phu-history. Không giữ một nhánh khổng lồ đến cuối deadline.

Khi working tree sạch và baseline/remote đã có:

```bash
git switch main
git pull --ff-only
git switch -c feat/phuc-workspaces
```

Cập nhật nhánh khi đã lưu thay đổi có chủ ý:

```bash
git fetch origin
git merge origin/main
```

AI chỉ commit/push/PR/merge khi đã được giao. Stage đúng file, đọc diff và xử lý conflict
cùng chủ phần code; không dùng hàng loạt ours/theirs, reset hard hoặc force-push.

## Quy tắc tích hợp

- Hợp đồng module xem MODULE-OWNERSHIP.md; hợp đồng chat hiện tại xem contracts/rag.md.
- Phúc sở hữu UI chat và stream; Phú sở hữu persistence/history; Bảo sở hữu retrieval.
- Một hệ auth, một ORM Base, một app shell và một service lưu chat.
- File App.tsx/routes/style chung do Phú điều phối; main.py/database/backend lock do Bảo điều phối.
- Owner module tự sửa các lớp frontend/backend thuộc domain; không đẩy mọi việc frontend cho Phú.
- API mới phải cập nhật schema, TypeScript, test và OpenAPI được xuất từ code.
- Không tái cấu trúc toàn repository ngay trong nhiệm vụ phân công; tạo đường dẫn mới theo task cụ thể.
- Auth thật chưa có; chỉ test fixture được override identity. Không dùng user cố định cho API thật.

## Prompt chung cho AI

```text
Tôi là <tên>, sở hữu module <tên module> xuyên suốt frontend và backend.
Nhiệm vụ nhỏ hiện tại: <đầu ra>.
Đọc AGENTS.md, docs/MODULE-OWNERSHIP.md và hợp đồng liên quan.
Phạm vi sửa: <file UI/API/schema/model/service/test của module>.
Dùng auth context, database, router/app shell và API client chung.
Không tự viết lại phần của module khác hoặc thay hợp đồng một phía.
Nếu phụ thuộc chưa sẵn sàng, dùng fixture có nhãn để phát triển/test; nêu phần chưa tích hợp.
Bàn giao UI + API + dữ liệu + test quyền sở hữu + hướng dẫn theo phạm vi.
Không tự commit/push/merge hoặc xóa dữ liệu nếu chưa được giao.
```

## Lịch và kiểm tra chung

- 18/11: nền chung/hợp đồng và các lát cắt đầu tiên của từng module.
- 19/11: auth và owner filtering đã ghép; nối PDF thật → retrieval → chat → lịch sử.
- 20/11: kiểm tra hai tài khoản, lỗi dữ liệu/stream, nguồn/xóa và responsive.
- 18:00 dừng thêm tính năng; 22:00 hạn nội bộ; 23:59 ngày 20/11/2026 UTC+7 hạn cuối,
  trừ khi nhóm chốt thời hạn mới.
- Bootstrap chưa có auth/upload/RAG/lưu chat thật. Kế hoạch này không xác nhận chúng đã hoàn tất.
