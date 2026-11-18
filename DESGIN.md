# EduRAG-VN — Đặc tả thiết kế giao diện P0

Tài liệu này ghi lại giao diện đã được chốt trong quá trình trao đổi, dùng làm chuẩn triển khai frontend và dựng các layer có thể chỉnh sửa trong Figma. Yêu cầu chức năng tham chiếu: [docs/PRD.md](docs/PRD.md).

Các kích thước, mã màu và khoảng cách dưới đây là quy ước triển khai được đề xuất để cụ thể hóa mockup. Các quyết định đã chốt gồm bố cục, sidebar, font **Roboto**, màu trắng–xanh tím và độ bo góc **không quá 2px**.

## 1. Phạm vi và nguyên tắc

- Thiết kế ưu tiên desktop/laptop, sử dụng tiếng Việt có dấu đầy đủ.
- Phong cách gọn, sáng, viền mảnh, biểu tượng nét mảnh và khoảng trắng rõ ràng.
- Mỗi màn hình có tiêu đề phù hợp với công việc người dùng đang làm.
- Dùng chung app shell, sidebar và thành phần giao diện giữa các màn hình.
- Không gian học tập chỉ có hai cột nội dung: nguồn tài liệu khoảng 30%, trợ lý AI khoảng 70%.
- PDF được mở trong popup khi người dùng nhấn nguồn trích dẫn.
- Sidebar tích hợp vào app shell, không dùng kiểu thanh nổi bo tròn lớn.
- Mọi container, nút, ô nhập, thẻ, badge, menu, popup và khung avatar đều có border-radius từ 0 đến 2px. Không dùng pill hoặc avatar có khung tròn.
- Đường tròn thuộc hình học của icon như kính lúp, đồng hồ, spinner không thuộc quy định bo góc container.

## 2. Hệ thống thị giác

### 2.1. Màu sắc

| Token | Giá trị | Sử dụng |
| --- | --- | --- |
| `background` | `#F8FAFC` | Nền ngoài vùng nội dung |
| `surface` | `#FFFFFF` | Sidebar, thẻ, form, popup |
| `surface-subtle` | `#F1F5F9` | Header bảng, vùng phụ |
| `text-primary` | `#0F172A` | Tiêu đề, nội dung chính |
| `text-secondary` | `#475569` | Mô tả, nội dung bổ sung |
| `text-muted` | `#64748B` | Ngày giờ, metadata, placeholder |
| `border` | `#E2E8F0` | Viền phân vùng, thẻ |
| `border-control` | `#CBD5E1` | Viền ô nhập và nút phụ |
| `primary` | `#5046E5` | Nút chính, link, trạng thái đang chọn |
| `primary-hover` | `#4338CA` | Hover nút chính |
| `primary-soft` | `#EEECFF` | Nền menu đang chọn, badge |
| `warning` | `#92400E` | Cảnh báo trùng tài liệu |
| `warning-soft` | `#FFFBEB` | Nền cảnh báo |
| `danger` | `#B91C1C` | Lỗi, xóa, đăng xuất |
| `danger-soft` | `#FEF2F2` | Nền lỗi |
| `citation-highlight` | `#FFF3A3` | Đoạn trích được tô sáng trong PDF |

Không dùng màu sắc làm dấu hiệu duy nhất: trạng thái luôn có chữ và có thể kèm icon. Trạng thái tài liệu sẵn sàng dùng checkmark, chữ và nền xanh tím nhạt như mockup.

### 2.2. Typography — Roboto

Nạp font Roboto thật, có hỗ trợ tiếng Việt. Không dùng ảnh chữ hoặc font thay thế để nghiệm thu typography. Ưu tiên self-host bộ font có giấy phép phù hợp, gồm đầy đủ glyph tiếng Việt và các weight sử dụng.

