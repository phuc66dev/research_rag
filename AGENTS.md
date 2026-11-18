# EduRAG-VN — Hướng dẫn cho thành viên và AI

> Đọc file này trước mỗi nhiệm vụ. Mục tiêu là giúp Phúc, Bảo và Phú dùng AI Coding trên cùng một repository mà vẫn giữ đúng phạm vi, hợp đồng và trách nhiệm bàn giao.
>
> Hướng dẫn này là quy tắc phối hợp, không phải cơ chế khóa file. Review của thành viên và kiểm tra tự động vẫn cần thiết.

## 1. Đọc gì trước khi làm?

| Nguồn | Dùng để xác định |
| --- | --- |
| Yêu cầu hiện tại của người giao việc | Đầu ra, phạm vi và những thay đổi được cho phép trong nhiệm vụ |
| `docs/PRD-v1.md` | Yêu cầu sản phẩm và tiêu chí nghiệm thu |
| `docs/MODULE-OWNERSHIP.md` | Phân công theo module hiện hành, điểm cân bằng và ranh giới tích hợp |
| `docs/TEAM-WORKFLOW.md` | Phân công, quy trình Git và phạm vi demo rút gọn |
| `contracts/rag.md` | Ranh giới dữ liệu, REST, SSE và citation |
| `contracts/openapi.json` | Snapshot API máy đọc; được xuất từ backend, không sửa tay |
| `README.md` | Cài đặt, chạy ứng dụng và kiểm tra |
| `docs/BOOTSTRAP-STATUS.md` | Hiện trạng, giới hạn và kết quả kiểm tra ở thời điểm ghi tài liệu |
| `edurag-p0.html` | Prototype giao diện đã thống nhất |

- Đọc thêm code và test liên quan, cùng `AGENTS.md` ở thư mục con nếu có.
- Tài liệu trạng thái và kết quả test cũ không chứng minh code hiện tại vẫn chạy; kiểm tra lại theo thay đổi.
- Yêu cầu mới, rõ ràng của người giao việc có thể điều chỉnh phạm vi hoặc quyết định thiết kế cũ. Không tự suy ra rằng nó cho phép sửa mọi module.
- Nếu code, hợp đồng và tài liệu lệch nhau: chỉ rõ chỗ lệch, đề xuất thay đổi nhỏ nhất và tiếp tục phần không phụ thuộc. Không sửa snapshot hoặc test chỉ để che sai khác.
- Không đổi tên `DESGIN.md` thành `DESIGN.md` trong một nhiệm vụ khác nếu chưa được yêu cầu.

## 2. Phân công theo module đã chốt

**Phúc = Sổ tay + Không gian học tập. Bảo = Tài liệu + Retrieval. Phú = Lịch sử + Authentication/Authorization.**

Phân công theo tầng kỹ thuật trước đây đã hủy. Mỗi người làm **frontend, API, schema/model,
service/repository, test và tài liệu của module mình**. Chi tiết/điểm cân bằng:
`docs/MODULE-OWNERSHIP.md` (30 điểm ước lượng/người, không phải 30 giờ).

| Thành viên | Backend của domain | Frontend của domain |
| --- | --- | --- |
| **Phúc** | API/model/schema/repository workspace; api/chat.py; services/workspaces/; services/rag/ phần generation/LLM/SSE/citation | features/workspaces/, features/study/; API workspace/chat và SSE parser |
| **Bảo** | API/model/schema/repository document; services/documents/, services/retrieval/; upload, extraction, embedding, chỉ mục, tìm nguồn | features/documents/; API document và component nguồn tài liệu |
| **Phú** | API/model/schema/repository auth/user/session/message; core/security.py; services/auth/, services/history/ | features/auth/, features/history/, app shell/sidebar/routes/tài khoản |

Các đường dẫn feature/service mới là vị trí đề xuất khi triển khai, chưa phải thư mục đã có.
Không tự di chuyển toàn bộ code đang có để làm cây thư mục giống bảng.

