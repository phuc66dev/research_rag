# Tài liệu/Retrieval — vận hành và bàn giao

Phạm vi Bảo theo MODULE-OWNERSHIP.md; kế hoạch trước code: BAO-IMPLEMENTATION.md.
Hợp đồng chi tiết: [retrieval.md](../contracts/retrieval.md).

## Cài đặt và chạy

Từ repository root, dùng Python 3.12/Node 24:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
backend/.venv/Scripts/python.exe -m pip install --no-deps -e ./backend
npm --prefix frontend ci
```

Không ghi đè .env. Biến mới có trong backend/.env.example. Chạy backend từ thư mục backend
như README, frontend bằng npm run dev. Storage/model cache mặc định nằm trong backend/data.
Đăng ký/đăng nhập qua UI; cần có workspace của tài khoản hiện tại. UI workspace của Phúc
chưa có trong nhánh này; có thể tạo bằng Swagger POST /api/v1/workspaces sau khi đăng nhập
qua cùng backend origin hoặc dùng Bearer token của auth. Trang Tài liệu của tôi tải danh sách
môn thật và có nút Tải lại sau khi tạo môn.

Chọn môn → chọn/kéo thả một PDF có text → Tải tài liệu → chờ worker → Sẵn sàng. Mở PDF dùng
API có auth. Tệp trùng/lỗi giữ lựa chọn để người dùng sửa; không tự gửi lại. Failed có Thử lại;
Xóa có dialog xác nhận và dọn nguồn thật. Lần đầu model tải từ Hugging Face, không phải gọi
dịch vụ embedding; không gửi nội dung tài liệu cho nhà cung cấp. Không cần API key.

## Dữ liệu và migration

Một Base ở core/database.py; workspace.py re-export import cũ để consumer không phải đổi hết.
Startup chạy core/migrations.py, ghi schema_revisions:

1. 0001_bootstrap: tạo bảng nền còn thiếu, giữ dữ liệu cũ.
2. 0002_workspace_owner: thêm owner_id nullable và is_deleting nếu thiếu.
3. 0003_documents: thêm documents/document_jobs/document_chunks.

Đây là migration additive cho mô hình bootstrap SQLite hiện có; không drop/rebuild bảng,
không xóa database. Workspace cũ owner=null không được tự gán hoặc hiển thị cho tài khoản
mới. Người điều phối cần quyết định gán owner cho dữ liệu cũ trong nhiệm vụ riêng.
SQLite bật foreign_keys và busy_timeout. Không tuyên bố đã kiểm thử PostgreSQL/multi-worker.
Sao lưu database và thư mục storage cùng nhau; model cache có thể tải lại.

Worker tắt được bằng DOCUMENT_WORKER_ENABLED=false để kiểm thử hoặc bảo trì. Khi bật, queued
được xử lý sau restart; job processing bị crash cần hết timeout+30 giây trước khi thành failed.
Giới hạn PDF không bảo đảm mức RAM tuyệt đối cho mọi PDF độc hại; subprocess có deadline,
giới hạn trang/chunk/content stream; chưa có sandbox CPU/RAM cấp OS cho pilot công khai.

## Kiểm tra

```powershell
# Nếu Windows chặn thư mục pytest mặc định, dùng thư mục tạm riêng:
$env:PYTEST_DEBUG_TEMPROOT='D:/research_rag/backend/data/test-tmp'
New-Item -ItemType Directory -Force $env:PYTEST_DEBUG_TEMPROOT | Out-Null
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m ruff check backend
backend/.venv/Scripts/python.exe -m ruff format --check backend
npm --prefix frontend test
npm --prefix frontend run build
backend/.venv/Scripts/python.exe backend/scripts/export_openapi.py

