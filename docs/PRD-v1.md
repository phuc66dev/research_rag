# EduRAG-VN — PRD v1

| Thuộc tính | Nội dung |
| --- | --- |
| Sản phẩm | Không gian học tập AI trên tài liệu tiếng Việt |
| Phiên bản tài liệu | 1.0 — Bản phác thảo để duyệt |
| Ngày cập nhật | 18/11/2026 |
| Bản phát hành trọng tâm | P0: quản lý tài liệu, hỏi đáp có nguồn và kiểm chứng |
| Người dùng trọng tâm | Sinh viên học tập cá nhân trên desktop/laptop |
| Tài liệu nền | [PRD ban đầu](PRD.md), [đặc tả giao diện](../DESGIN.md), [prototype HTML](../edurag-p0.html) |

> Cập nhật 18/11/2026: hủy phân công theo tầng kỹ thuật, áp dụng [phân công theo module](MODULE-OWNERSHIP.md). Authentication/Authorization cơ bản được bổ sung cho đợt triển khai; bootstrap hiện chưa có các chức năng này.

## 1. Tóm tắt sản phẩm

EduRAG-VN giúp sinh viên gom tài liệu theo môn học, hỏi đáp bằng tiếng Việt và kiểm chứng câu trả lời ngay tại đoạn nguồn. Sản phẩm tập trung vào giáo trình, đề cương, bài giảng PDF và tài liệu văn bản do người dùng cung cấp.

Giá trị cốt lõi của P0 là một luồng hoàn chỉnh: **tạo sổ tay → thêm tài liệu → xử lý → chọn nguồn → đặt câu hỏi → kiểm chứng → tiếp tục hội thoại**.

Tài liệu này điều chỉnh phạm vi bản phát hành đầu từ PRD ban đầu. Các mục ghi “đã chốt” dựa trên trao đổi thiết kế; các mục ghi “đề xuất” cần được duyệt cùng bản PRD. Tài liệu không xác nhận các tính năng đã được lập trình hoặc nghiệm thu.

### 1.1. Hiện trạng

- Đã có prototype HTML với các màn hình P0, dữ liệu mẫu và một số tương tác lưu cục bộ trên trình duyệt.
- Prototype chưa kết nối dịch vụ hỏi đáp AI, OCR, vector database, xác thực hoặc đồng bộ Drive.
- Trong phạm vi rà soát tài liệu lần này, chưa có bằng chứng về một backend vận hành hoặc bản thiết kế đã được ghi thành công vào Figma.
- Không dùng kết quả từ prototype để kết luận về độ chính xác RAG, hiệu năng hoặc độ an toàn của hệ thống thật.

## 2. Vấn đề và người dùng

### 2.1. Vấn đề cần giải quyết

1. Tài liệu môn học nằm rải rác, khó xác định nguồn đang được dùng khi hỏi AI.
2. Tìm định nghĩa, thuật ngữ hoặc thông tin cụ thể trong giáo trình dài tốn thời gian.
3. Câu trả lời AI thiếu nguồn đáng tin cậy, khó kiểm tra đúng file và đoạn văn.
4. PDF scan, bảng mã tiếng Việt cũ và tài liệu có cấu trúc phức tạp gây lỗi trích xuất.
5. Phiên hỏi đáp bị mất ngữ cảnh hoặc khó tìm lại khi tiếp tục học.

Đây là các giả thuyết nhu cầu từ tài liệu nền; cần kiểm chứng bằng quan sát người dùng thử nghiệm.

### 2.2. Nhóm người dùng

| Nhóm | Nhu cầu | Phạm vi |
| --- | --- | --- |
| Sinh viên cá nhân | Quản lý tài liệu, hỏi bài, kiểm chứng và xem lại hội thoại | Trọng tâm P0 |
| Nhóm học tập / lớp trưởng | Chia sẻ và đồng bộ kho tài liệu của lớp | Giai đoạn sau |
| Giảng viên / trợ giảng | Cung cấp nguồn chuẩn, xem phản hồi chất lượng | Giai đoạn sau |
| Người vận hành | Chẩn đoán lỗi xử lý và tình trạng dịch vụ AI | Công cụ vận hành tối thiểu P0; dashboard riêng chưa thuộc P0 |

