# Design Input Bundle UI

## Goal

Người dùng upload một bộ đầu vào giống `INPUT/input`: một file Markdown mô tả thiết kế, một hoặc nhiều ảnh UI, và một file CSV danh sách composable. Hệ thống chỉ sinh DD sau khi toàn bộ bộ input được tiếp nhận và phân tích.

## Contract

`POST /projects/{project_id}/documents/design-input` nhận multipart fields `design`, `images`, `composable`. Markdown là bắt buộc; ảnh và CSV là tùy chọn. Backend lưu Markdown thành `basic-design`; Gemini Flash phân tích từng ảnh, ghép kết quả với CSV có tiêu đề rõ ràng và lưu thành `ui-design`.

## UI

Form có ba upload card riêng, hiển thị tên file, số ảnh và giải thích vai trò. Nút chạy bị khóa nếu thiếu Markdown. Timeline giải thích Input Bundle, Gemini Vision, BD Analysis, KB Retrieval, Analysis Review, DD Generation và Review/Export.

## Errors

Sai định dạng, file quá lớn, CSV không UTF-8 hoặc Gemini chưa cấu hình phải hiển thị lỗi backend và không bắt đầu generate.

