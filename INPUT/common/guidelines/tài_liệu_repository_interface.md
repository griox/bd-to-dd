# 1. Tên interface
{RepositoryID}Repository
- Quy tắc đặt tên: {RepositoryID} + “Repository”.

# 2. Tên phương thức
- Tên phương thức thống nhất là execute.

# 3. Tham số đầu vào

# 3. 1 Tên Entity
- Quy tắc đặt tên: {RepositoryID} + “InEntity”.

# 3. 2 Thuộc tính
| Tên | Kiểu | Diễn giải | Kiểm tra/giới hạn |
| --- | --- | --- | --- |
| userID | String | ID người dùng | Bắt buộc, tối đa 20 ký tự |
| quantity | Int | Số lượng | Số nguyên ≥ 0 |
- Tên thuộc tính: dùng camelCase, ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Diễn giải: ghi rõ ý nghĩa.
- Kiểm tra/giới hạn: ghi rõ quy tắc kiểm tra đầu vào.
- Nếu đã được ghi trong tài liệu thiết kế ngoài, chỉ cần dẫn link đến tài liệu đó.

# 4. Giá trị trả về

# 4. 1 Tên class
{RepositoryID}OutEntity
- Quy tắc đặt tên: {RepositoryID} + “OutEntity”.
- Nếu luôn cần dữ liệu mới nhất, hãy ghi Flow<{RepositoryID}OutEntity>.
- Nếu trả về kiểu Flow, khi dữ liệu được cập nhật ở thread khác, dữ liệu thay đổi sẽ truyền về UI một cách bất đồng bộ.
- Tuy nhiên, nếu không cần giám sát dữ liệu thay đổi, chỉ cần trả về entity mà không dùng Flow.

# 4. 2 Thuộc tính
| Tên | Kiểu | Diễn giải |
| --- | --- | --- |
| result | XxxEntity | Thông tin Xxx lấy được |
| success | Boolean | Đánh giá thành công xử lý |
| errorMessage | String? | Lưu thông báo lỗi nếu có |
| ... | ... | ... |
- Tên thuộc tính: dùng camelCase, ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Diễn giải: ghi rõ ý nghĩa.
- Nếu đã được ghi trong tài liệu thiết kế ngoài, chỉ cần dẫn link đến tài liệu đó.
Back
Tài liệu thiết kế lớp triển khai Repository (phiên bản DB) RepositoryID_TênChứcNăng
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
- Nếu xử lý nhiều resource trong một transaction, phải quy định thứ tự truy cập các bảng và đảm bảo mọi Repository đều tuân thủ thứ tự này.
Lý do: Nếu thứ tự truy cập bảng không cố định, dễ phát sinh deadlock khi kiểm soát loại trừ.
(TODO: Kiểm soát transaction sẽ được quyết định khi thiết kế Framework vào cuối tháng 8/2025.)
- Transaction phải được kiểm soát ở Repository, vì tầng domain không nhận biết thực thể của Repository. Nếu kiểm soát transaction ở tầng domain, domain sẽ phải quan tâm đến implement connection Room, đi ngược lại triết lý kiến trúc.
- Quản lý bộ nhớ thiết bị:
- Khi sử dụng List hoặc các class tập hợp để xử lý nhiều record trong tham số đầu vào hoặc trả về, luôn phải giới hạn số lượng tối đa.
- Với SQL, phải sử dụng LIMIT để tránh trường hợp truy vấn trả về quá nhiều kết quả không mong muốn.
Nếu vượt quá số lượng tối đa, phải thiết kế xử lý phù hợp (ví dụ: báo lỗi, chỉ lấy tối đa, hỗ trợ phân trang, ...).
(TODO: Số lượng tối đa sẽ được xác định dựa trên đặc tả ứng dụng và xác nhận yêu cầu).
- Xử lý ngoại lệ:
- Nguyên tắc không bắt ngoại lệ phát sinh, mà truyền lên cấp trên để Framework xử lý thống nhất.
- Lỗi nghiệp vụ phải được bọc bằng BusinessLogicException (do Framework cung cấp) rồi truyền lên cấp trên.
- Quy tắc viết SQL:
- Tuân thủ quy tắc coding SQL của dự án.
- Quy định bổ sung:
- Chỉ cho phép JOIN giữa các bảng cùng domain nghiệp vụ (các bảng đã chuẩn hóa của một domain).
Lý do: Nếu JOIN giữa các domain khác nhau, dễ dẫn đến coupling chặt giữa các domain.
Lý do: SQL phức tạp, ảnh hưởng đến hiệu năng.
- JOIN với bảng master chỉ khi truy cập bằng PrimaryKey hoặc Index rõ ràng.
Lý do: JOIN master là nhu cầu phổ biến, cấm JOIN master sẽ khiến aggregate logic tiêu tốn quá nhiều resource.
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