### 2.3. Công việc người dùng muốn hoàn thành

> Khi ôn một môn học, tôi muốn hỏi từ những tài liệu đã chọn và xem ngay đoạn nguồn để biết câu trả lời có phù hợp với giáo trình của mình hay không.

## 3. Mục tiêu và cách đánh giá

### 3.1. Mục tiêu P0

- Hoàn thành luồng học tập cốt lõi bằng tài liệu thật, không cần dữ liệu mẫu.
- Người dùng biết tài liệu nào sẵn sàng và tài liệu nào đang được dùng cho câu hỏi.
- Câu trả lời có căn cứ đi kèm nguồn có thể mở để kiểm chứng.
- Khi nguồn không đủ, hệ thống nêu rõ hạn chế thay vì trình bày suy đoán như kiến thức trong tài liệu.
- Dữ liệu và hội thoại tồn tại sau khi tải lại trang hoặc khởi động lại dịch vụ.
- Chi phí sử dụng được kiểm soát trên môi trường nhỏ; không cần GPU cho embedding trong cấu hình cơ sở đề xuất.

### 3.2. Chỉ số mục tiêu đề xuất

Các ngưỡng dưới đây là mục tiêu thử nghiệm, chưa phải cam kết SLA. Báo cáo phải ghi cấu hình máy, mô hình, kích thước tài liệu, tải đồng thời và trạng thái cache.

| Chỉ số | Cách đo | Mục tiêu ban đầu |
| --- | --- | --- |
| Hoàn thành luồng chính | Người thử tự tạo môn, nạp tài liệu, hỏi và mở nguồn mà không cần hướng dẫn trực tiếp | ≥ 80% trong đợt thử tối thiểu 5 sinh viên |
| Trích dẫn chính xác | Số trích dẫn vừa hỗ trợ nhận định vừa chỉ đúng vị trí / tổng trích dẫn được đánh giá | ≥ 90% |
| Từ chối đúng khi thiếu dữ liệu | Số câu ngoài tài liệu được thông báo không đủ dữ liệu / tổng câu ngoài tài liệu | ≥ 95% |
| Trả lời hữu ích trong tài liệu | Số câu trong phạm vi được đánh giá đúng, đủ ý và có nguồn / tổng câu trong phạm vi | ≥ 85%; theo dõi để tránh đạt tỷ lệ từ chối bằng cách từ chối mọi câu |
| Tốc độ token đầu | Từ lúc gửi yêu cầu hợp lệ đến token nội dung đầu tiên, không tính sự kiện trạng thái | Mục tiêu p95 ≤ 2,5 giây khi tài liệu đã sẵn sàng; cần đo baseline trước |
| Cô lập dữ liệu | Bộ kiểm tra truy cập file, chat, metadata và tìm kiếm chéo phạm vi | Không có trường hợp truy cập vượt quyền trong bộ kiểm tra |

Tập đánh giá đề xuất gồm ít nhất 100 câu trong tài liệu và 40 câu ngoài tài liệu, có đáp án/nguồn tham chiếu do người đọc kiểm tra. Bao gồm câu hỏi khái niệm, từ khóa chính xác, câu tổng hợp nhiều nguồn và trường hợp OCR lỗi. Đánh giá riêng PDF có text, PDF scan và DOCX/TXT.

Không cam kết vận hành luôn miễn phí hoặc độ sẵn sàng 99% dựa trên các API miễn phí. Hạn mức, giá và mô hình thực tế phải được kiểm tra khi triển khai.

## 4. Phạm vi bản phát hành

### 4.1. P0 — Bắt buộc

