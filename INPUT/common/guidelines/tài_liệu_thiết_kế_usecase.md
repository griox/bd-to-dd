# 1. Tên interface
- Để sử dụng DI, luôn phải định nghĩa interface.
- Nguyên tắc: {UseCaseID} + “UseCase”.
- Nếu gọi từ bridge, dùng {BridgeID} + “UseCase”.

# 2. Tên lớp
- Nguyên tắc: {UseCaseID} + “UseCaseImpl”.
- Nếu gọi từ bridge: {BridgeID} + “UseCaseImpl”.

# 3. Domain Model / Repository liên quan
| Tên | Loại | Mục đích |
| --- | --- | --- |
| XxxRepository | Repository | Dùng để lấy/sửa dữ liệu |
| XxxEntity | Entity | Domain model (ví dụ: người dùng, sản phẩm, đơn hàng, ...) |
Liệt kê các RepositoryIF và Entity sử dụng.

# 4. Tên phương thức
- Tên phương thức thống nhất là: execute
- Framework sẽ bắt buộc implement phương thức execute ở lớp cơ sở.

# 5. Tham số đầu vào

# 5. 1 Tên class
{UseCaseID}InEntity
hoặc
{BridgeID}InEntity

# 5. 2 Thuộc tính
| Tên | Kiểu | Diễn giải | Kiểm tra/giới hạn |
| --- | --- | --- | --- |
| userID | String | ID người dùng | Bắt buộc, tối đa 20 ký tự |
| quantity | Int | Số lượng | Số nguyên ≥ 0 |
- Tên thuộc tính: dùng camelCase, ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Diễn giải: ghi rõ ý nghĩa.
- Kiểm tra/giới hạn: ghi rõ quy tắc kiểm tra đầu vào.
- Nếu đã được ghi trong tài liệu thiết kế ngoài, chỉ cần dẫn link đến tài liệu đó.

# 6. Giá trị trả về

# 6. 1 Tên class
{UseCaseID}OutEntity
hoặc
{BridgeID}OutEntity

# 6. 2 Thuộc tính
| Tên | Kiểu | Diễn giải |
| --- | --- | --- |
| result | XxxEntity | Thông tin Xxx lấy được |
| success | Boolean | Đánh giá thành công xử lý |
| errorMessage | String? | Lưu thông báo lỗi nếu có |
- Tên thuộc tính: dùng camelCase, ưu tiên tên đã đăng ký trong từ điển mục.
- Kiểu: ghi rõ kiểu dữ liệu.
- Diễn giải: ghi rõ ý nghĩa.
- Nếu đã được ghi trong tài liệu thiết kế ngoài, chỉ cần dẫn link đến tài liệu đó.

# 7. Xử lý
Tham khảo: {UseCaseID}_{TênUseCase}.md
- Kiểm tra đầu vào
- Lấy dữ liệu cần thiết qua Repository liên quan
- Thực hiện domain logic (thao tác Entity, thay đổi trạng thái)
- Trả về kết quả xử lý
- Nếu flow xử lý đã được mô tả đầy đủ trong tài liệu thiết kế ngoài, chỉ cần dẫn link đến tài liệu đó.

# 8. Xử lý ngoại lệ / lỗi
| Loại ngoại lệ | Vị trí phát sinh | Xử lý |
| --- | --- | --- |
| XxxException | Gọi Repository | Nếu không lấy được dữ liệu thì thực hiện Xxx thay thế |
| ... | ... | ... |
*** Nguyên tắc: không bắt ngoại lệ, nên phần này thường không cần ghi. Chỉ ghi nếu đặc biệt bắt buộc phải xử lý ngoại lệ theo yêu cầu nghiệp vụ.
Back
Thiết kế Service_{ServiceID}_{TênService}.md
- Tài liệu này được lập cho từng Service.
- Các chức năng chung trong một chức năng (logic dùng chung) là vai trò của Service.
- Định hướng thiết kế bên trong tuân theo hướng dẫn thiết kế UseCase.
- Phạm vi lớp được định nghĩa trong Service là internal.