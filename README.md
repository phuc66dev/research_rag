# EduRAG-VN

Bộ khung làm việc nhóm cho hệ thống hỏi đáp tài liệu tiếng Việt.
Phúc sở hữu Sổ tay/Không gian học tập; Bảo sở hữu Tài liệu/Retrieval; Phú sở hữu Lịch sử/Auth.
Mỗi người làm xuyên suốt frontend–backend; xem docs/MODULE-OWNERSHIP.md.

## Đã có và chưa có

| Phần                                                      | Trạng thái                                                                    |
| --------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Git, cấu trúc module, quy tắc nhóm, template PR, CI       | Đã tạo cục bộ; chưa push lên GitHub                                           |
| FastAPI health, CRUD sổ tay và SQLite persistence         | Có triển khai và test                                                         |
| SSE mock và parser TypeScript                             | Có triển khai và test; không phải AI thật                                     |
| React/Vite                                                | Chạy nguyên prototype đã chốt trong iframe; chưa viết lại màn hình bằng React |
| API client typed                                          | Có, chưa nối vào prototype; dữ liệu prototype vẫn riêng trong localStorage    |
| Upload/OCR, Qdrant retrieval, LLM, chat persistence, auth | Chưa triển khai; endpoint ghi rõ 501 khi phù hợp                              |

Prototype mở ở trang chủ; chọn màn hình và trạng thái ở thanh trên cùng.
Không dùng các chức năng mô phỏng trong prototype như bằng chứng API đã hoạt động.

## Yêu cầu

- Node.js 24.x và npm.
- Python 3.12 (khuyến nghị; package chấp nhận từ 3.12 đến dưới 3.15).
- Git; Docker Compose chỉ cần cho cách chạy bằng container.
- Chưa cần API key hoặc Qdrant để chạy bootstrap.

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
$workspace = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/workspaces -Method Post -ContentType application/json -Body '{"name":"Kinh tế vĩ mô"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/workspaces
```

Sổ tay API lưu trên SQLite; danh sách trong prototype không tự đồng bộ với API ở giai đoạn này.

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
# Chỉ khi Phúc bắt đầu tích hợp Qdrant:
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
- Cấu trúc module mới là kế hoạch, chưa tự thay đổi code hoặc thêm auth/RAG thật.
- Cách phối hợp: [TEAM-WORKFLOW.md](docs/TEAM-WORKFLOW.md); trạng thái bootstrap: [BOOTSTRAP-STATUS.md](docs/BOOTSTRAP-STATUS.md).

## Phát hành và dữ liệu

Bootstrap **chưa có xác thực**, chỉ dành cho phát triển một người dùng trên localhost.
Chưa có luồng xóa file/vector/chat thật; workspace hiện chưa có các dữ liệu liên quan đó.
Không mở dịch vụ ra Internet hoặc xem dữ liệu localStorage của prototype là lưu trữ sản phẩm.
Không commit `.env`, file người dùng, database, API key hoặc thư mục môi trường ảo.