- Xác thực tài khoản, quản lý phiên và phân quyền sở hữu theo mục P0-AUTH.
- Tạo, liệt kê, tìm kiếm, đổi tên và xóa sổ tay môn học.
- Thêm PDF, DOCX, TXT; giới hạn 50 MB/tệp; kiểm tra nội dung trùng trong cùng môn học.
- Xử lý ngầm, theo dõi trạng thái, thông báo thất bại và thử lại có kiểm soát.
- Trích xuất văn bản tiếng Việt, chuẩn hóa Unicode, OCR cho trang scan được hỗ trợ.
- Tìm kiếm kết hợp ngữ nghĩa và từ khóa, lọc theo môn học và các nguồn được chọn.
- Hỏi đáp bám sát tài liệu bằng streaming, có nguồn, có thông báo khi không đủ căn cứ.
- Popup kiểm chứng: PDF theo trang/đoạn; DOCX/TXT theo đoạn văn có định danh ổn định.
- Tạo phiên hội thoại, lưu lịch sử, mở lại đúng môn học.
- Sidebar dùng chung, popup tài khoản và các trạng thái rỗng, tải, lỗi.
- Lưu trữ phía máy chủ, kiểm soát phạm vi truy cập và ghi nhận lỗi vận hành.

### 4.2. P1 — Sau khi P0 đạt nghiệm thu

- Chế độ Gia sư, phân biệt rõ giải thích mở rộng với kiến thức trong nguồn.
- Like/Dislike và báo lý do câu trả lời sai.
- Sinh quiz, làm bài, chấm điểm và xem nguồn giải thích.
- Đồng bộ Google Drive và thông báo tài liệu mới qua n8n.
- Reranker nâng cao, semantic cache và điều phối nhà cung cấp bổ sung sau khi có đo lường.

Lưu ý: khả năng thông báo thiếu căn cứ thuộc P0 trong bản đề xuất này; mô hình reranking cụ thể không phải điều kiện để thực hiện hành vi đó.

### 4.3. P2 / Chưa thuộc bản đầu

- Flashcards, bot Telegram/Discord, chia sẻ workspace và phân quyền nhóm.
- Dashboard giảng viên, dashboard quản trị đầy đủ.
- Ứng dụng native, thanh toán, fine-tune mô hình riêng.
- Hiểu hoàn hảo bảng biểu, công thức phức tạp, chữ viết tay hoặc mọi loại bản scan.

Không đưa chức năng chưa triển khai thành nút có vẻ hoạt động. Google Drive có thể giữ mục điều hướng “Sắp có”; bỏ badge thông báo giả và dữ liệu giả khỏi bản phát hành thật.

## 5. Trải nghiệm và màn hình

### 5.1. Những quyết định thiết kế đã chốt

- Giao diện trắng–xanh tím, viền mảnh, icon nét mảnh; font **Roboto** hỗ trợ tiếng Việt.
- Sidebar tích hợp vào app shell, có tìm kiếm, bốn mục: Sổ tay môn học, Tài liệu của tôi, Google Drive, Lịch sử hỏi AI.
- Tài khoản nằm cuối sidebar; dấu “…” mở popup. Dạng thu gọn mở popup từ avatar.
- Popup tài khoản chứa thông tin cá nhân, Hồ sơ, Thông báo, Cài đặt, Trợ giúp và Đăng xuất. Chỉ hiển thị hành động thật phù hợp với cách xác thực được chọn.
- Không có nút chuyển “Cá nhân / Nhóm học”.
- Không gian học tập gồm **nguồn tài liệu khoảng 30% và trợ lý AI khoảng 70%**, tính trên vùng nội dung sau sidebar.
- PDF xuất hiện trong popup từ nút nguồn; không có cột đọc PDF cố định.
- Khôi phục bo góc mềm theo HTML mới nhất: control khoảng 6px, thẻ 8px, popup 12px và avatar tròn. **Giới hạn 2px trước đây đã bị hủy.**

`DESGIN.md` còn quy tắc 2px cũ. Khi có xung đột về bo góc, áp dụng quyết định mới nhất ở mục này và prototype đã cập nhật; cần đồng bộ lại đặc tả chi tiết trước khi triển khai giao diện.

### 5.2. Danh mục màn hình