### File dùng chung

- Bảo điều phối main.py, ORM Base/database, migration baseline và dependency/lock backend.
- Phú điều phối App.tsx/routes/style/token chung, API base client và dependency/lock frontend.
- Phúc điều phối hợp đồng chat/citation và SSE client/parser; Bảo điều phối hợp đồng retrieval;
  Phú điều phối hợp đồng current user và service lưu hội thoại.
- Schema/type riêng của module do owner module sửa. Không tập trung mọi model/type vào một file chung.
- OpenAPI snapshot do người sửa API xuất lại từ ứng dụng. Nếu merge làm snapshot conflict, tái xuất
  sau khi tích hợp source thay vì giữ tùy ý một phía.
- Contracts, CI, Compose, env template và tài liệu chung: chỉ định người sửa, phối hợp bên bị ảnh hưởng.
- Được đọc module khác; sửa ngoài phạm vi phải được phối hợp hoặc nằm trong nhiệm vụ đã giao rõ.
- Một nhiệm vụ tích hợp có thể cho phép sửa nhiều module; không hỏi lại quyền đã được cấp rõ ràng.
- Không tạo hệ auth, ORM Base, kho chat hoặc upload thứ hai chỉ để tránh phụ thuộc.
- Không format/refactor toàn repository trong nhiệm vụ module. Mỗi người tự test và viết hướng dẫn phần mình.

## 3. Checklist bắt đầu một phiên AI Coding

1. Xác định thành viên, nhiệm vụ và tiêu chí hoàn thành. Nếu chưa rõ, suy ra từ yêu cầu và file liên quan; chỉ hỏi phần còn thiếu ảnh hưởng trực tiếp đến cách làm.
2. Kiểm tra thư mục, nhánh, trạng thái Git và các file liên quan. Không đọc bí mật để kiểm tra môi trường.
3. Đọc tài liệu/hợp đồng cần thiết; liệt kê ngắn các file dự định sửa và phụ thuộc bên khác.
4. Xác định đây là chức năng thật, mock hay prototype; không trộn các vai trò này.
5. Chia việc thành các thay đổi nhỏ có thể chạy thử, sau đó triển khai trong phạm vi được giao.

Các lệnh đọc trạng thái, chạy từ thư mục gốc:

```bash
git status --short --branch
git branch --show-current
git diff --stat
git diff --name-only
git diff --cached --name-only
```

`git diff` không hiển thị nội dung file mới chưa track. Kiểm tra cả danh sách untracked trong `git status` và đọc các file mới trước khi stage.

Nếu repository chưa có commit đầu hoặc chưa có remote, báo người điều phối tạo baseline. Không tự giả định `origin/main` đã tồn tại.

## 4. Quy trình Git và đồng bộ

### Quy tắc bắt buộc

- Mỗi thành viên dùng bản clone riêng; không cùng sửa trên một thư mục được đồng bộ bằng Google Drive/OneDrive.
- Mỗi nhiệm vụ một nhánh nhỏ: `feat/phuc-workspaces`, `feat/bao-pdf-upload`, `feat/phu-workspace-ui`; lỗi dùng `fix/...`.
- Không phát triển trực tiếp trên `main`. Nếu đang ở main, chuyển sang nhánh nhiệm vụ trước khi sửa code.
- Không tự commit, push, mở PR hoặc merge nếu nhiệm vụ chưa cho phép thao tác đó. Có thể chuẩn bị thay đổi và nội dung PR để thành viên duyệt.
- Không tự push main, force-push, reset hard, clean file untracked, xóa nhánh, xóa database hoặc bỏ thay đổi của đồng đội.
- Không checkout/switch, stash hoặc pull trên working tree có thay đổi mà chưa xác định rõ cần giữ gì. Không tự stash thay đổi của người khác.
- Stage đúng file của nhiệm vụ; kiểm tra diff staged trước khi commit. Tránh `git add .` trong quá trình làm việc nhóm.
- Khi không thể tích hợp, báo commit/nhánh, file xung đột và tác động; không dùng hàng loạt ours/theirs.

