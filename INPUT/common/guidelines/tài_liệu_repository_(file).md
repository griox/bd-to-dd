# 1. Tên class
- Quy tắc đặt tên: {RepositoryID} + “RepositoryImpl”.

# 2. Tham số đầu vào, giá trị trả về
- Tham khảo thiết kế RepositoryIF RepositoryID_TênChứcNăng.md
- Dẫn link đến tài liệu thiết kế interface.
- Link là đường dẫn tương đối từ tài liệu này.

# 3. Thiết kế lưu trữ (storage)

## 3.1. Tên thư mục
- Quy tắc đặt tên: “{5 ký tự đầu của RepositoryID}/{RepositoryID}/”.
*** Note: Tạo cấu trúc thư mục dạng phân cấp theo 5 ký tự đầu của RepositoryID để tránh quá nhiều file/thư mục trong một thư mục gốc, giúp tránh giảm hiệu năng.

## 3.2. Loại file:
- CSV
- JSON
- JPG
- Khác

## 3.3. Định dạng file:
Xxxログファイル
- Nếu là file văn bản, đính kèm link đến tài liệu định dạng file. Nếu file lưu trên Google Drive, đính kèm link đến file trên Google Drive. Nếu đã có trong tài liệu thiết kế ngoài, chỉ cần đính kèm link đến repository main của tài liệu đó.
Back
Đây là một ví dụ mẫu đầy đủ cho màn hình Tạo thông tin bệnh nhân (PatientCreate)