| Màn hình / lớp giao diện | Nội dung và hành động chính |
| --- | --- |
| Sổ tay môn học | Danh sách, tìm/sắp xếp, số tài liệu, tạo mới, đổi tên/xóa |
| Tạo sổ tay | Tên bắt buộc, mô tả tùy chọn, lỗi trường nhập và kết quả lưu |
| Tài liệu của tôi | Chọn môn, tải tệp, trạng thái xử lý, thử lại và xóa |
| Không gian học tập | Chọn nguồn, hỏi đáp, trạng thái sinh nội dung, tạo/mở phiên chat |
| Lịch sử hỏi AI | Tìm kiếm, lọc môn, nhóm theo thời gian, tiếp tục hội thoại |
| Popup xem nguồn | Đúng tài liệu, vị trí nguồn, highlight, điều hướng và đóng |
| Popup tài khoản | Hành động tài khoản theo cơ chế xác thực được duyệt |
| Dialog xác nhận | Xóa sổ tay, xóa tài liệu và các hành động mất dữ liệu |

Trạng thái rỗng/tải/lỗi là biến thể của màn hình. Đăng nhập và các trang tài khoản chi tiết chưa có thiết kế được chốt; xem quyết định phát hành ở mục 11.

### 5.3. Responsive và khả năng truy cập

- Desktop từ 1024px: bố cục học tập hai cột; sidebar có thể thu gọn.
- Màn hình nhỏ hơn: chuyển giữa Tài liệu và Hỏi đáp bằng tab/panel; PDF phủ màn hình khi cần.
- Bảng chỉ cuộn ngang trong vùng bảng; không đẩy toàn trang tràn ngang.
- Điều hướng được bằng bàn phím; icon có tên truy cập, trạng thái focus rõ ràng.
- Popup có quản lý focus, Escape để đóng và trả focus về nút mở.
- Không dùng màu làm tín hiệu trạng thái duy nhất. Tiến độ và lỗi luôn có chữ.

## 6. Yêu cầu chức năng và tiêu chí nghiệm thu

### P0-AUTH — Authentication và Authorization (bổ sung 18/11/2026)

Theo phân công module mới, Phú sở hữu nền tảng xác thực/phân quyền; từng chủ module chịu trách nhiệm
áp dụng quyền trên dữ liệu của mình. Đây là yêu cầu cần triển khai, không phải chức năng bootstrap đã có.

- Có đăng ký, đăng nhập, đăng xuất, lấy người dùng hiện tại và UI tương ứng.
- Mật khẩu được hash bằng thư viện phù hợp; phiên hết hạn/đăng xuất không tiếp tục truy cập được.
- Owner lấy từ danh tính đã xác thực ở server, không tin user_id client.
- Workspace, document, file, chat, history và retrieval không truy cập chéo tài khoản khi sửa ID/URL.
- UI route guard không thay thế kiểm tra quyền ở backend.
- Cơ chế phiên cụ thể phải thống nhất trước triển khai; nếu dùng cookie phải xử lý CSRF và thuộc tính bảo vệ theo môi trường.
- Đợt demo ưu tiên tài khoản cá nhân riêng tư; chưa làm chia sẻ nhóm/admin panel/RBAC nhiều cấp/OAuth/reset email.
- Test với tối thiểu hai tài khoản; mock hoặc identity override trong test không phải bằng chứng auth thật hoạt động.

### P0-WS — Sổ tay môn học

**Câu chuyện:** Là sinh viên, tôi muốn chia tài liệu theo môn để hỏi trong đúng phạm vi kiến thức.

- Tạo sổ tay với tên không rỗng sau khi loại khoảng trắng; mô tả không bắt buộc.
- Sổ tay vừa tạo xuất hiện trong danh sách và vẫn tồn tại sau khi tải lại trang.
- Tìm kiếm theo tên; sắp xếp theo tên hoặc cập nhật gần nhất.
- Đổi tên không làm mất tài liệu hoặc hội thoại.
- Xóa phải xác nhận rõ môn học và phạm vi dữ liệu bị xóa.
- Sau xóa thành công, workspace không thể truy cập hoặc tham gia tìm kiếm; file và chỉ mục liên quan được dọn theo tác vụ có theo dõi kết quả.

