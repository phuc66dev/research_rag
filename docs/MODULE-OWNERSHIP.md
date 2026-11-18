# Phân công theo module — EduRAG-VN

Cập nhật: 18/11/2026. Đây là phân công hiện hành, thay thế cách chia Phúc=RAG, Bảo=Backend, Phú=Frontend.
Mỗi người sở hữu module từ giao diện đến API, dữ liệu, kiểm thử và tài liệu.
Không coi các chức năng trong kế hoạch này là đã triển khai; bootstrap hiện vẫn thiếu auth và RAG thật.

## 1. Phân công và cân bằng

| Thành viên | Module chính | Phần hệ thống bổ sung |
| --- | --- | --- |
| **Phúc** | Sổ tay môn học; Không gian học tập/Hỏi đáp AI | Điều phối câu trả lời LLM, SSE, popup kiểm chứng và quyền trên workspace/chat |
| **Bảo** | Tài liệu của tôi | Lưu file, extraction/chunking, lập chỉ mục, retrieval và dọn nguồn khi xóa |
| **Phú** | Lịch sử AI | Authentication, Authorization nền tảng, tài khoản và app shell dùng chung |

### Điểm công việc đề xuất

Điểm là ước lượng tương đối cho **phần còn phải làm sau bootstrap**, không phải số giờ.
Tổng bằng nhau là điểm khởi đầu; cần điều chỉnh sau mỗi vòng tích hợp theo thời gian thực tế,
độ khó và lỗi phát sinh. Chưa có dữ liệu năng lực từng người để cam kết giờ làm chính xác bằng nhau.

| Người | Hạng mục | Điểm |
| --- | --- | ---: |
| Phúc | Sổ tay xuyên suốt: danh sách/tạo/đổi tên/xóa, API, liên kết owner | 5 |
| Phúc | Workspace hai cột, chọn nguồn và composer React | 6 |
| Phúc | Tích hợp retrieval, LLM và SSE có xử lý gián đoạn | 7 |
| Phúc | Citation và popup PDF đúng file/trang | 4 |
| Phúc | Kiểm tra quyền workspace/chat tại điểm tích hợp | 2 |
| Phúc | Test module, tích hợp, review và tài liệu/demo phần mình | 6 |
| **Phúc** | **Tổng** | **30** |
| Bảo | Tài liệu của tôi: UI, API, trạng thái rỗng/tải/lỗi | 5 |
| Bảo | Upload, kiểm tra loại/dung lượng/hash, lưu file và metadata | 5 |
| Bảo | Trích xuất PDF có text, chia đoạn, giữ vị trí nguồn | 5 |
| Bảo | Embedding, chỉ mục và tìm kiếm trong tập nguồn hợp lệ | 7 |
| Bảo | Thử lại/dọn dữ liệu khi xóa, chống job tái tạo nguồn bị xóa | 3 |
| Bảo | Test module, tích hợp, review và tài liệu/demo phần mình | 5 |
| **Bảo** | **Tổng** | **30** |
| Phú | Lịch sử: UI, API phiên/tin nhắn, tìm/lọc/mở lại/xóa | 6 |
| Phú | Authentication: đăng ký, đăng nhập, phiên, đăng xuất, me và UI | 7 |
| Phú | Authorization nền tảng và hợp đồng current user cho các module | 4 |
| Phú | App shell/sidebar, route bảo vệ, tài khoản và API client dùng chung | 4 |
| Phú | Hạ tầng test auth, dữ liệu thử hai tài khoản và hỗ trợ CI | 3 |
| Phú | Test module, tích hợp, review và tài liệu/demo phần mình | 6 |
| **Phú** | **Tổng** | **30** |

Việc tích hợp và review đã nằm trong điểm của cả ba. Không dồn toàn bộ công việc cuối kỳ
cho người có module hoàn thành sớm hoặc cho người giữ file main.py.

## 2. Phúc — Sổ tay và Không gian học tập

### Giao diện
- Danh sách/tạo/đổi tên/xóa sổ tay; đếm tài liệu bằng dữ liệu thật.
- Workspace hai cột 30%/70%, chọn nguồn, chat, trạng thái tìm nguồn/sinh nội dung/lỗi.
- Popup PDF và highlight khi có tọa độ hợp lệ; phản hồi rõ khi nguồn đã bị xóa.

### Backend và dữ liệu
- CRUD workspace theo owner, không tin user_id từ client.
- API streaming chat: kiểm tra user/workspace/session/nguồn, gọi retrieval của Bảo,
  gọi LLM và sinh citation đúng dữ liệu nguồn.