| Vai trò | Cỡ chữ / line-height | Weight | Ví dụ |
| --- | --- | --- | --- |
| `h1` | 24px / 32px | 600 | Sổ tay môn học, Tài liệu của tôi |
| `h2` | 18px / 26px | 500 | Nguồn tài liệu, Trợ lý AI |
| `h3` | 16px / 24px | 500 | Tên môn học, tiêu đề hội thoại |
| `p`, nội dung chat | 14px / 22px | 400 | Mô tả môn học, câu trả lời |
| Nhãn form | 14px / 20px | 500 | Tên môn học |
| Sidebar, nút, input | 14px / 20px | 400–500 | Menu, hành động, giá trị nhập |
| Metadata, badge, caption | 12px / 18px | 400 | Ngày cập nhật, dung lượng, trạng thái |
| Nhãn nhóm sidebar | 11px / 16px | 500 | HỌC TẬP |
| Tên sản phẩm | 18px / 24px | 600 | EduRAG-VN |

- Mỗi màn hình dùng một `h1`. `h2` chia khu vực; `h3` đặt tên thẻ khi phù hợp với cấu trúc nội dung.
- `span` dùng cho nội dung ngắn trong dòng như metadata hoặc badge; chọn kiểu chữ theo vai trò, không áp một kiểu chung cho mọi `span`.
- Không dùng toàn bộ nội dung đậm. Tiêu đề nổi bật bằng cỡ chữ và weight; thông tin phụ nhẹ hơn bằng màu và kích thước.
- Không dùng chiều cao cố định làm cắt dấu tiếng Việt. Nội dung dài được xuống dòng; tên tệp có thể ellipsis và xem đủ qua tooltip.

### 2.3. Khoảng cách, viền và icon

- Thang khoảng cách: `4, 8, 12, 16, 24, 32, 48px`.
- Padding nội dung trang: 24px; khoảng cách giữa các khu vực chính: 24px.
- Padding thẻ: 16px; khoảng cách giữa thẻ: 12–16px.
- Viền tiêu chuẩn: 1px. Bo góc mặc định: 2px; khung lớn có thể dùng 0px.
- Control thông thường cao 36–40px; icon button có vùng nhấn tối thiểu 36 × 36px trên desktop.
- Icon menu 18–20px; icon trong nút 16px, cùng một thư viện nét mảnh.
- Popup có bóng nhẹ để thể hiện lớp nổi; thẻ thông thường ưu tiên viền, không cần bóng đậm.

## 3. App shell và sidebar

### 3.1. Bố cục chung

Sidebar nằm bên trái toàn chiều cao ứng dụng. Vùng bên phải gồm header và nội dung màn hình. Header có thể chứa thông tin cập nhật nếu có dữ liệu thực; không hiển thị ngày giả cố định từ mockup.

Kích thước triển khai đề xuất: sidebar mở rộng 232px, thu gọn 64px. Tỷ lệ 30%–70% của màn hình học tập được tính **sau khi trừ sidebar và khoảng cách nội dung**.

### 3.2. Sidebar mở rộng

Thứ tự từ trên xuống:

1. Logo sách và tên **EduRAG-VN**, nút thu gọn.
2. Ô tìm kiếm ngắn với placeholder “Tìm kiếm…”.
3. Nhãn nhóm “HỌC TẬP”.
4. Sổ tay môn học.
5. Tài liệu của tôi.
6. Google Drive.
7. Lịch sử hỏi AI.
8. Khoảng trống linh hoạt.
9. Tài khoản: avatar vuông, tên, dòng phụ “Sinh viên”, nút “…”.

Không có nút chuyển “Cá nhân / Nhóm học”. Không đặt Thông báo, Cài đặt, Trợ giúp thành các hàng thường trực trong sidebar. Hàng đang chọn có nền xanh tím nhạt, chữ và icon xanh tím.

Ô tìm kiếm và các mục chưa có chức năng trong P0 phải có hành vi được xác định trước khi triển khai. Google Drive là tính năng P1 theo PRD; nếu chưa làm, hiển thị rõ trạng thái “Sắp có”, không tạo đích điều hướng rỗng hoặc nút giả kết nối thành công.

### 3.3. Sidebar thu gọn

Hiển thị logo, nút mở rộng, tìm kiếm, bốn icon điều hướng và avatar phía dưới. Icon có tooltip và tên truy cập bằng bàn phím. Nhấn avatar mở cùng popup tài khoản.

### 3.4. Popup tài khoản

