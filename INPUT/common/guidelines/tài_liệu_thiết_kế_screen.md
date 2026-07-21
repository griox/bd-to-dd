# 1. Thiết kế hàm Composable

## 1.1. Tên hàm
- Quy tắc đặt tên: {ID màn hình}Screen(...)
- Ví dụ: N9P90A0X2101W102Screen(...)

## 1.2. Tham số đầu vào
| Tên tham số | Kiểu dữ liệu | Mô tả |
| --- | --- | --- |
| navController | NavHostController | Controller điều khiển chuyển đổi màn hình |
| viewModel | {ID chức năng}ViewModel | Lớp ViewModel thao tác trạng thái UI của màn hình |
- navController là tham số bắt buộc để Framework kiểm soát chuyển đổi màn hình.

## 1.3. Cấu trúc màn hình (Các hàm Composable cấu tạo nên màn hình)
- Ví dụ:
| Tên hàm Composable | Loại hàm | Nội dung/Vai trò | Ghi chú |
| --- | --- | --- | --- |
| HomeTopBar | FW | Thanh top bar | - |
| TaskListSectionCard |  | Thẻ danh sách đã chọn | - |
| PreShipmentTasks |  | Tác vụ trước khi xuất kho | - |
| ... | ... | ... | - |
- Nguyên tắc chia nhỏ hàm Composable:
- Chia hàm Composable theo từng trách nhiệm riêng biệt.
- Mỗi hàm chỉ đảm nhận một vai trò, càng đơn giản càng tốt.
- Phân biệt hàm Composable có quản lý trạng thái UI (stateful) và không quản lý trạng thái (stateless).
- Nếu là danh sách (ví dụ: LazyColumn), các item hiển thị nên có hàm Composable riêng.
- Đặt tên hàm Composable rõ ràng theo đối tượng được vẽ (dạng danh từ).
- Nguyên tắc, sử dụng tên đã đăng ký trong từ điển mục. Nếu phía hệ thống giao nhận (PF) chưa định nghĩa thì tự quản lý bên phía ứng dụng thiết bị.
- Nếu là hàm Composable riêng của màn hình, hãy chèn liên kết tới tài liệu thiết kế hàm Composable được tạo cùng lúc.
- Loại hàm:
- FW: Hàm Composable chung do Framework cung cấp
- DS: Hàm Composable do DesignSystem cung cấp
- Trống: Hàm Composable riêng của màn hình
- Nội dung/Vai trò: Ghi rõ hàm vẽ cái gì.
- Các hàm bố trí layout (Row, Column,...) có thể ghi hoặc không.

## 1.4. Danh sách Action
- Ví dụ:
| Đối tượng | Action | Nội dung xử lý | Nguyên nhân phát sinh |
| --- | --- | --- | --- |
| PreShipmentTasks | onClick | Gọi phương thức YY của XXViewModel | Nhấn nút bắt đầu tác vụ trước khi xuất kho |
| ... | ... | ... | ... |
- Cột “Đối tượng”: Ghi tên hàm Composable sở hữu phần tử UI sinh ra Action.
- Cột “Action”: Ghi tên tham số sự kiện của hàm Composable.
- Cột “Nội dung xử lý”: Ghi tóm tắt xử lý khi Action được kích hoạt.
- Nguyên tắc, Action chỉ gọi phương thức của ViewModel. Hàm Composable chỉ đảm nhận vẽ UI, không chứa logic xử lý.
- Cột “Nguyên nhân phát sinh”: Ghi rõ thao tác trong màn hình dẫn đến phát sinh Action.
Back