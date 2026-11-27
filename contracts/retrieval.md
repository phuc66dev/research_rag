# Hợp đồng nguồn và retrieval — Bảo, 26/11/2026

Code đã có; Phúc/Phú cần review consumer trước merge. Chat/SSE giữ nguyên hợp đồng rag.md.

## REST

Mọi endpoint dưới `/api/v1` dùng current user của Phú. Chưa đăng nhập: 401; sai owner: 403;
ID không tồn tại: 404; lỗi validation: 422. Owner luôn lấy từ phiên máy chủ.

| Method/path | Kết quả |
| --- | --- |
| GET /workspaces/{workspace_id}/documents | 200, mảng DocumentRead |
| POST /workspaces/{workspace_id}/documents?filename=... | 202, DocumentRead queued |
| GET /documents/{document_id}/status | 200, DocumentRead |
| GET /documents/{document_id}/file | 200 application/pdf, inline, private/no-store |
| POST /documents/{document_id}/retry | 202 nếu failed, 409 nếu đang chạy/ready |
| DELETE /documents/{document_id} | 204 sau khi dọn file/chunk/vector và vô hiệu citation |
| POST /workspaces/{workspace_id}/sources/search | 200, mảng SourceChunk |

Upload gửi **body nhị phân PDF**, Content-Type: application/pdf, tên tệp qua query filename.
Không phải multipart/FormData hoặc JSON/base64. Payload upload cũ là stub 501 chưa có body;
consumer mới là frontend/src/api/documents.ts. Không đổi payload chat/citation.

Chỉ PDF có text; mặc định 50 MiB, 500 trang, 5.000 chunks, 10 tài liệu/workspace; cấu hình
qua Settings/env. Hash SHA-256 phát hiện trùng bytes trong cùng workspace (409), kể cả đổi tên.
Không mở rộng sang DOCX/TXT/OCR. Sai loại/chữ ký: 415; quá dung lượng: 413. PDF có chữ ký
nhưng sai cấu trúc/mã hóa/scan được nhận queued, sau xử lý trả failed với error_code thật.

DocumentRead gồm id, workspace_id, title, document_version (SHA-256), size_bytes, status,
error_code, page_count, chunk_count, embedding_model, created_at/updated_at (UTC).
Status: queued → processing → ready hoặc failed; deleting trong giai đoạn dọn nguồn.
Không trả path lưu trữ hay owner tùy ý cho frontend. Không có % tiến độ giả.

## Search service cho Phúc

```python
from app.schemas.document import SourceSearch
from app.services.retrieval.service import search_sources

chunks = search_sources(
    db,
    current_user=current_user,  # User đã xác thực từ dependency, không lấy từ JSON
    workspace_id=str(workspace_id),
    request=SourceSearch(document_ids=document_ids, query=query, limit=6),
    embedder=request.app.state.embedder,
)
```

REST body tương ứng:

```json
{"document_ids":["UUID"],"query":"Câu hỏi tiếng Việt","limit":6}
```

Query trim, 1–4.000 ký tự; 1–100 UUID nguồn; limit 1–20. Kiểm tra **toàn bộ** tập nguồn trước
khi embedding/truy xuất. Sai workspace: 403; có nguồn chưa ready: 409; model khác chỉ mục: 409;
model không chạy được: 503. Không bỏ qua nguồn không hợp lệ để trả thành công một phần.

Mỗi SourceChunk: id (chunk ổn định theo document/version/page/offset), document_id,
document_version, document_title, text, page_number từ 1, section_title=null, bbox=null, score
(cosine). Không có số trang hoặc tọa độ suy đoán. Phúc ánh xạ text thành snippet khi tạo
citation; citation ID/order do generation quản lý. Không coi score là xác suất đúng hoặc
bằng chứng rằng mọi câu hỏi có đáp án. Generation phải đánh giá căn cứ và báo thiếu thông tin.

Vector thật dùng FastEmbed CPU, mặc định paraphrase-multilingual-MiniLM-L12-v2 (384 chiều).
Vector/text lưu SQLite, cosine tính trên scope đã xác thực; không cần Qdrant cho demo nhỏ.
Không gọi LLM, không gọi API embedding trả phí, không fallback sang fixture.
Lần đầu cần mạng để tải model công khai; model không tải được khiến job failed.
Chưa đánh giá recall/latency trên tập chuẩn PRD; không tuyên bố chất lượng RAG hoàn chỉnh.

## Worker, retry và xóa

Worker của application lifespan poll document_jobs; pipeline PDF/embedding chạy subprocess
có deadline DOCUMENT_JOB_TIMEOUT. Một tiến trình API khuyến nghị cho demo SQLite. Job lưu
attempt/generation/lease_token; chỉ worker còn lease mới được publish index nguyên tử.
Sau crash, queued còn trong DB; processing quá timeout + 30 giây thành failed để thử lại.
Retry chỉ cho failed; không thêm chunks trùng hoặc giữ vector của lần lỗi trước.

`delete_document_index(db, document_id)` ở repositories/documents.py dọn text/vector, không
tự commit. `delete_workspace_documents(db, workspace_id, current_user, storage)` là helper
cho Phúc. API xóa workspace đánh dấu is_deleting trước, ngăn upload mới rồi gọi helper Bảo
và helper history hiện có; không sao chép kho chat. Luồng upload giữ khóa ghi workspace khi
publish để tránh đua với xóa. Xóa document thu hồi lease trước khi dọn file/citation.

Nếu dọn file/history lỗi, document còn tombstone deleting; không được search/mở file.
Worker tiếp tục cleanup, hoặc người dùng thử Xóa lại. Nếu xóa workspace bị gián đoạn, owner
có thể gửi lại DELETE; môn đang xóa không nhận thêm tài liệu.

## Component cho Phúc

`frontend/src/features/documents/DocumentSources.tsx`: documents, selectedIds, onChange,
loading, error, onRetry. Đây là component controlled; parent dùng documentsApi.list, chụp
tập nguồn ready tại mỗi request (helper readySelection), và xử lý nguồn thay đổi khi poll.
Chỉ ready có checkbox hoạt động; không có upload thứ hai trong workspace.
File URL dùng documentsApi.fileUrl; popup citation do Phúc thực hiện.

## Tài liệu thư viện đã kiểm tra

- [pypdf PdfReader](https://pypdf.readthedocs.io/en/latest/modules/PdfReader.html).
- [FastEmbed và registry model](https://qdrant.tech/documentation/embeddings/fastembed/).