- Sử dụng service lưu hội thoại của Phú; không tự tạo bảng/repository chat thứ hai.
- Khi xóa workspace, điều phối dọn tài liệu/chỉ mục qua Bảo và lịch sử qua Phú.
  Không tự sao chép logic xóa của các module khác.

### Đầu ra nghiệm thu
- Hai tài khoản không thấy sổ tay của nhau.
- Chọn nguồn ảnh hưởng đúng câu hỏi tiếp theo; không truy xuất ngoài nguồn được cấp quyền.
- Có trả lời từ tài liệu thật, thiếu căn cứ thì nêu rõ; mở đúng file/trang nguồn.
- Hội thoại được lưu qua service lịch sử và có trạng thái hoàn tất/gián đoạn.

## 3. Bảo — Tài liệu và nguồn tìm kiếm

### Giao diện
- Trang Tài liệu của tôi, bộ chọn môn, tải tệp, bảng trạng thái, lỗi/thử lại/xóa.
- Thành phần nguồn tài liệu có thể cung cấp cho Phúc dùng trong workspace qua props/API,
  không sửa trực tiếp trang học tập của Phúc.

### Backend và dữ liệu
- Document model/schema/repository, lưu file, hash, trạng thái và tác vụ xử lý.
- Kiểm tra quyền workspace trước upload/list; kiểm tra owner trước file/status/delete.
- PDF có text → chuẩn hóa → chia đoạn → embedding/chỉ mục → retrieval có bộ lọc quyền/phạm vi.
- Cung cấp search service cho Phúc, không gọi LLM để tạo câu trả lời.
- Cung cấp file gốc, page metadata và bbox nếu có; không tạo tọa độ/số trang giả.
- Xóa file/chunk/vector và ngăn tác vụ đang chạy tạo lại tài liệu đã xóa.
- Phối hợp Phú vô hiệu hóa citation đã lưu tới tài liệu bị xóa.

### Đầu ra nghiệm thu
- Chỉ nhận định dạng/giới hạn đã thống nhất; hash nội dung phát hiện trùng trong cùng môn.
- Tệp lỗi không thành ready giả; dữ liệu tồn tại sau khi khởi động lại.
- PDF được lập chỉ mục và tìm lại đúng đoạn; không trả nguồn người khác dù sửa ID trực tiếp.
- Xóa hoặc thử lại không để lại bản ghi/chỉ mục trùng ngoài ý muốn.

## 4. Phú — Lịch sử và nền tảng tài khoản

### Giao diện
- Lịch sử: danh sách/tìm kiếm/lọc môn, tiếp tục phiên, xóa hội thoại.
- Đăng ký/đăng nhập, trạng thái hết phiên, tài khoản hiện tại và đăng xuất.
- App shell/sidebar/route bảo vệ dùng chung. Cung cấp điểm gắn trang cho Phúc/Bảo,
  không tự viết màn hình nghiệp vụ của họ.

### Backend và dữ liệu
- User, phiên đăng nhập và service lấy current user.
- Session/message model và service lưu câu hỏi, câu trả lời, tập nguồn, citation, trạng thái stream.
- API lịch sử luôn lọc theo chủ sở hữu; mở lại dẫn tới workspace/session đúng.
- Hợp đồng authentication và helper authorization để hai module còn lại sử dụng.
- Authorization không chỉ là ẩn nút trên UI: từng chủ module phải áp dụng ở endpoint/service.
- Cung cấp helper xử lý lịch sử/citation khi workspace hoặc tài liệu bị xóa.

### Authentication/Authorization tối thiểu
- Đăng ký, đăng nhập, đăng xuất, lấy tài khoản hiện tại; kiểm tra dữ liệu đầu vào.
- Hash mật khẩu bằng thư viện phù hợp, không tự viết thuật toán hoặc lưu mật khẩu rõ.
- Mặc định đề xuất một cơ chế phiên phía máy chủ qua cookie HttpOnly; cả nhóm thống nhất
  trước khi triển khai. Không tự dùng đồng thời JWT và session ở các module khác nhau.
- Nếu dùng cookie: thống nhất SameSite, Secure theo môi trường, hết hạn/thu hồi phiên
  và bảo vệ CSRF cho thao tác thay đổi dữ liệu.
