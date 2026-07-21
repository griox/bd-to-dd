# 1. Danh sách các tài liệu cần tạo
- Tầng UI
| Tên tài liệu | Đơn vị tạo | Nội dung |
| --- | --- | --- |
| Screen | Screen | Thiết kế các hàm Composable cho bố cục tổng thể màn hình |
| Composable | Function | Thiết kế các hàm Composable riêng cho từng màn hình |
| ViewModel | Feature ID | Thiết kế UI State quản lý trạng thái màn hình; thiết kế logic ViewModel; thiết kế State Mapper |
| Navigation | Feature ID | Thiết kế điều phối chuyển đổi màn hình (Navigation) |
| Resource | Feature ID | Thiết kế các nhãn, văn bản sử dụng trên màn hình |
- Tầng Domain
| Tên tài liệu | Đơn vị tạo | Nội dung |
| --- | --- | --- |
| UseCase | UseCase | Thiết kế logic nghiệp vụ riêng cho từng màn hình |
| Service | Service | Thiết kế logic chung sử dụng trong chức năng |
| Repository Interface | Interface | Thiết kế Entity đầu vào/đầu ra |
- Tầng Data
| Tên tài liệu | Đơn vị tạo | Nội dung |
| --- | --- | --- |
| Repository (DB) | Interface | Thiết kế Dto, Dao, và mapping giữa Dto và Entity |
| Repository (API) | Interface | Thiết kế Dto, API client, và mapping giữa Dto và Entity |
| Repository (DataStore/MemoryStore) | Interface | Thiết kế các lớp dữ liệu, interface DataStore |
| Repository (File) | Interface | Thiết kế thư mục/file đầu vào-đầu ra |

# 2. Bảng  tài liệu design theo độ phức tạp màn hình.
- Định nghĩa độ phức tạp
| Độ phức tạp | Nội dung | Ví dụ |
| --- | --- | --- |
| Thấp | Chỉ hiển thị đơn giản, không có nhập liệu, không lấy dữ liệu, không chuyển màn hình | Màn hình splash, màn hình lỗi, màn hình trợ giúp |
| Trung bình | Có nhập liệu đơn giản (nhập text, bấm nút), lấy/lưu từ một nguồn dữ liệu, chuyển màn hình đơn giản, quản lý trạng thái đơn giản | Màn hình đăng nhập, màn hình cài đặt, hiển thị danh sách đơn giản |
| Cao | Nhập liệu phức tạp, lấy/lưu từ nhiều nguồn dữ liệu, logic nghiệp vụ phức tạp | Màn hình chi tiết sản phẩm, màn hình kết quả tìm kiếm, màn hình cài đặt phức tạp |
| Rất cao | UI/UX nâng cao, quản lý trạng thái phức tạp, liên kết giữa nhiều màn hình | Màn hình chính, danh sách giao nhận, danh sách tác vụ với UI dạng thẻ |
| - Bảng các tài liệu cần tạo theo độ phức tạp màn hình |  |  | Note: ○ = Required, △ = Recommended, Blank = Optional |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| Layer | Tài liệu | Ghi chú | Thấp | Trung bình | Cao | Rất cao |
| UI | Screen | Cần thiết cho tất cả màn hình | ○ | ○ | ○ | ○ |
| UI | Composable | Nếu có custom UI component |  | △ | ○ | ○ |
| UI | ViewModel | Nếu cần quản lý trạng thái |  | ○ | ○ | ○ |
| UI | Navigation | Nếu có chuyển màn hình |  | △ | ○ | ○ |
| UI | Resource | Nếu cần hỗ trợ đa ngôn ngữ hoặc quản lý văn bản |  | △ | ○ | ○ |
| Domain | UseCase | Nếu có business logic |  | △ | ○ | ○ |
| Domain | Service | Nếu có logic chung hoặc xử lý phức tạp |  |  | △ | ○ |
| Domain | Repository Interface | Nếu cần truy cập dữ liệu |  | △ | ○ | ○ |
| Data | Repository (DB) | Nếu cần truy cập DB cục bộ |  | △ | ○ | ○ |
| Data | Repository (DataStore/MemoryStore) | Nếu cần lưu cài đặt hoặc dữ liệu vùng nhớ riêng |  | △ | ○ | ○ |
| Data | Repository (File) | Nếu cần thao tác file I/O |  |  | △ | ○ |
| Data | Repository (API) | Nếu cần truy cập API |  | △ | ○ | ○ |
Back