Nhấn “…” mở menu nổi neo cạnh hoặc phía trên tài khoản, nằm trọn trong viewport. Menu không đẩy nội dung và không làm tối toàn trang.

Nội dung:

- Tên và email tài khoản.
- Hồ sơ tài khoản.
- Thông báo, kèm số lượng khi có dữ liệu.
- Cài đặt.
- Trợ giúp.
- Đường phân cách.
- Đăng xuất, màu đỏ.

Đóng bằng Escape, nhấn ra ngoài hoặc chọn mục. Trả focus về nút mở sau khi đóng. Các mục tài khoản là thiết kế điều hướng đã thống nhất; PRD chưa đặc tả đầy đủ các trang đích và cơ chế đăng nhập, cần xác định riêng trước khi triển khai phần đó.

## 4. Các màn hình P0

### 4.1. Danh sách sổ tay môn học

- Tiêu đề: “Sổ tay môn học”. Sidebar chọn mục tương ứng.
- Thanh công cụ: tìm kiếm môn học, sắp xếp, nút chính “+ Tạo sổ tay”.
- Danh sách thẻ dạng hàng như bản chốt, gồm icon sách, tên môn, mô tả, số tài liệu, số tài liệu đã xử lý và lần cập nhật.
- Menu “…” trên từng thẻ: đổi tên, xóa. Menu này tách biệt với menu tài khoản.
- Nhấn thẻ mở không gian học tập của môn.
- Không hiển thị phần trăm tiến độ học nếu chưa có dữ liệu đo việc học. Số lượng đã xử lý là tiến độ tài liệu.
- Khi chưa có sổ tay: lời hướng dẫn ngắn và nút “Tạo sổ tay đầu tiên”.

### 4.2. Tạo sổ tay môn học

- Tiêu đề: “Tạo sổ tay môn học”, có nút quay lại.
- Tên môn học bắt buộc; mô tả tùy chọn theo dữ liệu workspace trong PRD.
- Trường thư mục Google Drive tùy chọn, phục vụ mở rộng P1; không cản việc tạo sổ tay.
- Hành động cuối form: “Hủy”, “Tạo sổ tay”.
- Hiển thị lỗi ngay dưới trường; giữ dữ liệu đã nhập khi thao tác thất bại.
- Nút gửi có trạng thái đang lưu và ngăn gửi trùng.

### 4.3. Tài liệu của tôi — tải lên và xử lý

- Tiêu đề: “Tài liệu của tôi”; bộ chọn môn học ở đầu nội dung.
- Dropzone: “Kéo thả tài liệu vào đây hoặc chọn tệp”.
- Chỉ hỗ trợ **PDF, DOCX, TXT; tối đa 50MB/tệp** theo PRD. Những mockup cũ có PPTX hoặc 100MB không phải yêu cầu triển khai.
- Bảng tài liệu gồm tên, dung lượng, trạng thái xử lý và menu hành động.
- Các bước hiển thị: chờ xử lý → đọc tài liệu/OCR khi cần → chuẩn hóa tiếng Việt → tạo vector → sẵn sàng.
- Hiển thị phần trăm hoặc trang X/Y khi backend cung cấp; không tạo tiến độ giả.
- Trùng tệp: cảnh báo rõ, tránh lập chỉ mục lại theo cơ chế hash trong PRD.
- Thất bại: thông báo dễ hiểu, hành động thử lại khi API hỗ trợ.
- Xóa tài liệu có xác nhận tên tệp và thông báo kết quả; backend chịu trách nhiệm xóa dữ liệu liên quan.

### 4.4. Không gian học tập môn học

Header nội dung có tên môn và các hành động liên quan. Phần chính chỉ có hai cột:

| Cột | Tỷ lệ | Nội dung |
| --- | --- | --- |
| Nguồn tài liệu | Khoảng 30% | Tải tài liệu, tìm tệp, chọn tất cả, checkbox từng tệp, trạng thái và số nguồn đang dùng |
| Trợ lý AI | Khoảng 70% | Lịch sử hội thoại, hội thoại mới, tin nhắn, nguồn trích dẫn và ô đặt câu hỏi |