### P0-DOC — Tải và quản lý tài liệu

**Câu chuyện:** Tôi muốn biết tài liệu đã sẵn sàng để AI sử dụng hay chưa.

- Kiểm tra định dạng, khả năng đọc và giới hạn 50 MB ở máy chủ; không chỉ dựa vào phần mở rộng hoặc kiểm tra frontend.
- Tệp hỏng, mã hóa không đọc được, không có nội dung hoặc vượt giới hạn nhận lỗi dễ hiểu; không chuyển thành `ready` giả.
- Dùng SHA-256 phát hiện nội dung trùng trong cùng workspace; cùng tên khác nội dung không tự động coi là trùng.
- API tiếp nhận trả mã tài liệu/trạng thái sớm; xử lý nặng chạy ngầm.
- Trạng thái tối thiểu: `pending`, `processing`, `ready`, `failed`; trùng lặp là kết quả tiếp nhận riêng, không tạo bản sao chỉ mục.
- Có bước xử lý hiện tại; chỉ hiển thị phần trăm khi có cơ sở đo, nếu không dùng tiến độ không xác định.
- Chỉ `ready` được chọn để hỏi đáp. Lỗi có lý do và khả năng thử lại; thử lại không tạo vector trùng.
- Sau khi worker/dịch vụ khởi động lại, tác vụ phải được tiếp tục hoặc chuyển sang trạng thái có thể khôi phục; không treo `processing` vô hạn.
- Xóa tài liệu loại bỏ file gốc, văn bản/chunks và vector liên quan. Tác vụ đang chạy không được tái tạo dữ liệu sau khi xóa.

**Chính sách lịch sử đề xuất:** xóa tài liệu vẫn giữ nội dung hội thoại cũ của người dùng, nhưng gỡ snippet nguồn đã lưu và vô hiệu hóa liên kết tới tài liệu bị xóa. Dialog phải nói rõ điều này. Xóa workspace xóa cả hội thoại trong workspace.

### P0-RAG — Đọc và tìm kiếm tài liệu tiếng Việt

**Câu chuyện:** Tôi muốn tìm được cả câu diễn đạt tương đương và thuật ngữ chính xác trong giáo trình.

- Chuẩn hóa Unicode NFC; phát hiện và xử lý bảng mã cũ khi có bộ chuyển mã phù hợp, ghi rõ trường hợp không khôi phục được.
- OCR theo trang PDF thiếu text; không ghi đè vô điều kiện text layer đang sử dụng tốt.
- Giữ thông tin tiêu đề/chương, nguồn và vị trí của mỗi đoạn; ưu tiên ranh giới câu/đoạn khi chia nhỏ.
- Công thức/bảng không trích xuất đáng tin phải được đánh dấu hạn chế; không cam kết giữ hoàn hảo mọi cấu trúc.
- Tìm kiếm kết hợp ngữ nghĩa và từ khóa, lọc theo workspace và danh sách tài liệu hợp lệ ở phía máy chủ.
- Mọi đoạn dùng làm căn cứ thuộc tài liệu người dùng được quyền truy cập và đã chọn cho yêu cầu đó.
- Khi không tìm thấy căn cứ đủ liên quan, trả thông báo không đủ dữ liệu. Ngưỡng cần hiệu chỉnh trên tập đánh giá, không chọn theo một giá trị tùy ý trong PRD.

### P0-CHAT — Hỏi đáp bám sát nguồn

**Câu chuyện:** Tôi muốn đọc câu trả lời dần trong lúc chờ và biết phần nào có thể kiểm chứng.

