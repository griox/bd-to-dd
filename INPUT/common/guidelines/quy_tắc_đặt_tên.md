# 1. Common chung

## 1.1. ID hệ thống
- Quy tắc đặt tên: N9

## 1.2. Tên hệ thống
- Quy tắc đặt tên: 次期集配2027

## 1.3. ID nghiệp vụ
- Quy tắc đặt tên: P90 〜 P9Z
ID nghiệp vụ sẽ được chia làm 3 phần chính sau:
- Android (Ứng dụng phân phối thế hệ tiếp theo): P90 〜 P99
| ID nghiệp vụ | Đối tượng |
| --- | --- |
| P90 | Ứng dụng phân phối (giao nhận hàng) |
| P91 | Trình duyệt tuỳ chỉnh cho ứng dụng phân phối |
| P92–P97 | (Chưa sử dụng) |
| P98 | Thành phần chung giữa các ứng dụng trên thiết bị |
| P99 | Thành phần chung cấp cao trên thiết bị |
- Android (ngoài ứng dụng phân phối): P9H 〜 P9N
| ID nghiệp vụ | Đối tượng |
| --- | --- |
| P9H | Ứng dụng trang chủ |
| P9I | Ứng dụng xác thực |
| P9J | Ứng dụng cài đặt thiết bị |
| P9K | Trình duyệt tuỳ chỉnh đa năng |
| P9L–P9N | (Chưa sử dụng) |
- Ngoài ứng dụng Android: P9A 〜 P9G
| ID nghiệp vụ | Đối tượng |
| --- | --- |
| P9A | Phân phối PF |
| P9B | Phân phối PF (dự phòng) |
| P9C | Quản lý phân phối web |
| P9D | Hệ thống quản lý hỗ trợ phân phối (bảo trì master) |
| P9E–P9G | (Chưa sử dụng) |

## 1.4. ID nhóm chức năng
- Quy tắc đặt tên: ID hệ thống + ID nghiệp vụ + (A0 đến Z9)
*** Ví dụ về ID nhóm chức năng nằm trong ứng dụng phân phối:
N9P90A0

## 1.5. ID chức năng
- Quy tắc đặt tên: ID nhóm chức năng + ký tự cố định (X) + số thứ tự (4 chữ số)
*** Ví dụ về ID chức năng nằm trong ứng dụng phân phối:
N9P90A0X0010

## 1.6. Định nghĩa về loại ứng dụng
| Mã | Tên | Ghi chú |
| --- | --- | --- |
| W | Ứng dụng web |  |
| A | Ứng dụng Android |  |
| P | Ứng dụng WPF |  |
| S | Shell |  |
| B | Ứng dụng VB.net |  |
| C | Ứng dụng C / C++ |  |
| J | Upper layer: US (BFF) |  |
| K | Upper layer: BS (API) |  |
| L | Upper layer: bất đồng bộ |  |
| M | Upper layer: batch |  |

## 1.7. String Resource ID
- Quy tắc đặt tên: Ký tự cố định (M) + ID nghiệp vụ + Loại ứng dụng + Loại tài nguyên (1 ký tự) + Loại thông điệp (1 ký tự) + chuỗi cố định (6 chữ số (alphabet, number))
- ID nghiệp vụ (Tham khảo định nghĩa ở mục 1.3)
- Loại ứng dụng (Tham khảo định nghĩa ở mục 1.6)
- Loại tài nguyên được định nghĩa ở bảng sau:
| Mã | Tên |
| --- | --- |
| L | Log |
| R | Screen Text |
| M | Screen Message |
| A | Screen Text (Array) |
- Loại thông điệp được định nghĩa ở bảng sau:
| Mã | Tên | Ghi chú |
| --- | --- | --- |
| I | Loại thông tin | INFO |
| E | Loại lỗi | ERROR, FATAL |
| W | Loại cảnh báo / chú ý | WARN |
| Q | Loại hỏi đáp | QUESTION |
*** Ví dụ về Resource ID nằm trong ứng dụng phân phối:
MP90AMW000001
MP90AMW00A001
MP90AME9A0001

# 2. App Ứng dụng phân phối (Giao nhận hàng)

## 2.1. ID màn hình
- Quy tắc đặt tên: ID chức năng + ký tự cố định (W) + số thứ tự (3 chữ số)
*** NOTE ***: Các thành phần UI chung trong/giữa chức năng cũng dùng quy tắc này (nên dùng số thứ tự ở dải 900).
- Ví dụ: N9P90A1X0010W001