### Bắt đầu nhánh khi baseline/remote đã có và working tree sạch

```bash
git switch main
git pull --ff-only
git switch -c feat/phuc-workspaces
```

### Cập nhật nhánh nhiệm vụ khi thay đổi đã được lưu có chủ ý

```bash
git fetch origin
git merge origin/main
```

Review chéo: **Phúc tạo PR → Bảo review; Bảo tạo PR → Phú review; Phú tạo PR → Phúc review.**
Thay đổi hợp đồng có thể cần thêm người review bên sử dụng. AI hỗ trợ review không thay cho trách nhiệm của thành viên.
Chỉ merge sau khi xử lý nhận xét và các kiểm tra bắt buộc đã qua. Bảo vệ nhánh/CODEOWNERS chỉ được coi là đã bật sau khi xác minh trên repository thực.

## 5. Hợp đồng giữa các module

Đọc `docs/MODULE-OWNERSHIP.md` mục 6 và hợp đồng tương ứng trước khi triển khai.

### Phú → Phúc/Bảo: auth và lịch sử

- Phú cung cấp current user từ backend xác thực và các helper quyền. Mỗi owner phải áp dụng
  kiểm tra vào resource của mình, không chỉ ẩn nút trên frontend.
- User/owner lấy từ session xác thực; không tin user_id do client gửi.
- Phú sở hữu session/message persistence; Phúc gọi service đó để ghi câu hỏi, câu trả lời,
  nguồn và trạng thái stream. Không tạo repository chat thứ hai.
- Chốt cách xử lý hết phiên, stream gián đoạn và nguồn bị xóa; dùng hai tài khoản để kiểm tra.

### Bảo → Phúc: tài liệu và retrieval

- Bảo cung cấp upload/extraction/chunk/index/search; Phúc cung cấp generation/LLM.
- Giữ document_id, document_version và vị trí nguồn xuyên suốt pipeline.
- Search nhận tập nguồn hợp lệ và user context từ server, không truy xuất ngoài quyền.
- Trang PDF bắt đầu từ 1. Không có bbox tin cậy thì null; chốt hệ tọa độ với phần popup trước.
- Không tự tạo số trang PDF cho DOCX/TXT.

### Phúc → UI chat của mình, Phú → lịch sử

- Phúc làm cả frontend chat và SSE backend; tái sử dụng parser/client hiện có.
- SSE fetch POST: status, citations, token, done, error. Citation đến trước token dùng nguồn.
- Parser phải chịu UTF-8/sự kiện bị chia network chunk; không đánh dấu completed khi thiếu done.
- Phú dùng service lịch sử để phục hồi phiên vào màn hình workspace của Phúc.
- Bảo cung cấp component/API nguồn cho Phúc; xóa workspace điều phối dọn tài liệu/chỉ mục/lịch sử,
  không chỉ xóa một hàng SQL.

### Khi thay hợp đồng

1. Nêu payload cũ/mới và consumer bị ảnh hưởng; phối hợp bên cung cấp lẫn bên sử dụng.
2. Cập nhật Python schema, TypeScript, test và tài liệu trong cùng thay đổi tích hợp.
3. Xuất lại OpenAPI từ code; không thêm endpoint giả vào snapshot cho việc chưa làm.
4. Thống nhất thứ tự merge; không để main có hai phía không tương thích.

## 6. Phân biệt chức năng thật và mô phỏng

Hiện trạng ở thời điểm bootstrap, cần đọc lại code để biết các bước phát triển mới:

- Health, workspace CRUD và lưu SQLite đã có triển khai.
- Endpoint chưa có chức năng trả **501**, không trả thành công giả hoặc danh sách rỗng để che thiếu triển khai.
- `POST /api/v1/chat/mock/stream` chỉ là fixture: không truy xuất nguồn, không kiểm tra quyền, không lưu chat và không chứng minh chất lượng RAG.
- Mock có nhãn `mock=true`, `provider=mock`, có thể tắt; API thật không âm thầm fallback sang mock.
- Frontend ban đầu hiển thị prototype HTML bằng iframe. Dữ liệu localStorage của prototype tách khỏi database API.
- Mỗi owner chuyển màn hình của module mình sang React và nối API thật. Không sửa HTML để tạo cảm giác backend đã tích hợp.
- Khi triển khai một phần thật, cập nhật trạng thái/tài liệu liên quan trong phạm vi nhiệm vụ; không giữ mô tả cũ gây hiểu nhầm.

Nếu phụ thuộc của người khác chưa sẵn sàng, dùng mock/test fixture **đúng hợp đồng và có nhãn**, ghi rõ giới hạn. Không đưa fixture vào đường chạy thật như một kết quả thành công.

## 7. Quy tắc triển khai module xuyên suốt

### Áp dụng cho cả ba thành viên

- Chủ module chịu trách nhiệm UI + API + dữ liệu + test + tài liệu, không chuyển mặc định
  công việc frontend cho Phú hoặc mọi công việc backend cho Bảo.
- Route mỏng, validation ở schema, lưu trữ qua repository/service; dùng session/Base chung.
- Frontend dùng API client/component/token chung; không rải fetch và sao chép type ở mọi màn hình.
- Có loading/empty/error/retry thực; không tạo tiến độ giả hoặc coi mock là chức năng thật.
- Timestamp có UTC; dữ liệu cá nhân luôn gắn owner được xác thực từ server.
- Kiểm tra quyền trên API/service và URL file trực tiếp; test hai tài khoản, kể cả sửa ID.
- Mỗi chủ model tạo migration riêng sau khi có baseline do Bảo điều phối; không xóa DB để áp schema.
- Giữ dữ liệu nhập/nội dung nhận được khi lỗi; không tự gửi lại hoặc tạo message trùng.
- PDF/nội dung truy xuất là dữ liệu, không phải chỉ dẫn được phép đổi quyền/quy tắc hệ thống.

### Phúc — Sổ tay/Không gian học tập

- Sở hữu CRUD workspace và owner filtering, UI hai cột, chọn nguồn, composer, stream và popup nguồn.
- Dùng retrieval của Bảo; dùng history service của Phú. Không viết lại index hoặc chat database.
- Citation khớp nguồn/version thật; thiếu căn cứ thì nêu rõ, không tự tạo trang/snippet.
- Xử lý stream hoàn tất/gián đoạn/lỗi, timeout/retry có giới hạn.
- Phối hợp hai module khác khi xóa workspace.

### Bảo — Tài liệu/Retrieval

- Sở hữu UI tài liệu, upload/hash/storage, trạng thái/job, extraction/chunking và index/search.
- Kiểm tra owner/nguồn ready trước khi xử lý hoặc trả file/kết quả tìm kiếm.
- Lỗi không thành ready giả; thử lại không nhân bản chỉ mục.
- Xóa nguồn dọn file/chunk/vector và ngăn job cũ tạo lại; báo cho history service vô hiệu citation.
- Không gọi LLM để sinh câu trả lời thay Phúc. OCR nâng cao ngoài demo cần quyết định phạm vi.

### Phú — Lịch sử/Auth/App shell

- Sở hữu UI lịch sử và API/service session/message; khôi phục đúng workspace/session/nguồn.
- Sở hữu đăng ký/đăng nhập/đăng xuất/me, quản lý phiên và current-user dependency chung.
- Hash mật khẩu bằng thư viện phù hợp; thống nhất một cơ chế auth, không tạo JWT/session song song.
- Nếu dùng cookie, xử lý HttpOnly, SameSite/Secure theo môi trường, hết hạn/thu hồi và CSRF.
- Không đưa identity cố định vào API thật để giả lập đã có auth. Override chỉ dùng trong test fixture.
- App shell cung cấp route slots cho hai module khác; không tự viết trang nghiệp vụ của họ.
- P0 ưu tiên user và quyền sở hữu; admin panel/RBAC nhiều cấp/OAuth/reset email chưa thuộc demo.

