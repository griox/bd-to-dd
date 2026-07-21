# 1. Cấu trúc navigation
| Tên màn hình | Tên route | Tên Bridge | Tổng quan Bridge |
| --- | --- | --- | --- |
| XxxScreen | "xxx" |  |  |
| YyyScreen | "yyy" | {ID Bridge}Bridge | Hiển thị dựa trên tham số truyền vào |
| ... | ... | ... | ... |
- Đối với các màn hình trong chức năng, định nghĩa route cho từng màn hình.
- Tên màn hình: sử dụng tên hàm Composable đã ghi trong tài liệu thiết kế Screen. Nguyên tắc đặt tên: “ID màn hình” + “Screen”.
- Tên route: đặt theo “ID màn hình”.
- Tên Bridge: Nếu chỉ chuyển màn hình đơn thuần thì để trống. Nếu có xử lý Bridge, ghi tên lớp Bridge (sẽ mô tả ở phần dưới) và đính kèm liên kết đến vị trí tương ứng trong tài liệu này.
- Tổng quan Bridge: Ghi tổng quan về xử lý của Bridge.

# 2. Thiết kế Bridge

# 2. 1 Tên lớp
{ID Bridge}Bridge
- Quy tắc đặt tên: “ID Bridge” + “Bridge”.
- Phạm vi của lớp Bridge là public.

## 2.1. 1 Tham số đầu vào
| Key | Giá trị | Kiểu | Ghi chú |
| --- | --- | --- | --- |
| key1 | XXXUiState.inputText | String |  |
| ... | ... | ... | ... |
- Trong Bundle, định nghĩa key chuỗi, giá trị và kiểu để truyền tham số đầu vào.
Key: Nguyên tắc sử dụng tên đã đăng ký trong từ điển mục.

## 2.1. 2 Xử lý
- Tham khảo {ID Bridge}_{Tên xử lý}.md
Gọi {Xxx}UseCase.
- Nếu giá trị trả về là "A", chuyển sang chức năng A.
- Nếu giá trị trả về là "B", chuyển sang chức năng B.
- Các trường hợp khác, chuyển sang chức năng mặc định.
- Đính kèm liên kết đến vị trí tương ứng của tài liệu thiết kế bên ngoài.
- Liên kết đến nhánh main của repository chứa tài liệu thiết kế bên ngoài.
- Nếu tài liệu thiết kế bên ngoài đã mô tả đủ flow xử lý, phần mô tả flow xử lý trong tài liệu này là không bắt buộc.
- Xử lý Bridge thường gồm hai phần: “xử lý chuyển màn hình” và “xử lý nghiệp vụ khi chuyển màn hình”.
- Xử lý chuyển màn hình: thiết kế trong lớp Bridge.
- Xử lý nghiệp vụ: thiết kế như một UseCase và gọi từ lớp Bridge.
- Đính kèm liên kết đến tài liệu thiết kế UseCase được gọi, bằng đường dẫn tương đối từ tài liệu này.

# 2. 2 Tên lớp
...

## 2.2. 1 Tham số đầu vào
...

## 2.2. 2 Xử lý
...
Back