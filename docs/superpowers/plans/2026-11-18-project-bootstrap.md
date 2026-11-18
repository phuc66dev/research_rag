# EduRAG-VN Bootstrap Implementation Plan

> TÀI LIỆU LỊCH SỬ: bootstrap đã được thực hiện. Phân công theo tầng trong bản này đã hủy từ 18/11/2026; công việc tiếp theo dùng docs/MODULE-OWNERSHIP.md. Không dùng bản này để giao nhiệm vụ mới.

**Goal:** Khởi tạo monorepo chạy cục bộ để Phúc, Bảo, Phú làm việc song song.
**Architecture:** FastAPI + SQLite lưu workspace; module RAG tách riêng với SSE mock được đánh dấu. Vite/React mở nguyên prototype hiện có và cung cấp API client typed cho bước chuyển sang React.
**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, pytest; Node 24, React, TypeScript, Vite.
**Spec:** docs/PRD-v1.md; phạm vi lần này là bootstrap, không triển khai toàn bộ P0.

## Constraints and rulings

- Phúc: RAG/AI; Bảo: backend/data; Phú: frontend.
- Không có base commit nên khởi tạo trực tiếp repository mới tại workspace đã được chỉ định; không cần worktree cho lần tạo nền tảng này.
- Giữ nguyên tài liệu/prototype; không dựng lại UI trong bootstrap. Better Design MCP không có trong danh sách công cụ phiên này; không tuyên bố đã review UI qua MCP.
- Không gọi AI thật hoặc cần API key để chạy smoke tests.
- Chỉ bind dịch vụ ra localhost; chưa có xác thực, không dùng bản này để triển khai công khai.
- Không tạo GitHub repository/remote hoặc push khi chưa có đích và yêu cầu của người dùng.

## Review focus

- Workspace tồn tại sau khi tạo lại ứng dụng bằng cùng database.
- Tên toàn khoảng trắng bị từ chối; UUID không tồn tại trả 404.
- SSE phát citation trước token; dữ liệu nguồn tuân hợp đồng.
- Mock có thể tắt và không bị nhầm là RAG thật.
- Frontend build có prototype và font nhúng, không phụ thuộc đường dẫn tuyệt đối trên máy tác giả.

## Tasks

- [x] 1. Tạo cấu hình, viết và chạy test đỏ cho health, workspace CRUD/persistence, SSE mock.
- [x] 2. Cài backend tối thiểu để các test xanh; endpoint chưa làm trả 501 rõ ràng.
- [x] 3. Dựng frontend React/TypeScript, API client, proxy và gói prototype vào build.
- [x] 4. Bàn giao contracts, AGENTS, hướng dẫn nhóm, CI và Docker Compose.
- [x] 5. Chạy pytest, lint, typecheck/build và smoke test tích hợp. Review bộ khung trước bàn giao.

## Evidence

Sẽ ghi kết quả sau khi chạy kiểm tra; không coi việc có file là chức năng đã chạy.


## Final evidence — 18/11/2026

- Backend RED: 10 failures / 2 passes against the initial empty factory; implemented API then 12/12 passed.
- Frontend RED: 4/4 SSE parser tests failed before parser implementation; then 4/4 passed.
- Independent review: six actionable P2 findings. Reproduced timestamp, memory SQLite,
  unavailable collections, OpenAPI declarations and SSE schema failures before fixing.
- Final fixes: UTC serialization; StaticPool for memory SQLite; explicit 501 collections/stubs;
  SSE OpenAPI media type; configurable Compose mock; required SSE payload fields.
- Final suite: backend 18/18; frontend 5/5; ruff check and formatter; TypeScript/build pass.
- Browser smoke: approved prototype renders, embedded Roboto loads, typed client CRUD works through
  Vite proxy, mock SSE produces status/citations/token/token/done, no browser page errors.
- Docker Compose config validated and ENABLE_MOCK_CHAT=false override verified. Runtime unavailable
  because Docker Desktop engine was not running; do not claim containers started.
- Hosted GitHub CI not executed: repo has no remote/commit/push. This is an environment limit,
  not evidence of passing hosted CI.
- Known dependency limit: one upstream picomatch advisory impacts five frontend dev dependency
  entries, latest package still affected at check time. No unsafe force/downgrade applied.
- No files were deleted or committed; original prototype and requirements retained.
