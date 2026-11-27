# Hợp đồng RAG và API — phiên bản 0.1

Chủ hợp đồng generation/chat: **Phúc** (cả UI và API). **Bảo** sở hữu extraction/index/retrieval; **Phú** sở hữu auth và persistence/history. Các consumer cùng review khi thay hợp đồng.
Thay đổi payload phải cập nhật Python schema, TypeScript types, test và OpenAPI trong cùng PR.

## Trạng thái hiện hành — cập nhật 26/11/2026

- Health và CRUD workspace chạy thật trên SQLite; workspace hiện có owner filtering qua auth.
- Document upload/list/status/file/retry/delete và source search đã triển khai; xem
  [hợp đồng retrieval](retrieval.md) cho payload/quyền/giới hạn. File chỉ mở khi nguồn ready.
- Auth và session/message/history có code. Chat generation thật vẫn trả **501**.
- `POST /api/v1/chat/mock/stream` là fixture để Phú làm UI. Không truy cập Qdrant, LLM,
  không xác thực workspace/document tồn tại và không lưu hội thoại.
- Mock không chứng minh chất lượng RAG hoặc phân quyền; dùng UUID tổng hợp, không dùng như API sản phẩm.
- Tắt mock bằng `ENABLE_MOCK_CHAT=false`. Không tự động fallback từ chat thật sang mock.

## Dữ liệu nguồn Bảo quản lý

```json
{
  "workspace_id": "UUID",
  "document_id": "UUID",
  "document_version": "SHA-256 hoặc phiên bản ổn định",
  "chunks": [{
    "id": "ID đoạn ổn định",
    "text": "Văn bản đã chuẩn hóa",
    "section_title": "Chương 3",
    "page_number": 42,
    "bbox": null
  }]
}
```

Bảo dùng metadata dưới đây cho extraction/index/retrieval; Phúc nhận các đoạn tìm được để sinh câu trả lời, không lập chỉ mục riêng. Chữ ký đã triển khai nằm trong [retrieval.md](retrieval.md), cần consumer review trước merge.

Trang bắt đầu từ 1, là chỉ số trang trong file PDF, không phải số trang in.
Upload PDF có text đã có pipeline thật; cấu trúc minh họa này mô tả dữ liệu nội bộ,
không phải response upload. Không có bbox thì dùng null. Trước khi gửi bbox thật, thống nhất hệ
tọa độ và phép biến đổi với Phú; không tự trộn điểm PDF với pixel màn hình.
DOCX/TXT chưa có nguồn trang: giữ ngoài demo rút gọn, không tạo số trang giả.

## Yêu cầu chat

```json
{
  "workspace_id": "11111111-1111-4111-8111-111111111111",
  "document_ids": ["22222222-2222-4222-8222-222222222222"],
  "query": "Tổng cầu gồm những thành phần nào?",
  "mode": "strict"
}
```

Query trim khoảng trắng, dài 1–4000 ký tự; 1–100 document IDs hợp lệ dạng UUID.
Tập nguồn được chốt theo từng request. Với API thật, backend phải kiểm tra quyền và
`ready` của mọi nguồn, không chỉ kiểm tra định dạng ID.

## SSE

Gửi bằng fetch POST; không dùng EventSource GET. UTF-8, Content-Type text/event-stream.
Mỗi sự kiện kết thúc bằng một dòng trống; data là JSON. Client có thể nhận nửa ký tự
hoặc nhiều sự kiện trong cùng một network chunk.

```text
event: status
data: {"stage":"retrieving","mock":true}

event: citations
data: {"citations":[{"id":"c1","document_id":"22222222-2222-4222-8222-222222222222","document_version":"mock-v1","document_title":"Tai_lieu_minh_hoa.pdf","page_number":42,"snippet":"Đoạn minh họa","bbox":null}],"mock":true}

event: token
data: {"text":"Nội dung minh họa [1]."}

event: done
data: {"message_id":"UUID","provider":"mock","mock":true}

```

- Citation trước token. Chỉ mục [1] tương ứng phần tử thứ nhất trong citations.
- Error tương lai: `event: error`, `data: {"code":"provider_unavailable","message":"..."}`.
  SSE lỗi sau khi bắt đầu trả HTTP 200 phải dùng sự kiện error; không thể đổi lại HTTP status.
- Không có căn cứ: citations rỗng, trả lời nêu thiếu thông tin, rồi done. Chưa cài RAG thật.
- Khi kết nối ngắt trước done, UI giữ nội dung đã nhận và đánh dấu gián đoạn.
- Transport client: `frontend/src/api/chat.ts`; parser có test cho CRLF, UTF-8 và mất kết nối.

## REST và lỗi

Nguồn máy đọc: [openapi.json](openapi.json), xuất từ ứng dụng bằng script export_openapi.py.
Danh sách workspace trả mảng, không bọc trong data. Tạo trả 201, xóa trả 204 không có body.
Workspace chưa tồn tại trả 404; dữ liệu không hợp lệ trả 422 chuẩn FastAPI.
Lỗi nghiệp vụ: `{"detail":{"code":"workspace_not_found","message":"..."}}`.
Client phải xử lý cả detail dạng chuỗi, object và danh sách lỗi validation.