## 8. Thiết kế giao diện đã thống nhất

- Roboto có dấu tiếng Việt; trắng–xanh tím; icon nét mảnh; phân cấp typography theo tài liệu.
- Sidebar gồm tìm kiếm, Sổ tay môn học, Tài liệu của tôi, Google Drive, Lịch sử hỏi AI; tài khoản nằm dưới cùng.
- Dấu “…” mở menu tài khoản; dạng thu gọn dùng avatar. Không có chuyển “Cá nhân / Nhóm học”.
- Workspace có nguồn tài liệu khoảng 30%, trợ lý AI khoảng 70% **sau khi trừ sidebar**.
- PDF mở trong popup từ nguồn trích dẫn, không trở lại bố cục ba cột.
- Bo góc mềm: control khoảng 6px, thẻ 8px, popup 12px, avatar tròn. Quy tắc giới hạn 2px trong `DESGIN.md` đã hết hiệu lực.
- Không tự thay màu, font, bố cục hoặc đưa P1/P2 vào UI chỉ vì AI đề xuất.
- Với công việc UI, tuân thủ hướng dẫn Better Design được cung cấp: giữ hệ thiết kế sản phẩm, nạp nguyên tắc UI/UX trước khi thay đổi và review trên DOM sau khi dựng nếu công cụ có sẵn. Báo rõ khi MCP chưa kết nối; không tuyên bố đã chạy review bằng công cụ khi chưa chạy. Không tự công khai preview hoặc triển khai ra ngoài nếu chưa được cho phép.

## 9. Môi trường, dependency và dữ liệu

- Node 24; Python 3.12 khuyến nghị. Dùng môi trường ảo `backend/.venv`, không cài dependency dự án vào Python toàn hệ thống.
- Cài frontend bằng `npm ci` khi có lockfile. Không đổi package manager hoặc tạo thêm lockfile khác.
- Thêm dependency phải có lý do, chủ file thực hiện và cập nhật manifest/lock tương ứng.
- Lock Python phải được cập nhật từ môi trường sạch/phù hợp của dự án; không đưa đường dẫn editable cục bộ hoặc package cá nhân vào file khóa.
- Không tự chạy `npm audit fix --force`, downgrade major hoặc tắt kiểm tra TLS để làm hết lỗi.
- Hướng xử lý lỗi chứng chỉ/chính sách Windows và advisory đã biết nằm trong `docs/BOOTSTRAP-STATUS.md`. Kiểm tra trạng thái mới, không coi ghi nhận cũ là lý do bỏ qua advisory mới.
- Không commit/đưa vào log: API key, token, mật khẩu, `.env`, database, file người dùng, nội dung tài liệu nhạy cảm hoặc môi trường ảo.
- Chỉ biến cấu hình công khai được đặt tiền tố `VITE_`; API key LLM ở backend.
- Không ghi đè `.env` đã có; dùng `.env.example` để mô tả biến mới.
- Không xóa volume, file người dùng hoặc database, chạy migration phá hủy dữ liệu hay gọi API tốn phí nếu chưa được phép trong nhiệm vụ.
- Bootstrap hiện chưa có xác thực; Phú triển khai auth theo phân công mới. Giữ localhost cho đến khi cơ chế phiên và quyền sở hữu được tích hợp/kiểm thử; không coi đổi tài liệu là đã thêm auth.
- Mọi truy cập khi bổ sung nhiều người dùng phải được kiểm tra ở máy chủ, gồm URL file trực tiếp và ID bị sửa từ client.

## 10. Kiểm tra trước khi bàn giao

