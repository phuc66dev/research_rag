# Chat trong sổ tay — 27/11/2026

Phạm vi tích hợp Phúc (chat/generation/UI) và Phú (history/app shell), tái sử dụng retrieval,
API tài liệu và DocumentSources của Bảo. Không thêm auth, bảng chat hoặc chỉ mục thứ hai.

## Cấu hình và chạy

Thêm vào `backend/.env` hiện có (không ghi đè các biến cũ):

```dotenv
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=your-model-id
LLM_API_KEY=your-key
LLM_TIMEOUT_SECONDS=120
LLM_MAX_TOKENS=2048
```

URL là base URL trước `/chat/completions`; nhà cung cấp phải hỗ trợ Chat Completions SSE,
delta.content dạng chuỗi, finish_reason=stop rồi `data: [DONE]`. Không theo redirect, không
ghi body upstream/key vào lỗi công khai. Key chỉ ở backend. URL/model mặc định rỗng nên
chưa cấu hình thì chat trả 503 rõ ràng; không gọi API hoặc chuyển sang mock tự động.
Một request/lượt, không retry hay đổi nhà cung cấp tự động. Deadline toàn lượt có thể thêm
tối đa 30 giây để kết thúc socket read đang chạy sau hủy/timeout. Không triển khai nhiều
worker API cho demo: khóa chống hai lượt cùng phiên hiện ở trong tiến trình.

Chạy backend từ thư mục `backend`:

```powershell
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Từ repository root:

```powershell
npm --prefix frontend run dev
```

Đăng nhập → Sổ tay môn học → Hỏi AI → chọn PDF ready → nhập câu hỏi → Gửi câu hỏi.
Enter gửi, Shift+Enter xuống dòng. Câu hỏi và tối đa sáu đoạn nguồn liên quan sẽ được gửi
đến nhà cung cấp cấu hình; màn hình nêu rõ điều này. Chọn nguồn lại ảnh hưởng lượt tiếp theo.
Lần đầu xử lý PDF cần tải model embedding như hướng dẫn Bảo.

Câu hỏi tiếp nối dùng tối đa sáu câu hỏi cũ có cùng tập nguồn; retrieval kèm câu hỏi trước
để hiểu các từ như “nó”. Tối đa ba câu trả lời hoàn tất có nguồn/version còn trong phạm vi
hiện tại được dùng làm ngữ cảnh, không làm bằng chứng. Chỉ chunks hiện truy xuất được dùng
làm căn cứ, đánh lại chỉ mục citation cho từng lượt.

Mở lại từ Lịch sử hỏi AI hoặc bộ chọn Cuộc hội thoại trong sổ tay. URL hash giữ workspace và
session để tải lại trang vẫn mở đúng phiên. Hội thoại mới giữ nguyên phiên cũ. Nguồn chọn
được lưu ở message user; assistant lưu citation riêng. Nguồn đã bị xóa/đổi version không
được mở bằng citation cũ; popup báo lỗi. PDF chưa có bbox nên không tô sáng đoạn chính xác.

## Cách lưu và xử lý lỗi

### Dùng Ollama local

Không cần API key cloud hay tài khoản nhà cung cấp. Máy phát triển đã kiểm tra có khoảng
16 GB RAM, RTX 3050 Laptop 4 GB; chọn `qwen2.5:3b` (~1,9 GB tải về) làm điểm khởi đầu.
Đây là lựa chọn theo tài nguyên. Trạng thái CPU và kiểm tra thật nằm ở mục lỗi GPU bên dưới;
chưa có bộ đánh giá chất lượng trên tập tài liệu chuẩn.

1. Tải và cài từ [Ollama cho Windows](https://ollama.com/download/windows), sau đó mở Ollama.
2. Mở PowerShell mới và tải model:

   ```powershell
   ollama pull qwen2.5:3b
   ```

3. Cấu hình `backend/.env` (chỉ cập nhật các dòng LLM, giữ các biến khác):

   ```dotenv
   LLM_BASE_URL=http://127.0.0.1:11434/v1
   LLM_MODEL=qwen2.5:3b
   LLM_API_KEY=ollama
   LLM_TIMEOUT_SECONDS=120
   LLM_MAX_TOKENS=2048
   ```

   `ollama` chỉ là giá trị minh họa công khai, không phải key bí mật. Chọn model local,
   không chọn model có hậu tố `:cloud`. Nếu cổng chưa chạy, mở Ollama hoặc dùng `ollama serve`.
   Giữ API ở localhost, không đặt OLLAMA_HOST=0.0.0.0.

4. Từ repository root, kiểm tra bằng nguồn/câu hỏi tổng hợp, không đọc PDF hay database:

   ```powershell
   backend/.venv/Scripts/python.exe backend/scripts/check_ollama.py
   ```

   Script chỉ cho phép loopback/cổng 11434, từ chối gửi request tới dịch vụ cloud. Báo rõ
   khi server chưa chạy hoặc model chưa tải; kiểm tra stream qua đúng transport ứng dụng.
   Sau đó khởi động lại backend từ thư mục `backend` và thử Hỏi AI trong sổ tay.

Ổ C hiện còn khoảng 11 GB, ổ D còn khoảng 82 GB (tại lúc kiểm tra). Nếu muốn lưu model ở D,
thoát hẳn Ollama ở khay hệ thống, mở PowerShell rồi chạy:

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'D:\Tools\OllamaModels', 'User')
$env:OLLAMA_MODELS = 'D:\Tools\OllamaModels'
ollama serve
```

