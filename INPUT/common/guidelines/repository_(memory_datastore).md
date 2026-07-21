# 1. Tên class
- Quy tắc đặt tên: {RepositoryID} + “RepositoryImpl”.

# 2. Tham số đầu vào, giá trị trả về
- Tham khảo thiết kế RepositoryIF RepositoryID_TênChứcNăng.md
- Dẫn link đến tài liệu thiết kế interface.
- Link là đường dẫn tương đối từ tài liệu này.

# 3. Định nghĩa Key
- Định nghĩa giá trị Key dùng cho Key-Value Store.
- Quy tắc đặt tên: {RepositoryID}.

# 4. Thiết kế file định nghĩa Proto
- Các mục dưới đây chỉ ghi nếu sử dụng DataStore.
- Nếu dùng MemoryCache thì không cần ghi.

## 4.1. Tên file
- Quy tắc đặt tên: {RepositoryID} + “.pb”.
- Danh sách trường (message định nghĩa)
| Tên trường | Kiểu | Diễn giải |
| --- | --- | --- |
| id | string | ID duy nhất |
| name | string | Tên |
| price | int32 | Giá (đơn vị: Yên) |
| created_at | string | Thời gian tạo (định dạng YYYYMMDD) |
- Tên trường: dùng snake_case (proto phổ biến dùng snake_case), ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Diễn giải: ghi rõ ý nghĩa hoặc giải thích về trường.

## 4.2. Mapping giữa DTO vào/ra và Proto message
| Proto message | {RepositoryID}*Entity | Quy tắc chuyển đổi | Ghi chú |
| --- | --- | --- | --- |
| id | id | Copy trực tiếp |  |
| name | name | Copy trực tiếp |  |
| price | price | Copy trực tiếp |  |
| created_at | createdAt | Chuyển từ string (YYYYMMDD) sang LocalDateTime |  |
- Định nghĩa quy tắc mapping giữa proto message và giá trị trả về của Repository.
- Nếu có chuyển đổi, ghi rõ ở cột "Quy tắc chuyển đổi".
Back
Tài liệu thiết kế lớp triển khai Repository (phiên bản file) RepositoryID_TênChứcNăng
- Tài liệu này được lập cho từng lớp triển khai RepositoryIF.
- Phạm vi class được định nghĩa trong Repository là public.
*** IMPORTANT ***
Định hướng thiết kế bên trong
- Thiết kế an toàn luồng (Thread-safe):
- Lớp Repository phải được thiết kế không giữ trạng thái (stateless).
Lý do: Nếu lưu trạng thái trong thuộc tính lớp, sẽ không an toàn luồng khi các trường hợp sau xảy ra:
Nhiều phương thức được thực thi đồng thời bằng xử lý bất đồng bộ.
Các phương thức đồng thời thao tác cùng một thuộc tính lớp.
(TODO: Đang xem xét cơ chế loại trừ đồng thời một cách thống nhất ở phía Framework)
- Khi thực thi từ nhiều thread cùng lúc, cần thiết kế kiểm soát loại trừ phù hợp.
Lý do: Nếu cùng lúc cập nhật một nguồn tài nguyên, trạng thái cuối cùng của dữ liệu có thể không xác định, dẫn đến lỗi hoặc sai lệch dữ liệu.
- Quản lý bộ nhớ thiết bị:
- Nếu tham số đầu vào hoặc trả về là List hoặc các lớp tập hợp, luôn cần giới hạn số lượng tối đa.
Nếu vượt quá số lượng tối đa, phải thiết kế xử lý phù hợp (báo lỗi, chỉ lấy tối đa, hỗ trợ phân trang, v.v.).
(TODO: Số lượng tối đa sẽ được quyết định theo đặc tả và yêu cầu của ứng dụng.)
- Xử lý ngoại lệ:
- Nguyên tắc không bắt ngoại lệ phát sinh, mà truyền lên cấp trên để Framework xử lý thống nhất.
- Lỗi nghiệp vụ phải được bọc bằng BusinessLogicException (do Framework cung cấp) rồi truyền lên cấp trên.
- Ghi log:
- Log bắt đầu/kết thúc/ngoại lệ của phương thức execute sẽ do Framework xuất ra, không cần ứng dụng nghiệp vụ tự ghi.
- Khi ghi log, phân biệt 2 loại sau:
Log INFO: Xuất khi chạy thực tế. Chỉ ghi log cần thiết cho điều tra, phân tích. Tránh ghi thừa, đặc biệt trong vòng lặp lớn.
Log DEBUG: Chỉ dùng khi phát triển, không xuất khi chạy thực tế.
- Các điều cấm:
- Không tạo hoặc sử dụng class có scope vượt quá vòng đời của ViewModel trong logic nghiệp vụ (ví dụ Application scope).
Lý do: Nếu tạo instance ở scope Application, instance không được giải phóng khi ViewModel kết thúc, gây rò rỉ bộ nhớ.
- Không dùng reflection (kotlin.reflect) trong logic nghiệp vụ.
Lý do: Có thể gây lỗi khi tối ưu hóa bằng Google R8 lúc build.
- Không implement xử lý dùng coroutine, thread một cách tường minh trong logic nghiệp vụ. Nếu bắt buộc về hiệu năng, phải trao đổi với đội kỹ thuật.