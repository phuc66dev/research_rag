# Trạng thái bootstrap — 18/11/2026

> Đây là ghi nhận lịch sử kỹ thuật. Phân công hiện hành đã chuyển sang module xuyên suốt; xem MODULE-OWNERSHIP.md. Việc thêm yêu cầu auth vào kế hoạch không có nghĩa code auth đã được triển khai.

## Đã triển khai

- Git main cục bộ, chưa có remote/commit.
- SQLite workspace CRUD và persistence qua application factory.
- Placeholder API trả 501 cho chức năng chưa làm.
- SSE mock tách endpoint, có thể tắt, không gọi LLM.
- React/TypeScript/Vite, API client và parser SSE, prototype đi cùng production build.
- Contracts, OpenAPI snapshot, CI, cấu hình Docker và quy tắc phân chia nhiệm vụ.

## Quyết định triển khai

- Làm trực tiếp trong repo mới chưa có commit, giữ nguyên các tài liệu/prototype gốc.
- Chưa viết lại UI: iframe hiển thị prototype đã được duyệt, trạng thái browser-local riêng.
- Dùng một owner phát triển cục bộ, chưa có account backend hoặc xác thực.
- Không đưa Qdrant/model lớn vào bootstrap bắt buộc; module được tách sẵn để Phúc phát triển.
- Các giả định này cần thay đổi trước khi triển khai công khai hoặc nghiệm thu P0 hoàn chỉnh.

## Môi trường

Node 24; Python 3.12. npm package-lock và backend requirements.lock.txt ghi phiên bản cài kiểm tra.
Lock Python là baseline phiên bản đã kiểm tra trên Windows; CI sẽ xác nhận trên Linux khi push.

Nếu npm báo UNABLE_TO_VERIFY_LEAF_SIGNATURE trên máy có chứng chỉ tổ chức,
Node 24 có thể dùng chứng chỉ hệ thống cho phiên PowerShell hiện tại:

```powershell
$env:NODE_USE_SYSTEM_CA='1'
npm ci
```

Không tắt strict-ssl hoặc kiểm tra TLS.

Nếu chính sách Windows chặn phần mở rộng nhị phân SQLAlchemy, có thể build Python thuần:

```powershell
$env:DISABLE_SQLALCHEMY_CEXT='1'
backend/.venv/Scripts/python.exe -m pip install --force-reinstall --no-binary=sqlalchemy 'sqlalchemy==2.1.9'
```

## Advisory dependency thực tế

npm audit ngày 18/11 báo advisory GHSA-fc5q-39xc-vjpf của picomatch, lan qua
5 dependency phát triển (picomatch/fdir/tinyglobby/vite/plugin-react).
Registry lúc kiểm tra chưa có bản picomatch mới hơn 4.0.7; advisory bao gồm <=4.0.7.
Không tự downgrade major hoặc dùng audit fix --force để che vấn đề.
Giữ Vite chỉ bind localhost, không chạy với cây source/glob không tin cậy.
Cần chạy lại npm audit và nâng dependency khi upstream có bản sửa.
Đây là giới hạn đã biết, không phải một lần audit sạch.

## Bằng chứng kiểm tra

Docker/GitHub CI không được xem là đã chạy chỉ vì có file cấu hình.

## Kết quả cuối

- pytest: 18 passed, gồm CRUD/persistence, UTC timestamp, in-memory SQLite, nguồn 404,
  stub 501, OpenAPI SSE và mock có thể tắt.
- Frontend: 5 parser tests passed; typecheck và production build thành công.
- Ruff check và format check thành công.
- Trình duyệt: tải prototype/Roboto, gọi CRUD qua Vite proxy, nhận SSE mock đúng thứ tự;
  không có lỗi JavaScript.
- Docker Compose: config hợp lệ, override mock=false hoạt động. Chưa chạy image/container
  vì Docker Desktop engine đang tắt.
- GitHub CI chưa chạy vì chưa có remote/commit/push.
- Review độc lập tìm được 6 vấn đề; đã sửa và thêm kiểm thử tái hiện trước khi sửa.
