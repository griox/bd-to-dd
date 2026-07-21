# 1. Thiết kế UI State

## 1.1. Tên lớp
{ID chức năng}UiState
- Quy tắc đặt tên là “ID chức năng” + “UiState”.
- Ví dụ: N9P90A0X0010UiState
Các mục trên màn hình (thông tin cần thiết để hiển thị các mục trên màn hình) mà cần giữ trạng thái động sẽ được định nghĩa là UI State.

## 1.2. Thuộc tính
| Tên thuộc tính | Kiểu | Diễn giải | Giá trị khởi tạo |
| --- | --- | --- | --- |
| isLoading | Boolean | Trạng thái đang tải | False |
| items | List | Danh sách mục hiển thị | emptyList() |
| errorMessage | String? | Thông báo lỗi |  |
| inputText | String | Văn bản nhập của người dùng | "" |
| selectedTabIndex | Int | Vị trí hiển thị tab | False |
- Quy tắc đặt tên:
- Đặt tên theo kiểu camelCase.
- Đặt tên rõ ràng, cụ thể.
- Nếu là dữ liệu nghiệp vụ, sử dụng tên đã đăng ký trong từ điển mục.
- Tránh viết tắt, nếu bắt buộc phải dùng thì phải đăng ký và sử dụng nhất quán.
- Các từ viết tắt phổ biến như id, url có thể dùng, nhưng tránh viết tắt không rõ nghĩa như usr, ct.
- Mẫu đặt tên
- Chuỗi, số: sử dụng tên đã đăng ký.
- Tập hợp: dùng số nhiều (items, users).
- Cờ (Boolean): thêm tiền tố động từ (is, has), ví dụ isLoading, hasPhoto.

# 2. Thiết kế ViewModel

## 2.1. Tên lớp
- Quy tắc đặt tên là “ID chức năng” + “ViewModel”.
- Ví dụ: N9P90A0X0010ViewModel

## 2.2. Phương thức
| Tên phương thức | Tham số đầu vào | Tóm tắt xử lý |
| --- | --- | --- |
| initialize | Không có | Đọc dữ liệu Xxx khi khởi tạo |
| createInitialState | Không có | Tạo và trả về constructor mặc định của UI State |
| onTabChanged | newTabIndex: Int | Cập nhật vị trí hiển thị tab của UI State bằng giá trị đầu vào |
*** IMPORTANT ***
- Các phương thức dưới đây phải được implement (được định nghĩa là abstract ở lớp cơ sở Framework).
- initialize: Được gọi khi khởi tạo ViewModel, ví dụ đọc dữ liệu khi màn hình hiển thị ban đầu.
- createInitialState: Tạo trạng thái ban đầu của UI State.
- Quy tắc đặt tên:
- Đặt tên theo kiểu camelCase.
- Event handler bắt đầu bằng "on".
- Phương thức gán giá trị cho trạng thái hoặc thuộc tính bắt đầu bằng "set".
- Phương thức khác bắt đầu bằng động từ.
- Mẫu đặt tên
- Hành động do người dùng khởi phát: on + đối tượng + động từ (onTabChanged, onXxxSelected).
- Cập nhật trạng thái: set + tên thuộc tính (setIsLoading, setIsXxxEnabled).
- Phương thức khác: động từ + đối tượng (loadUsers, calculateTotal).

## 2.3. Thiết kế chi tiết từng phương thức
- Ghi rõ nội dung xử lý cho từng phương thức.
- Chỉ dẫn thiết kế bên trong:
- Xử lý ngoại lệ: nguyên tắc không bắt ngoại lệ phát sinh, mà truyền lên cấp trên để Framework xử lý.
- Nếu lỗi là nghiệp vụ, bọc bằng BusinessLogicException và truyền lên.
- Ghi log: chú ý phân biệt INFO và DEBUG, tránh ghi log quá mức, đặc biệt trong vòng lặp lớn.

## 2.3. 1 initialize
- Nội dung xử lý:
- Gọi phương thức initialize của lớp cha
- Dùng xử lý bất đồng bộ chung của lớp cha để thực hiện các bước:
- Gọi XXUseCase để lấy dữ liệu Xxx
- Dùng State Mapper để gán dữ liệu vào UI State
- Khi gọi UseCase, đính kèm link đến UseCase liên quan (đường dẫn tương đối).
- Nếu cần ánh xạ giá trị trả về của UseCase sang UI State, đính kèm link đến thiết kế State Mapper.

## 2.3. 2 createInitialState
Nội dung xử lý
...

## 2.3. 3 ...

# 3. Thiết kế State Mapper
- Ghi rõ quy cách ánh xạ giá trị trả về của UseCase sang UI State.
- Ghi theo từng UseCase.

## 3.1. Tên lớp
{XXX}StateMapper
- Quy tắc đặt tên là “UseCaseID” + “StateMapper”.
| Giá trị trả về của UseCase | Thuộc tính UI State | Quy cách chuyển đổi | Ghi chú |
| --- | --- | --- | --- |
| items | items |  |  |
- Chuyển đổi sang trạng thái phù hợp để hiển thị UI được thực hiện ở đây.
- Nếu cần chuyển đổi, ghi rõ quy cách chuyển đổi ở cột tương ứng.
Back