- Lấy owner từ danh tính đã xác thực; không nhận owner tùy ý từ JSON client.
- P0: người dùng thường và quyền sở hữu dữ liệu cá nhân. Chưa làm admin panel/RBAC nhiều cấp,
  OAuth, email reset mật khẩu hoặc chia sẻ nhóm.
- Test bằng ít nhất hai tài khoản, gồm sửa ID workspace/document/session và URL file.
- Auth thật chưa có trong bootstrap. Chỉ override user trong test fixture có kiểm soát;
  không đưa user cố định vào API thật như một cách giả lập đã có phân quyền.

## 5. Tổ chức file để giảm xung đột

Giữ cấu trúc backend theo lớp đang có nhưng chia file theo domain. Các đường dẫn dưới đây
chưa tồn tại thì được tạo khi bắt đầu nhiệm vụ; kế hoạch không tự di chuyển code.

| Người | Backend | Frontend đề xuất | Test |
| --- | --- | --- | --- |
| Phúc | api/workspaces.py, api/chat.py; models/schemas/repositories workspace; services/workspaces/; services/rag/ phần generation/SSE | src/features/workspaces/, src/features/study/, src/api/workspaces.ts, src/api/chat.ts, src/api/events.ts | backend/tests/workspaces/, backend/tests/chat/; frontend test tương ứng |
| Bảo | api/documents.py; models/schemas/repositories document; services/documents/; services/retrieval/ | src/features/documents/, src/api/documents.ts | backend/tests/documents/, backend/tests/retrieval/; frontend test tương ứng |
| Phú | api/auth.py, api/sessions.py; models/schemas/repositories user/session/message; core/security.py; services/auth/, services/history/ | src/features/auth/, src/features/history/, src/app/; shared API client | backend/tests/auth/, backend/tests/history/; frontend test tương ứng |

- services/rag/contracts.py do Phúc điều phối, Bảo/Phú review khi ảnh hưởng consumer.
- Bảo quản lý main.py, database/Base chung, dependency backend và đầu mối migration.
- Phú quản lý App.tsx, route/app shell, style/token chung, API base client, dependency frontend.
- Phúc quản lý SSE client/parser và hợp đồng chat; Bảo quản lý hợp đồng retrieval.
- Mỗi người sở hữu file type/schema riêng của module, không để cả ba thêm mọi kiểu vào một file types.ts.
- Mỗi người viết migration riêng cho model của mình sau khi baseline migration được chốt;
  Bảo điều phối thứ tự để tránh nhiều migration head. Không tạo thêm ORM Base.
- Thay đổi OpenAPI snapshot do người sửa API xuất lại; khi ghép tuần tự phải xuất từ code mới nhất.
- Tests/test_bootstrap.py hiện là baseline chung, sửa có phối hợp; test mới nên nằm trong domain riêng.
- Chỉ sửa file chung trong PR nhỏ đã ghi rõ. Chưa cần tái cấu trúc toàn backend sang modules/
  nếu việc đó không phục vụ một tính năng cụ thể.

## 6. Điểm giao tiếp cần chốt trước khi code song song

### Phú → Phúc/Bảo: danh tính và quyền
- Một dependency current user dùng chung, cung cấp định danh đã xác thực từ máy chủ.
- Một quy tắc phản hồi thống nhất cho chưa đăng nhập và không được truy cập.
- Phú cung cấp cơ chế; Phúc/Bảo thêm owner/query filter vào từng resource của mình.
- Bảo tách/ổn định ORM Base dùng chung trước khi cả ba thêm model.

### Bảo → Phúc: nguồn
- Hợp đồng chunk/index và search: user context, workspace ID, document IDs, query,
  kết quả gồm document version, text, page/bbox nếu có.
- Prototype interface đề xuất: index_document(...), search_sources(...), delete_document_index(...).
  Đây chưa phải API đang có; cần chốt chữ ký và kiểu ở PR hợp đồng đầu tiên.
- User context do backend xác thực truyền vào, không lấy trực tiếp từ user_id client.

### Phú ↔ Phúc: hội thoại
- Phú sở hữu tạo phiên, đọc/ghi message và lưu citation; Phúc sở hữu stream trả lời.
- Phúc gọi service của Phú để ghi câu hỏi trước stream và chốt trạng thái câu trả lời sau stream.
- Chốt cách lưu khi người dùng ngắt kết nối; không tự coi stream dở là completed.
- Tiếp tục từ lịch sử mở đúng workspace/session; tập nguồn trước đây được lưu với request,
  nguồn đã xóa phải có thông báo thay vì link hỏng.

