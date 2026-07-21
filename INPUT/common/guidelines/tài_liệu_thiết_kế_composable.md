# 1. Thiết kế Composable {XX}_Tên hàm
Tài liệu thiết kế này được lập theo từng hàm.
Phần {XX} được thêm số thứ tự tùy ý sao cho các hàm Composable liên quan được nhóm lại trong cùng một thư mục.
Nếu hàm Composable chỉ được sử dụng từ một hàm cấp trên cụ thể trong cấu trúc phân cấp, hãy định nghĩa nó với phạm vi private trong cùng tệp.

## 1.1. Tên hàm
- Ví dụ: PreShipmentTasks
- Tên hàm nên rõ ràng thể hiện đối tượng được vẽ (dùng danh từ).
- Nguyên tắc: sử dụng tên đã đăng ký trong từ điển mục.

## 1.2. Tham số đầu vào
| Tên mục | Kiểu | Note |
| --- | --- | --- |
| Không có | - | - |

## 1.3. Cấu trúc (Các hàm Composable cấu thành)
- Ví dụ:
| Tên hàm Composable | Loại hàm | Nội dung/Chức năng | Ghi chú |
| --- | --- | --- | --- |
| DsAccordionCard | DS | Thanh trên cùng |  |
| AccordionHeader |  | Hàm Composable được gán cho tham số headerContent của DsAccordionCard |  |
| AccordionBody |  | Hàm Composable được gán cho tham số bodyContent của DsAccordionCard |  |
| ... | ... | ... | ... |
- Nguyên tắc tách hàm Composable:
- Tách thành các hàm Composable khác nhau theo trách nhiệm.
- Mỗi hàm Composable chỉ đảm nhận một vai trò, giữ càng đơn giản càng tốt.
- Tách biệt hàm Composable có trạng thái (stateful) và không có trạng thái (stateless).
- Đối với danh sách (LazyColumn...), tách riêng hàm Composable cho từng item hiển thị.
- Tên hàm nên rõ ràng thể hiện đối tượng được vẽ (dùng danh từ). Nguyên tắc: sử dụng tên đã đăng ký trong từ điển mục.
- Nếu là hàm Composable riêng cho màn hình, hãy đính kèm liên kết đến tài liệu thiết kế hàm Composable tương ứng.
- Loại hàm:
- FW: Hàm Composable chung do Framework cung cấp
- DS: Hàm Composable do DesignSystem cung cấp
- Trống: Hàm Composable riêng của màn hình
- Nội dung/Vai trò: Ghi rõ hàm vẽ cái gì.
- Các hàm bố trí layout (Row, Column,...) có thể ghi hoặc không.

## 1.4. Danh sách Action
- Ví dụ:
| Đối tượng | Action | Nội dung | Nguyên nhân phát sinh |
| --- | --- | --- | --- |
| XXX | onClick | Gọi phương thức YY của XXViewModel | Nhấn nút XXX |
| ... | ... | ... | ... |
- Đối tượng: ghi hàm Composable có phần tử UI phát sinh action.
- Action: ghi tên tham số dùng để phát sinh sự kiện của hàm Composable.
- Nội dung: tóm tắt xử lý được thực hiện khi Action diễn ra. Nguyên tắc: chỉ gọi phương thức của ViewModel.
- Nguyên tắc: Hàm Composable chỉ đảm nhận việc vẽ UI, không chứa logic nghiệp vụ.
- Nguyên nhân phát sinh: ghi thao tác thực tế trên màn hình dẫn đến action.
Back