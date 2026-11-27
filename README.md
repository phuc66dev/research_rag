# EduRAG-VN

Bộ khung làm việc nhóm cho hệ thống hỏi đáp tài liệu tiếng Việt.
Phúc sở hữu Sổ tay/Không gian học tập; Bảo sở hữu Tài liệu/Retrieval; Phú sở hữu Lịch sử/Auth.
Mỗi người làm xuyên suốt frontend–backend; xem docs/MODULE-OWNERSHIP.md.

## Đã có và chưa có

| Phần                                                      | Trạng thái                                                                    |
| --------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Git, cấu trúc module, quy tắc nhóm, template PR, CI       | Đã tạo cục bộ; chưa push lên GitHub                                           |
| FastAPI health, CRUD sổ tay và SQLite persistence         | Có triển khai và test                                                         |
| SSE mock và parser TypeScript                             | Có; chat generation thật vẫn 501, mock không phải AI thật |
| React/Vite                                                | Auth, history và Tài liệu của tôi đã có React/API; workspace UI còn slot cho Phúc |
| PDF upload/extraction/embedding/retrieval                   | Có pipeline thật, model CPU đa ngôn ngữ và vector lưu SQLite; xem docs/BAO-DOCUMENTS.md |
| Auth/history                                              | Có triển khai; workspace/document dùng current user và owner filtering |
| OCR, DOCX/TXT, Qdrant production, LLM                       | Chưa triển khai trong demo rút gọn |

Trang chủ hiện là luồng đăng nhập và app shell React. Prototype HTML vẫn là tài liệu tham chiếu;
không dùng chức năng mô phỏng của prototype như bằng chứng API đã hoạt động.
Kế hoạch, cách chạy và giới hạn phần Bảo: [BAO-DOCUMENTS.md](docs/BAO-DOCUMENTS.md).

## Yêu cầu

- Node.js 24.x và npm.
- Python 3.12 (khuyến nghị; package chấp nhận từ 3.12 đến dưới 3.15).
- Git; Docker Compose chỉ cần cho cách chạy bằng container.
- Chưa cần API key hoặc Qdrant. Xử lý PDF lần đầu cần mạng để tải model embedding công khai.

## Chạy cục bộ trên Windows

Mở terminal thứ nhất tại thư mục dự án:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
backend/.venv/Scripts/python.exe -m pip install --no-deps -e ./backend
Copy-Item backend/.env.example backend/.env
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu đã có `.env`, giữ nguyên cấu hình của bạn, không chạy lại lệnh sao chép.
Database mặc định nằm trong `backend/data/` khi chạy đúng thư mục backend.

Terminal thứ hai:

```powershell
cd frontend
npm ci
npm run dev
```

- Frontend: http://127.0.0.1:5173
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/v1/health
- OpenAPI runtime: http://127.0.0.1:8000/openapi.json

Vite chuyển `/api` đến backend qua proxy. API client dùng `/api/v1`.
Chỉ các biến công khai được đặt tiền tố `VITE_`; không đặt khóa LLM trong frontend.

## macOS / Linux

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock.txt
backend/.venv/bin/python -m pip install --no-deps -e ./backend
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend dùng cùng lệnh npm. Trong các lệnh kiểm tra bên dưới, thay
`backend/.venv/Scripts/python.exe` bằng `backend/.venv/bin/python`.

## Chạy thử API thật

PowerShell ở terminal khác:

```powershell
# Thay placeholder bằng token trả từ POST /api/v1/auth/login; không lưu token vào source.
$authHeaders = @{ Authorization = 'Bearer <token-từ-API-đăng-nhập>' }
$workspace = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/workspaces -Method Post -Headers $authHeaders -ContentType application/json -Body '{"name":"Kinh tế vĩ mô"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/workspaces -Headers $authHeaders
```

Các lệnh workspace trên dùng Authorization Bearer từ API đăng nhập; có thể thay bằng WebSession
có cookie đăng nhập. Có thể dùng Swagger để đăng ký/đăng nhập/tạo workspace. Owner lấy từ phiên máy chủ;
không gửi user_id. Sổ tay API lưu SQLite; dữ liệu localStorage trong prototype vẫn tách biệt.

Luồng SSE mock, chạy từ thư mục backend:

```powershell
.venv/Scripts/python.exe scripts/demo_mock.py
```

Dùng ID tổng hợp trong demo mock. Endpoint mock không kiểm tra quyền sở hữu hoặc truy xuất nguồn;
`provider=mock` và `mock=true` ghi rõ đây là dữ liệu minh họa.
Đặt `ENABLE_MOCK_CHAT=false` trong backend/.env rồi khởi động lại backend để tắt mock khi chạy Python.
Với Docker Compose, đặt biến này trong .env ở **thư mục gốc** (xem .env.example) hoặc biến môi trường shell, rồi chạy lại docker compose up -d backend. Compose không đọc backend/.env.

## Kiểm tra trước Pull Request

Tại thư mục gốc:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m ruff check backend
backend/.venv/Scripts/python.exe -m ruff format --check backend
npm --prefix frontend test
npm --prefix frontend run build
```

Sau khi đổi API/schema:

```powershell
backend/.venv/Scripts/python.exe backend/scripts/export_openapi.py
```

Commit snapshot `contracts/openapi.json` cùng thay đổi API. CI xuất lại và báo lỗi khi snapshot lệch.
Không chỉnh thủ công snapshot để che thay đổi API.

## Docker Compose (tùy chọn)

```bash
docker compose up --build
# Qdrant tùy chọn cho bước mở rộng retrieval của Bảo:
docker compose --profile rag up --build
```

Container bind cổng ra loopback của máy host; data dùng named volume.
Qdrant là dịch vụ tùy chọn, hiện chưa nối vào API. Cấu hình container cần được kiểm tra trên máy có Docker.
Để dừng: `docker compose down` (giữ data volume). Không thêm `-v` nếu muốn giữ dữ liệu.

## Cấu trúc và phần việc

- Phân công hiện hành: [MODULE-OWNERSHIP.md](docs/MODULE-OWNERSHIP.md).
- Phúc: workspace và study/chat, gồm UI, API, model/service và test.
- Bảo: document/upload/extraction/index/retrieval, gồm UI, API, dữ liệu và test.
- Phú: history/auth/authorization nền tảng/app shell, gồm UI, API, dữ liệu và test.
- contracts/ là hợp đồng chung; đổi phải được cả bên cung cấp và bên sử dụng review.
- edurag-p0.html là prototype gốc; owner từng module chuyển sang React khi thực hiện task.
- Theo dõi trạng thái module hiện tại qua code/test và hướng dẫn riêng; BOOTSTRAP-STATUS là ghi nhận lịch sử.
- Cách phối hợp: [TEAM-WORKFLOW.md](docs/TEAM-WORKFLOW.md); trạng thái bootstrap: [BOOTSTRAP-STATUS.md](docs/BOOTSTRAP-STATUS.md).

## Phát hành và dữ liệu

Giữ dịch vụ trên localhost. Auth/history và document đã có code, nhưng chưa nghiệm thu pilot
công khai; chat generation/UI học tập chưa hoàn tất. Xóa workspace điều phối dọn tài liệu,
vector và history. Migration giữ workspace cũ chưa có owner ở trạng thái không truy cập được,
không tự gán dữ liệu cũ cho user mới. Không xem localStorage của prototype là lưu trữ sản phẩm.
Không commit `.env`, file người dùng, database, API key hoặc thư mục môi trường ảo.