## 2.2. Use Case ID
Quy tắc đặt tên: ID chức năng + ký tự cố định (U) + số thứ tự (3 chữ số)
*** NOTE ***: Các thành phần BL chung trong/giữa chức năng cũng dùng quy tắc này (nên dùng số thứ tự ở dải 900).
- Ví dụ: N9P90A1X0010U001

## 2.3. ID nhóm repository
- Quy tắc đặt tên: ID nhóm chức năng + ký tự cố định (R) + số thứ tự (4 chữ số)
- Ví dụ: N9P90A1R0010

## 2.3. ID repository
- Quy tắc đặt tên: ID nhóm repository + ký tự cố định (R) + số thứ tự (3 chữ số)
- Ví dụ: N9P90A1R0010R001

## 2.4. Dao ID
- Quy tắc đặt tên: ID nhóm repository + ký tự cố định (D) + số thứ tự (3 chữ số)
- Ví dụ: N9P90A1R0010D001

## 2.5. ID báo cáo (Report)
- Quy tắc đặt tên: ID nhóm repository + ký tự cố định (P) + số thứ tự (3 chữ số)
*** NOTE ***: ID nhóm chức năng cố định là Z1; số thứ tự của ID chức năng cố định là 0000.
- Ví dụ: N9P90Z1R0000P001

## 2.6. Background Task ID
- Quy tắc đặt tên: ID chức năng + ký tự cố định (B) + số thứ tự (3 chữ số)
- Ví dụ: N9P90A1X0010B001

# 3. Platform Ứng dụng phân phối (Giao nhận hàng)

## 3.1. API ID (API tầng US hoặc tầng BS cho chức năng)
- Quy tắc đặt tên: ID chức năng + ký tự cố định (A) + số thứ tự (3 chữ số)
- Ví dụ: N9P9BA1X0010A001

# 4. Web Ứng dụng phân phối (Giao nhận hàng)

## 4.1. ID màn hình
- Quy tắc đặt tên: ID chức năng + ký tự cố định (W) + số thứ tự (3 chữ số)
- Ví dụ: N9P9CA1X0010W001

# 5. Từ điển nghiệp vụ (Business Dictionary)

Phần này quy định cách chuyển đổi từ thuật ngữ Hán tự (Kanji) trong BD sang định danh (Identifier) trong DD. 

## 5.1. Quy tắc chuyển đổi chung
- **Tuyệt đối không dịch sang tiếng Anh chuyên ngành** (Ví dụ: KHÔNG dịch 航空会社 thành Airline).
- **Sử dụng Romaji CamelCase:** Viết phiên âm tiếng Nhật, viết hoa chữ cái đầu của mỗi từ.
- **Ưu tiên sự nhất quán:** Nếu một thuật ngữ đã xuất hiện trong bảng dưới đây, bắt buộc phải sử dụng đúng từ đó cho tất cả các màn hình (W002 - W009).

## 5.2. Bảng đối chiếu thuật ngữ (Mapping Table)

| Tiếng Nhật (BD) | Romaji (DD) | Diễn giải |
| :--- | :--- | :--- |
| 航空会社 | KokuKaisha | Hãng hàng không |
| 搭載種別 | TosaiSbt | Loại đóng gói/chứa |
| 異常種別 | AbnormalSbt | Loại bất thường (Ngoại lệ: Giữ English theo baseline) |
| 便名 | BinNm | Số hiệu chuyến bay |
| 搭載日付 | TosaiDate | Ngày đóng gói |
| ボックスNo | BoxNo | Số hộp |
| コンテナNo | ContainerNo | Số công-te-nơ |
| 登録件数 | TourokuKensu | Số lượng đăng ký |
| 小計 | Shokei | Tổng phụ/Tiểu kế |
| 検索 | Search | Tìm kiếm (Dùng English theo chuẩn kỹ thuật) |

## 5.3. Quy tắc đặt tên Class kỹ thuật
Để vượt qua máy chấm điểm `evaluator.py`, tên Class phải tuân thủ:
- **Định dạng:** `{ScreenID}UiState` và `{ScreenID}ViewModel`.
- **Lưu ý:** KHÔNG bao gồm tiền tố dự án trong tên Class.