- Chỉ tài liệu sẵn sàng mới tham gia phạm vi hỏi đáp; tài liệu đang xử lý có trạng thái rõ ràng.
- Số nguồn đang dùng phải khớp với số checkbox đã chọn.
- Giữ ô nhập câu hỏi dễ tiếp cận khi nội dung chat dài, cho phép vùng hội thoại cuộn.
- Trạng thái gửi câu hỏi: “Đang tìm trong N tài liệu…” → tìm thấy đoạn trích → đang viết câu trả lời.
- Câu trả lời streaming, có nhãn trích dẫn `[1]`, `[2]` và nút nguồn gồm tên tài liệu, số trang.
- Khi không có thông tin phù hợp, thông báo rõ thay vì tạo câu trả lời giả.
- Nếu chưa có tài liệu hoặc chưa chọn nguồn, hiển thị hướng dẫn và hành động phù hợp.
- Chế độ Bám sát/Gia sư và Like/Dislike đã xuất hiện trong mockup nhưng thuộc P1 theo PRD. P0 ưu tiên Bám sát; chỉ bật các điều khiển mở rộng khi có chức năng thật.

### 4.5. Popup xem nguồn PDF

- Nhấn nguồn mở popup nổi trên màn hình học tập, nền phía sau được làm tối nhẹ.
- Header: tên tệp, nút đóng.
- Toolbar: trang hiện tại/tổng trang, trang trước/sau, mức zoom; tải xuống nếu endpoint hỗ trợ.
- Tự mở đúng tài liệu và trang nguồn, tô sáng đoạn theo bbox/snippet.
- Popup desktop rộng khoảng 72–80% viewport, cao tối đa 90vh; nội dung PDF cuộn bên trong.
- Bo góc tối đa 2px, kể cả toolbar và các nút.
- Escape hoặc nút đóng trả về hội thoại và giữ vị trí đọc; khóa focus trong dialog khi mở, trả focus về nguồn trích dẫn khi đóng.
- Tài liệu không còn tồn tại hoặc không tải được phải có trạng thái lỗi rõ ràng.
- Với DOCX/TXT, PRD chưa xác định cách hiển thị nguồn có số trang. Cần thống nhất backend/viewer; không tự hiển thị số trang PDF hoặc bbox không tồn tại.

### 4.6. Lịch sử hỏi AI

- Tiêu đề: “Lịch sử hỏi AI”.
- Thanh công cụ: tìm hội thoại, lọc môn học, “+ Hội thoại mới”.
- Nhóm theo “Hôm nay”, “Hôm qua” và các khoảng thời gian phù hợp.
- Mỗi hàng gồm tiêu đề hội thoại, môn học, thời gian và đoạn xem trước.
- Nhấn hàng mở đúng workspace và phiên chat, khôi phục tin nhắn và nguồn trích dẫn đã lưu.
- Hội thoại mới cần gắn với workspace; nếu chưa có ngữ cảnh, cho chọn môn học.
- Trạng thái rỗng có hướng dẫn bắt đầu hội thoại từ một môn học.

## 5. Thành phần và trạng thái dùng chung

| Thành phần | Trạng thái cần thiết |
| --- | --- |
| Button | Mặc định, hover, focus-visible, pressed, disabled, loading |
| Input / textarea | Rỗng, có giá trị, focus, disabled, lỗi và hướng dẫn |
| Sidebar item | Mặc định, hover, selected, focus-visible |
| Document row | Chờ, xử lý, sẵn sàng, trùng lặp, thất bại |
| Checkbox | Chưa chọn, đã chọn, chọn một phần, disabled |
| Account menu | Đóng, mở, mục đang focus |
| Citation button | Mặc định, hover, focus, nguồn không khả dụng |
| Chat | Rỗng, tìm nguồn, streaming, hoàn tất, không có thông tin, lỗi kết nối |
| Data list | Đang tải, có dữ liệu, không có dữ liệu, lọc không có kết quả, lỗi |
| PDF dialog | Đang tải, hiển thị, tải lỗi, nguồn không còn tồn tại |