Chạy kiểm tra tương ứng với phạm vi thay đổi. Thêm/sửa test có ý nghĩa cho hành vi mới hoặc lỗi sửa; không đổi kỳ vọng test để che lỗi, không thêm test chỉ kiểm tra lại nội dung source.

Các lệnh dưới đây chạy từ **thư mục gốc repository** trên Windows:

```powershell
# Backend
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m ruff check backend
backend/.venv/Scripts/python.exe -m ruff format --check backend

# Frontend: build đã bao gồm typecheck
npm --prefix frontend test
npm --prefix frontend run build

# Khi thay đổi API/schema
backend/.venv/Scripts/python.exe backend/scripts/export_openapi.py

# Khi thay đổi cấu hình container
docker compose config --quiet
```

macOS/Linux thay `backend/.venv/Scripts/python.exe` bằng `backend/.venv/bin/python`.

| Thay đổi | Kiểm tra tối thiểu |
| --- | --- |
| Backend/RAG | Test hành vi bị ảnh hưởng, bộ pytest backend và Ruff |
| Frontend | Test frontend, typecheck/build; xem trực tiếp màn hình bị đổi |
| Hợp đồng dùng chung | Backend + frontend, OpenAPI snapshot, thử bên cung cấp và bên sử dụng |
| UI | Kiểm tra desktop/mobile, bàn phím, trạng thái lỗi và màn hình dài |
| Docker/CI | Kiểm tra cấu hình; chạy môi trường thật khi có điều kiện |
| Chỉ tài liệu | So lại đường dẫn, lệnh, phân công và hợp đồng; không cần chạy lại toàn bộ test nếu code không đổi |

- Sửa backend chung/schema phải kiểm tra cả các consumer liên quan, không chỉ một test riêng.
- Khi có điều kiện, thử luồng xuyên suốt: tạo môn → tải PDF thật → chọn nguồn → hỏi → mở nguồn → xem lại. Không tuyên bố luồng này hoàn tất khi upload/RAG vẫn là stub.
- Nếu test không chạy được, ghi rõ lệnh, lỗi và phần chưa xác minh. Không báo “passed” dựa trên đọc code hoặc kết quả của lần trước.
- Docker config hợp lệ không chứng minh container đã chạy. Có file CI không chứng minh GitHub Actions đã qua.
- Không cần cài thêm công cụ hoặc chạy lại kiểm tra không liên quan cho một thay đổi tài liệu nhỏ.

## 11. Mẫu giao nhiệm vụ cho AI

Mỗi phiên phải nêu một lát cắt có thể kiểm tra, không giao chung chung “làm hết phần tôi”.

### Phúc — Sổ tay và Không gian học tập

```text
Tôi là Phúc, sở hữu module Sổ tay môn học/Không gian học tập xuyên suốt frontend–backend.
Nhiệm vụ: <một lát cắt, ví dụ list/create sổ tay của người đang đăng nhập>.
Phạm vi: <file React/API/schema/model/service/test cụ thể của module>.
Đọc AGENTS.md, docs/MODULE-OWNERSHIP.md và hợp đồng liên quan.
Dùng auth/history service của Phú, retrieval/document service của Bảo; không viết bản sao.
Giữ thiết kế đã chốt; test UI/API, dữ liệu lỗi và truy cập trái owner.
Nếu phụ thuộc chưa có, dùng fixture có nhãn cho phát triển/test, ghi phần chưa tích hợp.
Không tự thay file chung, commit/push/merge hoặc xóa dữ liệu ngoài quyền của nhiệm vụ.
Bàn giao file sửa, cách chạy, test thực tế và phần cần module khác tiếp nối.
```

### Bảo — Tài liệu và Retrieval