- Khi không chọn nguồn, không gửi yêu cầu hỏi đáp; chỉ dẫn người dùng chọn hoặc tải tài liệu.
- Phạm vi tài liệu được chốt tại lúc gửi câu hỏi. Đổi checkbox sau đó chỉ ảnh hưởng câu hỏi tiếp theo.
- Máy chủ gửi trạng thái và danh sách nguồn trước các token nội dung; khi hoàn tất có định danh tin nhắn để lưu lại.
- Nhận định dựa trên nguồn có chỉ mục trích dẫn tương ứng với dữ liệu nguồn do máy chủ cấp; không chấp nhận mã nguồn do LLM tự tạo không khớp.
- Không có đủ căn cứ thì nêu rõ; không đính trích dẫn không liên quan để tạo vẻ đáng tin.
- Lỗi mạng, timeout hoặc hết hạn mức không xóa câu hỏi đã nhập hay trình bày câu trả lời dở như đã hoàn tất.
- Tin nhắn lưu trạng thái hoàn tất/gián đoạn/thất bại. Thử lại không tạo bản sao ngoài ý muốn; tránh gửi lại tự động toàn câu sau khi đã nhận một phần mà không báo người dùng.
- Nội dung tài liệu được coi là dữ liệu tham khảo; chỉ dẫn nhúng trong tài liệu không được phép đổi phạm vi truy cập hoặc ghi đè quy tắc hệ thống.

### P0-CITE — Kiểm chứng nguồn

- Nút nguồn hiển thị tên tài liệu và vị trí có thật.
- PDF: mở đúng file, đúng trang, highlight bbox hoặc đoạn phù hợp; phân biệt chỉ số trang file với số trang in trên giáo trình nếu khác nhau.
- DOCX/TXT: đề xuất mở đoạn trích văn bản chuẩn hóa kèm tiêu đề/định danh đoạn; không tạo số trang giả. Nếu chọn chuyển đổi sang PDF, cần chốt lại pipeline và cách tham chiếu trước khi làm.
- Khi không thể xác định bbox, vẫn mở đúng vị trí gần nhất và thông báo giới hạn highlight.
- Đóng popup giữ vị trí cuộn và nội dung hội thoại.
- Nguồn bị xóa, đổi phiên bản hoặc không còn quyền truy cập phải có thông báo rõ; kiểm tra quyền cả khi mở URL file trực tiếp.

### P0-HIST — Phiên và lịch sử hội thoại

- Mỗi phiên gắn với một workspace và có tên dễ nhận biết.
- Tạo phiên mới không xóa phiên trước; có thể tìm theo tiêu đề và lọc theo môn học.
- Mở lại khôi phục tin nhắn theo thứ tự cùng các trích dẫn còn hợp lệ.
- Đề xuất lưu danh sách nguồn đã dùng trên từng yêu cầu để có thể giải thích câu trả lời cũ.
- Phiên thuộc workspace đã bị xóa không xuất hiện trong lịch sử thông thường.

## 7. Dữ liệu, quyền truy cập và riêng tư

### 7.1. Đối tượng dữ liệu chính

| Đối tượng | Thông tin tối thiểu |
| --- | --- |
| Chủ sở hữu / người dùng | Định danh, tên hiển thị; danh tính phải được giải quyết ở máy chủ |
| Workspace | Chủ sở hữu, tên, mô tả, thời gian cập nhật |
| Document | Workspace, tên, loại, hash, vị trí lưu, phiên bản, trạng thái và lỗi |
| Processing job | Tài liệu/phiên bản, bước, số lần thử, thời điểm, kết quả |
| Chunk | Tài liệu/phiên bản, văn bản, chương/mục, vị trí trang/bbox hoặc đoạn |
| Chat session | Workspace, tiêu đề, thời gian |
| Message | Vai trò, nội dung, trạng thái, phạm vi nguồn, trích dẫn và thời gian |

### 7.2. Yêu cầu bắt buộc