# Kiểm thử opt-in PDF + model thật, cần tải model, không tốn phí API:
$env:EDURAG_RUN_MODEL_TEST='1'
backend/.venv/Scripts/python.exe -m pytest backend/tests/documents/test_real_model.py -q
Remove-Item Env:EDURAG_RUN_MODEL_TEST
```

Test mặc định dùng FixtureEmbedding có nhãn, chỉ inject trong fixture; test model thật tách
riêng. Không dùng fixture trong API thật. Kết quả kiểm tra cuối được ghi trong báo cáo bàn giao.

## Giới hạn và consumer cần tiếp nối

- PDF có text; scan/trang thiếu text báo ocr_required, không coi index một phần là ready.
- Chưa OCR, DOCX/TXT, Drive, Qdrant production hoặc đánh giá tập chuẩn PRD.
- Phúc cần dùng search_sources/DocumentSources cho chat và popup citation. Chat thật vẫn 501;
  chưa có luồng hỏi → trả lời LLM → lưu câu trả lời hoàn chỉnh.
- Phú review auth/history consumer và hai thay đổi tích hợp nhỏ ở API client/app shell.
  Helper vô hiệu citation được làm idempotent để retry cleanup không nhân đôi nhãn nguồn đã xóa.
- Style hiện có của app shell khác Roboto/trắng–xanh tím đã chốt trong AGENTS. Chỉ module tài
  liệu dùng thiết kế đã chốt; không tự sửa toàn bộ theme của Phú.
- Better Design MCP chưa được kết nối. Review DOM/viewport dùng browser có sẵn; không gọi đó
  là review Better Design.
- Chưa commit/push/PR/merge; reviewer chính của Bảo là Phú, thêm Phúc cho hợp đồng nguồn.

## Biên bản bàn giao — 26/11/2026

Thành viên / nhiệm vụ: Bảo — Tài liệu của tôi và retrieval xuyên suốt theo phạm vi demo PDF có text.

Đã làm: UI React/API thật; kiểm tra PDF/dung lượng/hash/quota; lưu file/metadata/job; extraction
NFC và chunk giữ trang/version; embedding CPU và cosine trên vector SQLite; scope/owner checks;
retry, lease chống kết quả job cũ, cleanup file/vector/history và phục hồi dữ liệu sau restart.
Đã cung cấp component nguồn và service cho Phúc, chưa nối vào chat generation của Phúc.

File thay đổi theo nhóm:

- Backend document: api/documents.py, models/document.py, schemas/document.py,
  repositories/documents.py, services/documents/*, services/retrieval/*.
- Nền/tích hợp: core/database.py, core/migrations.py, core/config.py, main.py,
  workspace model/API/repository; owner checks ở history/session consumer; helper citation
  idempotent trong repositories/sessions.py.
- Frontend: api/documents.ts, features/documents/*, test documents; API client nhận body File,
  AppShell gắn DocumentsView. Không đổi theme chung hoặc prototype.
- Contracts/docs: OpenAPI xuất từ app, rag.md/retrieval.md, README, kế hoạch và hướng dẫn này;
  backend/.env.example, pyproject và lock backend.

Dependency: thêm pypdf cho extraction và FastEmbed/ONNX cho embedding thật. Lock được xuất từ
môi trường ảo sạch dùng baseline pins và hai dependency mới; không có editable path cá nhân.
Không đổi dependency/lock frontend. Migration additive 0001–0003 như mô tả ở trên.

Kiểm tra thực tế cuối:

| Lệnh/kiểm tra | Kết quả |
| --- | --- |
| pytest backend/tests -q (PYTEST_DEBUG_TEMPROOT riêng) | 61 passed, 1 skipped; 77,21 giây |
| EDURAG_RUN_MODEL_TEST=1 pytest backend/tests/documents/test_real_model.py -q | 1 passed; 10,01 giây |
| ruff check backend | Passed |
| ruff format --check backend | 60 files already formatted |
| npm --prefix frontend test | 7 passed |
| npm --prefix frontend run build | Typecheck và Vite production build passed |
| export_openapi.py + so JSON với create_app().openapi() | Khớp |
| pip check | No broken requirements found |
| git diff --check | Không có lỗi whitespace |
| Browser DOM/ảnh 1366×900 và 390×844 | Module không tràn ngang; bảng cuộn bên trong; Roboto |
| Dialog xóa + Escape | Focus vào Hủy, đóng và trả focus về nút mở |
| Browser console trong lượt review | Không có error |

Lần pytest nền đầu bị WinError 5 ở thư mục temp hệ thống; các lần báo passed dùng thư mục
temp riêng trong backend/data. Test model mặc định skipped để CI không tự tải model;
đã chạy riêng với model thật, không coi fixture là chất lượng embedding.

Chưa xác minh: Better Design MCP (không kết nối), GitHub Actions, container runtime,
PostgreSQL/multi-worker, tập chuẩn recall/latency của PRD và luồng generation/chat của Phúc.
Không có thay đổi Compose/CI. Preview review chỉ bind loopback; database/files review tách biệt
trong backend/data/bao-ui-review*, không dùng database mặc định của người dùng.

Consumer tiếp nối: Phúc review retrieval/DocumentSources rồi ghép vào chat và popup nguồn;
Phú review auth/history/app shell/client. Workspace cũ owner=null cần điều phối quyết định gán
chủ trong nhiệm vụ riêng. Cách chạy/cách dùng và giới hạn đã ghi ở các mục trên.

Git: nhánh codex/bao-documents-retrieval tạo từ nhánh bao đang sạch lúc bắt đầu. Chưa stage,
commit, push, mở PR hoặc merge. Không xóa database, file người dùng hay sửa .env hiện có.