Giữ terminal server đó mở; dùng terminal thứ hai để `ollama pull qwen2.5:3b`.
Không có thao tác di chuyển/xóa model cũ tự động. Chỉ lần cài/tải model cần mạng; local
inference không phát sinh phí API cloud, nhưng dùng tài nguyên máy.

Lần thiết lập ban đầu ngày 27/11/2026, cài Ollama tự động bị bộ duyệt chặn
(`blocked by policy`). Sau khi người dùng cài phần mềm và tải model, đã kiểm tra được
Ollama 0.40.18 ở localhost và chuyển sang CPU để xử lý lỗi CUDA như mục bên dưới.

Tham chiếu: [API tương thích OpenAI](https://docs.ollama.com/api/openai-compatibility),
[model qwen2.5:3b](https://ollama.com/library/qwen2.5:3b).

### Khi Ollama lỗi GPU trên máy phát triển

Ngày 27/11 đã tái hiện HTTP 500: runner CUDA dừng với `device kernel image is invalid`.
Máy có driver NVIDIA 546.92; tài liệu Ollama Windows yêu cầu 551.61 trở lên. Không cài/đổi
driver trong nhiệm vụ này. Đã tạo model local riêng ép CPU, tái sử dụng trọng số đã tải:

```powershell
ollama create edurag-qwen2.5-cpu -f backend/ollama/Modelfile.cpu
```

Chạy từ repository root. Modelfile giữ `qwen2.5:3b`, đặt `num_gpu=0`, `num_ctx=8192`.
Không xóa/ghi đè model gốc, không đổi cấu hình GPU toàn máy. Trong `backend/.env` dùng
`LLM_MODEL=edurag-qwen2.5-cpu:latest`, URL vẫn `http://127.0.0.1:11434/v1`, key công khai
`ollama`. Khởi động lại backend hoặc chờ uvicorn reload nạp lại cấu hình.

Đã kiểm tra model thật bằng câu hỏi tổng hợp trên CPU qua transport SSE của ứng dụng:
“2 + 2 bằng mấy?” → “2 + 2 bằng 4.”. Đây là kiểm tra kết nối, chưa chứng minh chất lượng
RAG trên tài liệu cá nhân. CPU có thể chậm hơn GPU. Thông báo HTTP 500/404 của Ollama
giờ hướng dẫn kiểm tra runner/model; 401/403/429 phân biệt quyền/key và hạn mức, không đưa
body lỗi upstream hoặc bí mật ra UI.

Kiểm tra xuyên suốt bổ sung: PDF tổng hợp → extraction/retrieval → model CPU thật → SSE
status/citations/token/done → lưu hai tin nhắn và mở lại qua history: HTTP 200, assistant
completed, citation đúng document_id, khoảng 5,9 giây cho câu hỏi tổng hợp ngắn. Embedding
trong kiểm tra này là fixture có nhãn; database/file riêng trong backend/data, không dùng
PDF hoặc lịch sử cá nhân. `/api/ps` xác nhận model CPU có size_vram=0, context_length=8192.
Sau sửa lỗi CPU: `pytest backend/tests -q --basetemp backend/data/cpu-fix-tests-20261127-a
--tb=short` qua **84 passed, 1 skipped**; Ruff check và format check qua (66 file).
Backend uvicorn reload đã khởi động worker mới sau khi cập nhật cấu hình LLM.

Tham chiếu yêu cầu driver: [Ollama Windows](https://docs.ollama.com/windows).

### Quy tắc lưu

- Trước stream kiểm tra auth, owner phiên/workspace và mọi nguồn qua retrieval hiện có.
- Câu hỏi và placeholder assistant `interrupted` được ghi trong một transaction qua history
  service. Mỗi delta được lưu trước khi gửi; chỉ sau kết thúc hợp lệ mới thành `completed`.
- Có status/citations/token/done/error đúng hợp đồng. Nguồn đến trước token.
- Provider lỗi, cắt do giới hạn hoặc thiếu `[DONE]`: giữ text, đánh dấu `error`, không có done.
  Dừng/chuyển trang/crash giữ `interrupted`. Giao diện chỉ completed khi nhận done.
- Lỗi giữ câu hỏi trong ô nhập và nội dung đã nhận, không tự gửi lại. Có nút tải lại hội thoại;
  người dùng chủ động quyết định gửi câu hỏi tiếp theo. Khi mất mạng, nội dung hiển thị có
  thể mới hơn lần tải lịch sử gần nhất; backend lưu từng delta để mở lại sau.
- Không có kết quả retrieval thì không gọi LLM; báo chưa đủ thông tin. Có kết quả không
  đồng nghĩa có đáp án: prompt yêu cầu báo thiếu căn cứ, dùng trích dẫn trong danh sách.
- Chưa có bộ đánh giá chất lượng RAG/grounding tự động. Chỉ mục nguồn sai bị đánh dấu lỗi,
  nhưng không có kiểm chứng ngữ nghĩa chứng minh từng nhận định đúng.

## File và hợp đồng

Backend: `api/chat.py`, `services/rag/generation.py`, `services/rag/provider.py`, cấu hình LLM.
History thêm begin_stream/update_stream; repository hỗ trợ ghi hai message nguyên tử và
cập nhật nội dung/trạng thái. Không đổi schema DB, không cần migration/dependency mới.
Frontend: `features/study/`, nút Hỏi AI ở workspace, điểm gắn màn hình trong AppShell,
transport SSE có credentials và xử lý error/done. ApiError viết bằng cú pháp có thể chạy
với Node strip-types để kiểm thử transport thật.

Request chat và loại event không đổi; endpoint thật từ 501 thành SSE 200. REST session/message
giữ nguyên schema; bổ sung ý nghĩa user.sources làm snapshot nguồn. Chi tiết ở
`contracts/rag.md`; OpenAPI phải xuất từ code bằng script. Phúc/Phú review consumer trước merge.

## Kiểm tra

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m ruff check backend
backend/.venv/Scripts/python.exe -m ruff format --check backend
npm --prefix frontend test
npm --prefix frontend run build
backend/.venv/Scripts/python.exe backend/scripts/export_openapi.py
```

Nếu temp mặc định Windows bị PermissionError, thêm `--basetemp backend/data/chat-tests-<mã-mới>`
vào lệnh pytest. Luôn chọn đường dẫn mới dành riêng cho test, vì pytest dọn basetemp nếu đã có.

Test integration dùng PDF thật và auth/retrieval/history thật, embedding/provider là fixture
có nhãn trong test. Test provider dùng HTTP server cục bộ để kiểm tra request, UTF-8 SSE,
upstream lỗi và stream dở; không dùng key thật hoặc gọi API tính phí. Browser QA dùng DB,
PDF và provider fixture riêng có nhãn, không dùng database người dùng.

Đã kiểm tra Ollama CPU thật bằng dữ liệu tổng hợp; chưa xác minh nhà cung cấp cloud hoặc
chất lượng câu trả lời trên tập PDF chuẩn. Bộ test
không chứng minh chất lượng model và không thay thế nghiệm thu hai tài khoản ngoài môi trường test.
Chưa triển khai chống trùng request xuyên reconnect hoặc khóa stream qua nhiều tiến trình.

Kết quả kiểm tra lần triển khai chat ban đầu ngày 27/11/2026:

- `pytest backend/tests -q --basetemp backend/data/chat-tests-20261127-d --tb=short`
  bằng Python trong `.venv`: **79 passed, 1 skipped** (test model thật cần opt-in).
- `ruff check backend` và `ruff format --check backend`: qua, 65 file đúng định dạng.
- `npm --prefix frontend test`: **14 passed**; `npm --prefix frontend run build`: qua.
- Xuất OpenAPI từ ứng dụng và `git diff --check`: qua.
- Browser QA bằng fixture riêng: gửi/lưu, tải lại trang, mở từ lịch sử, phục hồi nguồn,
  popup PDF, Escape, Enter gửi, lỗi giữa stream giữ câu hỏi/text, câu trả lời 40 đoạn có
  cuộn riêng, Dừng không tự gửi lại, mở lại giữ trạng thái chưa hoàn tất. DOM desktop
  1440px: hai cột 333.6/778.4px; mobile 390px: một cột, không tràn ngang.
- Better Design MCP chưa kết nối; kiểm tra DOM/screenshot dùng trình duyệt local.
  Lần kiểm tra giao diện ban đầu dùng provider fixture; lần kiểm tra Ollama thật được
  ghi riêng ở mục CPU bên trên. Dữ liệu cá nhân không được dùng trong các smoke test.

Tài liệu transport tham chiếu: [Chat Completions API](https://developers.openai.com/api/reference/resources/chat).