- Kiểm tra quyền tại mọi API đọc/ghi, mở file, truy vấn vector và xem lịch sử. Không tin `workspace_id` hoặc `document_ids` từ client chỉ vì chúng tồn tại.
- Chỉ mục tìm kiếm và cache, nếu có, phải cô lập theo chủ sở hữu, workspace, tập nguồn và phiên bản; xóa/đổi tài liệu làm mất hiệu lực cache liên quan.
- API key nhà cung cấp chỉ ở máy chủ; không xuất hiện trong bundle frontend hoặc log gửi về client.
- Có giới hạn yêu cầu, giới hạn tác vụ nặng và kiểm soát dung lượng để tránh một người dùng chiếm toàn bộ tài nguyên.
- Thông báo cho người dùng nếu đoạn tài liệu/câu hỏi được gửi tới nhà cung cấp LLM bên ngoài; không mô tả dịch vụ là hoàn toàn cục bộ khi vẫn dùng API cloud.
- Log kỹ thuật ưu tiên định danh và mã lỗi; không mặc định ghi toàn văn tài liệu hoặc bí mật. Thời hạn giữ file, chat, log và bản sao lưu cần chốt trước phát hành.

## 8. Định hướng kỹ thuật và vận hành

Đây là định hướng kế thừa để lập kế hoạch; tên mô hình và các thư viện cụ thể cần được xác nhận bằng thử nghiệm và tài liệu hiện hành khi triển khai.

- Frontend: React, TypeScript, Vite; hệ component và theme dùng token từ thiết kế đã thống nhất.
- Backend: Python/FastAPI; REST cho quản lý dữ liệu, streaming cho chat.
- Lưu metadata/chat: PostgreSQL; SQLite có thể dùng cho phát triển cục bộ.
- Lưu file: kho file do máy chủ kiểm soát; lưu vector và metadata tìm kiếm trong Qdrant hoặc lựa chọn tương đương đã đánh giá.
- Xử lý tài liệu: pipeline trích xuất/OCR → chuẩn hóa → chia đoạn → lập chỉ mục; có tác vụ bền vững và cơ chế khôi phục.
- Embedding chạy CPU trong cấu hình đề xuất. OCR là tác vụ tốn tài nguyên riêng, cần giới hạn đồng thời.
- Nhà cung cấp LLM được cấu hình phía máy chủ; timeout/retry/fallback có giới hạn và tuân thủ hạn mức được cấp. Không dùng xoay key như cách bảo đảm vượt hạn mức.
- Theo dõi tỷ lệ xử lý lỗi, thời gian từng bước, lỗi streaming, token đầu, quota và chất lượng trích dẫn. P0 có thể dùng log/công cụ vận hành sẵn có, chưa cần trang admin.
- Có hướng dẫn cấu hình, sao lưu/khôi phục và chạy hệ thống tái lập được. Đo mức RAM thực tế trước khi chốt giới hạn; chưa cam kết backend toàn pipeline dưới 1,2 GB.

## 9. Các mốc bàn giao

| Mốc | Kết quả cần có để chuyển bước |
| --- | --- |
| M0 — Chốt phạm vi | Duyệt bản PRD, cách truy cập, cách hiển thị nguồn DOCX/TXT và giới hạn thử nghiệm |
| M1 — Quản lý nguồn | Workspace, lưu file/metadata, tác vụ xử lý, trạng thái/lỗi/thử lại và xóa thực sự hoạt động |
| M2 — Luồng hỏi đáp | Tìm nguồn đúng phạm vi, trả lời streaming, thiếu căn cứ và lưu hội thoại |
| M3 — Kiểm chứng và giao diện | Các màn hình P0 kết nối dữ liệu thật, popup nguồn, responsive và bàn phím |
| M4 — Pilot | Đánh giá chất lượng trên tập chuẩn, quan sát người dùng, kiểm tra quyền/xóa/khôi phục và sửa lỗi chặn |

Chưa ấn định ngày giao hoặc số tuần khi chưa có nguồn lực, baseline OCR/RAG và cách triển khai được thống nhất. Quiz, flashcard và n8n không chặn bàn giao P0.

## 10. Điều kiện hoàn thành P0