### Phúc ↔ Bảo: UI nguồn và xóa workspace
- Phúc dùng API/component tài liệu của Bảo; không tự làm upload thứ hai trong workspace.
- Xóa workspace phải có một luồng điều phối rõ cho file/vector/lịch sử, tránh chỉ xóa hàng SQL.

Hợp đồng auth và history do Phú đề xuất; retrieval do Bảo đề xuất; chat/workspace do Phúc đề xuất.
Mọi bên cung cấp và sử dụng cùng review. Chỉ cập nhật OpenAPI khi endpoint/schema đã có code,
không tạo snapshot giả cho tính năng chưa triển khai.

## 7. Thứ tự triển khai

### M0 — Chốt nền dùng chung
- Cả nhóm: baseline Git/PR/CI và hợp đồng module.
- Bảo: ORM Base/database và điểm đăng ký router dùng chung.
- Phú: app shell, route slots và hợp đồng current user.
- Phúc: hợp đồng chat/citation và ranh giới generation–retrieval.
- Không đợi auth xong để làm UI/test: có thể dùng fixture có nhãn; code thật vẫn phải qua auth.

### M1 — Mỗi người có một lát cắt chạy được
- Phúc: đăng nhập → tạo/list sổ tay của mình.
- Bảo: chọn workspace hợp lệ → upload PDF → xem trạng thái.
- Phú: đăng ký/đăng nhập/đăng xuất/me; API tạo/list phiên theo owner.
- Ghép auth và owner filtering sớm, không để đến cuối mới thêm user_id vào toàn hệ thống.

### M2 — Tích hợp luồng học tập
- Bảo cung cấp retrieval trên PDF thật.
- Phúc cung cấp hỏi đáp/citation; dùng dịch vụ lưu hội thoại của Phú.
- Phú cung cấp lịch sử và mở lại đúng phiên.
- Thử hai tài khoản: không thể truy cập chéo kể cả sửa URL/ID.

### M3 — Kiểm thử và bàn giao
- Mỗi người test/sửa lỗi module mình, review chéo và cập nhật tài liệu.
- Review chính: Phúc → Bảo; Bảo → Phú; Phú → Phúc (mũi tên là người tạo PR → reviewer).
- Thay đổi hợp đồng/security phải có thêm review của bên sử dụng khi cần.
- Giữ mốc trước đây: dừng thêm tính năng 18:00, chốt nội bộ 22:00, deadline 23:59
  thứ Sáu 20/11/2026 UTC+7, trừ khi nhóm thay đổi deadline.

## 8. Phạm vi phù hợp với thời hạn ngắn

Ưu tiên: auth tối thiểu, quyền sở hữu, workspace, PDF có text, hỏi đáp có nguồn và lịch sử.
Các hạng mục từng thuộc P0 đầy đủ nhưng chưa phù hợp demo rút gọn cần ghi rõ chưa đạt.
Chưa nhận OCR bản scan khó, DOCX/TXT hoàn chỉnh, OAuth/reset email, admin/RBAC nâng cao,
Drive/n8n, Quiz/Flashcard vào đợt này nếu chưa có quyết định đổi phạm vi/thời gian.

Việc thêm auth làm tăng khối lượng so với demo một người trước đây. Không cam kết đạt toàn bộ PRD
trong ba ngày chỉ vì dùng AI. Nếu không đủ thời gian, báo phần thiếu và điều chỉnh phạm vi/mốc;
không bỏ kiểm tra quyền hoặc đổi nhãn mock thành chức năng thật.

## 9. Điều kiện công bằng và hoàn thành

- Mỗi module bàn giao UI + API + dữ liệu + test + hướng dẫn; không chấm hoàn thành chỉ vì giao diện đẹp.
- Hằng ngày ghi thời gian thực, điểm đã xong, điểm bị chặn và phần việc đang chờ.
- Nếu một người lệch đáng kể, chuyển một task độc lập còn chưa làm và cập nhật owner trước khi sửa;
  không để hai AI cùng sửa một file rồi tính là hỗ trợ.
- Công việc chung phải ghi tên người làm và chia vào khối lượng, không để thành việc vô chủ.
- PR cần có test happy path, đầu vào lỗi và truy cập trái owner cho module có dữ liệu cá nhân.
- Backend + frontend phải dùng cùng hợp đồng; không trả 200 [] cho tính năng chưa làm.
- Plan này chỉ thay đổi phân công/phạm vi tổ chức. Auth, retrieval và các màn hình mới chưa được
  tạo chỉ bằng việc cập nhật tài liệu.