```text
Tôi là Bảo, sở hữu module Tài liệu của tôi và retrieval xuyên suốt frontend–backend.
Nhiệm vụ: <ví dụ upload PDF thật, list trạng thái và cung cấp chunks>.
Phạm vi: <file React/API/schema/model/service/test document/retrieval cụ thể>.
Đọc AGENTS.md, docs/MODULE-OWNERSHIP.md và hợp đồng nguồn.
Dùng current user của Phú và workspace của Phúc; không viết auth/LLM/chat history khác.
Test định dạng/dung lượng/trùng/lỗi/owner và đầu ra dữ liệu cho Phúc.
Nếu cần đổi component nguồn, hợp đồng chunk/search hoặc schema chung, phối hợp consumer trước.
Không tự commit/push/merge hoặc xóa DB/file hiện có ngoài quyền được giao.
Bàn giao UI + API + dữ liệu + test và cách module học tập sử dụng.
```

### Phú — Lịch sử và Authentication/Authorization

```text
Tôi là Phú, sở hữu Lịch sử AI, Auth và app shell xuyên suốt frontend–backend.
Nhiệm vụ: <ví dụ đăng nhập/me/current-user dependency hoặc list lịch sử theo owner>.
Phạm vi: <file React/API/schema/model/service/test auth/history/app shell cụ thể>.
Đọc AGENTS.md, docs/MODULE-OWNERSHIP.md và hợp đồng liên quan.
Cung cấp auth/history interface cho Phúc/Bảo, không tự làm UI tài liệu hay retrieval.
Test ít nhất hai tài khoản; kiểm tra phiên, truy cập trái quyền và mở lại đúng hội thoại.
Dùng database/Base chung; migration/dependency chung phối hợp Bảo.
Không tự commit/push/merge hoặc mở dịch vụ công khai ngoài quyền được giao.
Bàn giao UI + API + service dùng chung + test và cách consumer tích hợp.
```

## 12. Tiêu chuẩn bàn giao của mỗi nhiệm vụ

Trước khi báo hoàn thành, kiểm tra diff và dùng mẫu ngắn:

```text
Thành viên / nhiệm vụ:
Đã làm:
File thay đổi:
Hợp đồng, dependency hoặc migration thay đổi:
Cách chạy / cách sử dụng:
Kiểm tra: <lệnh thực tế → kết quả>
Phần chưa chạy được / chưa hoàn thành:
Phụ thuộc hoặc việc cần thành viên khác tiếp nối:
Git: <nhánh; đã/chưa commit/push/PR theo quyền được giao>
```

PR dùng `.github/pull_request_template.md`. Không tự nhận một phần đã tích hợp nếu mới chạy độc lập.
Giữ PR nhỏ, tránh trộn sửa UI, đổi API, nâng dependency và refactor không liên quan.

## 13. Mốc phối hợp hiện hành

- Phân công theo module ở `docs/MODULE-OWNERSHIP.md` thay thế mọi phân công theo tầng trước đây.
- 18/11: baseline/hợp đồng; Bảo ổn định ORM Base/router, Phú auth context/app shell,
  Phúc ranh giới workspace/chat/generation. Phần chưa có có thể phát triển bằng fixture có nhãn.
- 19/11: ghép auth/owner filtering sớm; nối PDF thật → retrieval → chat → lịch sử.
- 20/11: kiểm tra hai tài khoản, lỗi/stream, nguồn/xóa và responsive; dừng thêm tính năng 18:00,
  hạn nội bộ 22:00, hạn cuối 23:59 thứ Sáu 20/11/2026 UTC+7, trừ khi nhóm đổi deadline.
- 30 điểm ước lượng/người không bảo đảm số giờ bằng nhau; ghi thời gian thực, điều chỉnh task
  độc lập và owner trước khi hỗ trợ. Không để hai AI cùng sửa một file.
- Auth làm tăng phạm vi so với demo một người cũ; không cam kết toàn bộ PRD trong ba ngày.
  Báo sớm phần chưa đạt, không bỏ phân quyền hoặc đổi mock thành kết quả thật.
- Các mốc này chỉ thuộc đợt bàn giao đầu, không tự áp dụng cho nhiệm vụ sau ngày đó.