1. Luồng tạo môn → nạp tài liệu → hỏi → mở nguồn → xem lại hoạt động với file thật trên môi trường bàn giao.
2. Có đủ màn hình và các trạng thái theo mục 5; không còn dữ liệu hoặc nút mô phỏng trong luồng sản phẩm thật.
3. Tài liệu không hợp lệ, trùng, lỗi OCR, lỗi nhà cung cấp và ngắt streaming đều có kết quả rõ ràng và đường khôi phục phù hợp.
4. Quyền truy cập và bộ lọc phạm vi vượt qua các trường hợp kiểm tra, gồm URL file trực tiếp và ID bị sửa từ client.
5. Xóa dữ liệu, vô hiệu hóa nguồn cũ và khôi phục sau khi dịch vụ khởi động lại được kiểm chứng.
6. Có báo cáo chỉ số chất lượng/hiệu năng theo mục 3; các chỉ số chưa đạt được ghi nhận rõ cùng quyết định có chấp nhận pilot hay không.
7. Roboto, bố cục hai cột, popup PDF, sidebar và bo góc mềm đúng quyết định thiết kế mới nhất.
8. Các quyết định chặn phát hành ở mục 11 đã được giải quyết; có hướng dẫn vận hành và giới hạn sử dụng.

## 11. Các quyết định còn cần duyệt

| Vấn đề | Đề xuất trong bản thảo | Điều kiện quyết định |
| --- | --- | --- |
| Cách xác thực | Đợt triển khai mới có nhiều tài khoản với dữ liệu riêng tư; Phú làm auth, từng module áp dụng owner filtering | Chốt cơ chế phiên/CSRF tại M0; chỉ phát hành sau khi kiểm tra truy cập chéo tài khoản. Chưa mở chia sẻ nhóm |
| Nguồn DOCX/TXT | Popup đoạn văn chuẩn hóa có định danh; PDF giữ trang gốc | Chốt trước khi thiết kế API trích dẫn |
| Chống trả lời thiếu căn cứ | Hành vi bắt buộc P0; reranker nâng cao giữ P1 | Duyệt thay đổi so với cách phân loại trong PRD cũ |
| Ngân sách và nhà cung cấp | Ưu tiên cấu hình tiết kiệm, hạn mức rõ; chưa cam kết chi phí 0 đồng | Chốt trước tích hợp và thử tải |
| Quy mô thử nghiệm | Đề xuất tối đa 10 tài liệu/môn, 5 môn/người; OCR chạy tuần tự ở cấu hình máy nhỏ | Cần đo giới hạn trang, tác vụ đồng thời và kích thước ngữ cảnh trước khi duyệt |
| OCR, bảng và công thức | Ưu tiên PDF tiếng Việt có text và bản scan rõ; báo hạn chế với nội dung khó | Xác định tập tài liệu được hỗ trợ và tiêu chí chấp nhận |
| Tài liệu đã xóa và chat cũ | Giữ câu trả lời cũ, gỡ snippet/liên kết nguồn; xóa workspace xóa cả chat | Duyệt chính sách và thông báo xác nhận xóa |
| Dữ liệu lưu bao lâu? | Chưa áp thời hạn tự xóa khi chưa thống nhất | Chốt lưu trữ, sao lưu và quyền xóa trước pilot có dữ liệu thật |
| Các mục popup tài khoản | Chỉ bật đích có chức năng thật; chưa yêu cầu một bộ trang quản lý tài khoản đầy đủ | Phụ thuộc cách xác thực và phạm vi pilot |

## 12. Thay đổi chính so với PRD ban đầu

- Thu hẹp bản phát hành đầu vào luồng hỏi đáp có kiểm chứng; chuyển công cụ ôn tập và tự động hóa sang P1/P2.
- Thay workspace ba cột bằng hai cột 30%–70%, trình đọc PDF nằm trong popup.
- Ghi nhận Roboto và khôi phục bo góc mềm, bỏ giới hạn 2px.
- Bổ sung lịch sử hội thoại, phạm vi nguồn theo từng yêu cầu và trạng thái streaming gián đoạn.
- Làm rõ hành vi DOCX/TXT, dữ liệu sau xóa, khôi phục tác vụ và quyết định xác thực còn thiếu.
- Chuyển các tuyên bố tuyệt đối về chi phí, độ sẵn sàng và RAM thành mục tiêu cần đo, không coi là năng lực đã có.