Các trạng thái rỗng, tải và lỗi là biến thể của màn hình, không cần tạo trang điều hướng riêng. Xóa workspace/tài liệu cần dialog xác nhận có mô tả phạm vi xóa và nút hủy rõ ràng.

## 6. Responsive và khả năng truy cập

- Desktop từ 1024px: ưu tiên bố cục hai cột học tập; cho phép thu gọn sidebar khi thiếu không gian.
- Dưới 1024px: nguồn tài liệu và hỏi đáp chuyển thành tab hoặc panel có thể mở/đóng; tránh ép hai cột hẹp. PDF vẫn mở dưới dạng dialog hoặc view phủ màn hình phù hợp kích thước.
- Trên màn hình nhỏ, sidebar là drawer. Vùng nhấn ưu tiên tối thiểu 44 × 44px.
- Bảng dài cho phép cuộn ngang trong vùng bảng; không làm toàn trang tràn ngang.
- Điều hướng được bằng bàn phím, focus-visible rõ ràng; icon button có accessible name.
- Dùng semantic HTML: `nav`, `main`, `header`, `button`, `label`, `table`, dialog/menu theo hành vi thực tế.
- Nhãn form liên kết với control; lỗi liên kết bằng `aria-describedby`.
- Thông báo tiến độ có thể dùng live region, tránh đọc lại từng token chat hoặc từng phần trăm liên tục.
- Bảo đảm tương phản chữ thường ít nhất 4.5:1 và chữ lớn 3:1; kiểm tra trực tiếp với màu sử dụng thực tế.

## 7. Token CSS tham khảo

```css
:root {
  --font-sans: 'Roboto', Arial, sans-serif;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-text: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #64748b;
  --color-border: #e2e8f0;
  --color-primary: #5046e5;
  --color-primary-hover: #4338ca;
  --color-primary-soft: #eeecff;
  --radius-control: 2px;
  --radius-card: 2px;
  --radius-dialog: 2px;
  --radius-avatar: 2px;
  --sidebar-width: 232px;
  --sidebar-width-collapsed: 64px;
}

body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 22px;
  color: var(--color-text);
  background: var(--color-bg);
}

button, input, textarea, select { font: inherit; }
h1 { font-size: 24px; line-height: 32px; font-weight: 600; }
h2 { font-size: 18px; line-height: 26px; font-weight: 500; }
h3 { font-size: 16px; line-height: 24px; font-weight: 500; }
p { font-size: 14px; line-height: 22px; font-weight: 400; }
.metadata { font-size: 12px; line-height: 18px; color: var(--color-text-muted); }
```

Ánh xạ các token vào theme và component của ứng dụng; không dùng reset `border-radius` bằng selector toàn cục làm hỏng icon hoặc thành phần bên ngoài. Kiểm tra từng component để bảo đảm không còn utility tạo pill, vòng tròn hoặc góc bo vượt 2px.

## 8. Chuẩn bàn giao và nghiệm thu giao diện

- Có đủ danh sách sổ tay, tạo sổ tay, quản lý tài liệu, lịch sử hội thoại và không gian học tập.
- Sidebar đồng nhất, có dạng mở rộng/thu gọn và popup tài khoản.
- Font thực tế trên các control và nội dung là Roboto, hiển thị dấu tiếng Việt đầy đủ.
- Phân cấp typography theo bảng; nội dung không bị cắt dấu, tràn hoặc chồng lên nhau.
- Mọi container và control bo góc không quá 2px.
- Màn hình học tập dùng hai cột 30%–70%, PDF xuất hiện trong popup từ nút nguồn.
- Có đầy đủ trạng thái rỗng, đang tải, lỗi và khôi phục tương ứng.
- Dữ liệu, tiến độ, ngày giờ và số nguồn hiển thị nhất quán, không dùng số giả từ mockup khi chạy thật.
- Nếu dựng Figma, bàn giao frame có text, vector và component chỉnh sửa được; dùng Roboto thật, không đặt ảnh toàn màn hình làm thiết kế thay thế.
- Tài liệu này ghi nhận thiết kế; chưa xác nhận đã có frontend, file Figma hoặc các bước kiểm tra giao diện hoàn tất.
