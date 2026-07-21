# 1. Tên class
- Quy tắc đặt tên: {RepositoryID} + “RepositoryImpl”.

# 2. Tham số đầu vào, giá trị trả về
- Tham khảo thiết kế RepositoryIF RepositoryID_TênChứcNăng.md
- Dẫn link đến tài liệu thiết kế interface.
- Link là đường dẫn tương đối từ tài liệu này.

# 3. Thiết kế Room Entity

## 3.1. Tên class
XxxDto
- Định nghĩa DTO cho từng bảng và DTO lưu trữ kết quả JOIN giữa các bảng.
- DTO cho từng bảng: {EntityName} + “Dto”
- DTO cho kết quả JOIN: {RepositoryID} + “Dto”
- EntityName ưu tiên dùng tên đã đăng ký trong từ điển mục.
- Có thể dẫn link đến tài liệu định nghĩa bảng thay cho liệt kê chi tiết.
Tên bảng:
xxx_table
Danh sách trường:
| Tên trường | Kiểu | Tên cột DB | Index | Diễn giải |
| --- | --- | --- | --- | --- |
| id | String | id (PRIMARY KEY) |  | Khóa chính, ID duy nhất |
| name | String | name | 2 | Tên |
| price | Int | price | 1 | Giá (đơn vị: Yên) |
| createdAt | Long | created_at |  | Thời gian tạo (Unix epoch mili giây) |
- Tên trường: dùng camelCase, ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Tên cột DB: ghi đúng tên cột đã định nghĩa trong DB, gắn “(PRIMARY KEY)” với cột khóa chính.
- Index: ghi số thứ tự index nếu có nhiều index.
- Diễn giải: ghi rõ ý nghĩa hoặc giải thích về trường.

## 3.2. ...

# 4. Thiết kế Room Dao (Trường hợp truy cập DB local)

## 4.1. Tên class
- Quy tắc đặt tên: “RepositoryID” + “Dao”.

## 4.2. Tên phương thức
selectById(id: String)
- Tên phương thức dạng {Động từ}{(Tùy chọn)Tên Entity}{(Tùy chọn)Điều kiện}
- Dùng camelCase.
- Động từ: select (lấy), insert (thêm), update (sửa), delete (xóa)
- Tên entity: dùng tên entity chính khi JOIN, nếu lấy toàn bộ thì có thể bỏ qua.
- Điều kiện: Với các phương thức khác nhau theo điều kiện, dùng “By” + tên điều kiện (danh từ tiếng Anh).
- Ví dụ: ByID, ByName

## 4.3. SQL
Câu lệnh SQL thực thi
SELECT id, name, price, created_at FROM xxx_table WHERE id = :id

## 4.4. Mapping biến bind SQL và tham số đầu vào
| Biến bind | {RepositoryID}InEntity | Ghi chú |
| --- | --- | --- |
| id | id |  |
- Liệt kê mapping giữa tham số đầu vào của Repository và biến bind của SQL.

## 4.5. Mapping giữa Dto và giá trị trả về
| {RepositoryID}Dto | {RepositoryID}OutEntity | Quy tắc chuyển đổi | Ghi chú |
| --- | --- | --- | --- |
| id | id | Copy trực tiếp |  |
| name | name | Copy trực tiếp |  |
| price | price | Copy trực tiếp |  |
| createdAt | createdAt | Chuyển từ Long (Unix epoch mili giây) sang LocalDateTime |  |
- Định nghĩa quy tắc mapping giữa giá trị của Dto và giá trị trả về của Repository. Nếu có chuyển đổi, ghi rõ ở cột "Quy tắc chuyển đổi".
Back
Tài liệu thiết kế lớp triển khai Repository (phiên bản API) RepositoryID_TênChứcNăng
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
- Khi sử dụng List hoặc các class tập hợp để xử lý nhiều record trong tham số đầu vào hoặc trả về, luôn phải giới hạn số lượng tối đa.
- Kiểm tra giới hạn số lượng trả về của API để tránh trường hợp trả về quá nhiều dữ liệu ngoài dự kiến, cần thiết kế giới hạn tối đa cho mỗi API.
Nếu vượt quá số lượng tối đa, phải thiết kế xử lý phù hợp (ví dụ: báo lỗi, chỉ lấy tối đa, hỗ trợ phân trang, ...).
(TODO: Đang xác định số lượng tối đa dựa trên đặc tả và yêu cầu phía app).
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