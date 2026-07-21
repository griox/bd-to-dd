# 1. Thiết kế resource chuỗi
*** Nguyên tắc: các resource không phải chuỗi sẽ được định nghĩa từ các component trong DesignSystem, do đó chỉ cần định nghĩa resource chuỗi.
| **ResourceID | Chuỗi | Diễn giải/Ghi chú** |
| --- | --- | --- |
| Được định nghĩa trong tài liệu thiết kế bên ngoài |  |  |
| MP90ARI390301 | Laser・Nhập tay | Tiêu đề tab |
| MP90ARI390302 | Camera | Tiêu đề tab |
| MP80ARI0342 | Mã vận đơn bên thứ ba | Nhãn textbox |
| ... | ... | ... |
*** TIP ***
- Định nghĩa nội dung chuỗi cho các ResourceID đã được xác định trong thiết kế bên ngoài.
- Nếu thiết kế bên ngoài đã ghi đầy đủ nội dung chuỗi, không cần ghi lại ở tài liệu này, mà chỉ cần đính kèm liên kết đến tài liệu thiết kế bên ngoài.
- Liên kết sẽ trỏ tới nhánh main của repository lưu trữ tài liệu thiết kế bên ngoài.
Back
Thiết kế UseCase: {UseCaseID}_{TênUseCase}.md
*** TIP ***
- Tài liệu này được lập cho từng UseCaseID.
- Phạm vi lớp được định nghĩa trong UseCase là internal.
*** IMPORTANT *** 
- Thiết kế an toàn luồng (Thread-safe):
- Lớp UseCase phải được thiết kế không giữ trạng thái (stateless).
     *** Lý do: Nếu lưu trạng thái trong thuộc tính của lớp, sẽ không an toàn luồng khi có các trường hợp sau:
- Nhiều phương thức được thực hiện đồng thời bằng xử lý bất đồng bộ.
- Các phương thức đồng thời thao tác cùng một thuộc tính lớp.
- Xử lý ngoại lệ:
- Nguyên tắc không bắt (catch) ngoại lệ phát sinh, mà truyền lên cấp trên để Framework xử lý thống nhất.
- Lỗi nghiệp vụ phải được bọc bằng BusinessLogicException (lớp ngoại lệ nghiệp vụ do Framework cung cấp) rồi truyền lên cấp trên.
- Ghi log:
- Log bắt đầu / kết thúc / ngoại lệ của phương thức execute sẽ do Framework xuất ra, không cần ứng dụng nghiệp vụ tự ghi.
- Khi ghi log, phân biệt 2 loại sau:
-        - Log INFO: Xuất cả khi chạy thực tế. Chỉ ghi log cần thiết cho điều tra, phân tích. Tránh ghi thừa, đặc biệt trong vòng lặp lớn.
-       - Log DEBUG: Chỉ dùng khi phát triển, không xuất khi chạy thực tế.
- Các điều cấm:
- Không tạo hoặc sử dụng lớp có scope vượt quá vòng đời của ViewModel trong nghiệp vụ logic (ví dụ Application scope).
     *** Lý do: Nếu tạo instance ở scope Application, instance không được giải phóng khi ViewModel kết thúc, gây rò rỉ bộ nhớ.
- Không dùng reflection (kotlin.reflect) trong nghiệp vụ logic.
    *** Lý do: Có thể gây lỗi khi tối ưu hóa bằng Google R8 lúc build.
- Không implement xử lý dùng coroutine, thread một cách tường minh trong nghiệp vụ logic. Nếu bắt buộc về hiệu năng, phải trao đổi với đội kỹ thuật.