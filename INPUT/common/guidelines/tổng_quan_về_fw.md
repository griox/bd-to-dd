# 1. Thay đổi PPFW từ 8PP => 9PP
| 8PP |  |  |  |  |  |  |  |  |  |  |  | 9PP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |

# 2. Tổng quan chức năng của PPFW giai đoạn tiếp theo
Kiến trúc được thiết kế gồm 3 tầng:
- Tầng giao diện người dùng (UI).
- Tầng Domain.
- Tầng Data.
- Tầng UI
- DesignSystem (Style):
Tập hợp các thành phần như màu sắc, kiểu chữ,… do nhà thiết kế định nghĩa trên Figma.
- DesignSystem (Component):
Tập hợp các thành phần thiết kế dạng atomic do nhà thiết kế định nghĩa trên Figma.
*** Atomic là thiết kế chia nhỏ UI thành các phần tử cơ bản
- Utility (PL):
Tập hợp các thành phần như kiểm tra hợp lệ, kiểm tra gửi trùng, phản hồi người dùng,…
- Tầng Data
- Quản lý truy cập đến đĩa, bộ nhớ cache,…
Quản lý bộ nhớ cache
Quản lý cơ sở dữ liệu
Quản lý lưu trữ dữ liệu
Quản lý file
- Quản lý giao tiếp với backend
Quản lý giao tiếp HTTPS
- Các chức năng dùng chung (Cross-cutting)
- Utility (Data):
Tập hợp các thành phần như bộ chuyển đổi kiểu dữ liệu, định dạng dữ liệu,…
- Analytics:
Tập hợp các thành phần ghi lại hành động, log giao diện,…
- Xử lý lỗi:
Tập hợp các thành phần liên quan đến xử lý ngoại lệ, lỗi,…
- Thiết lập:
Tập hợp các thành phần liên quan đến thiết lập log và các cài đặt khác