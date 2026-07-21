# DD-only Knowledge Base Design

## Goal

Knowledge Base chỉ chứa các Detail Design đã review nằm trong `INPUT/DD/**`. Dữ liệu trong `INPUT/input/**` chỉ phục vụ demo/upload thủ công và không được ingest vào KB.

## Data flow

`InputReviewedDdLoader.load()` chỉ đọc đệ quy `INPUT/DD`. Mỗi screen ID tạo một reviewed sample chứa các tài liệu Screen/ViewModel tương ứng. File văn bản được parse trực tiếp; ảnh trong `INPUT/DD` vẫn bắt buộc đi qua Gemini Vision.

Explicit reindex phải kiểm tra Qdrant sẵn sàng, tải và chuẩn bị toàn bộ sample/chunk/embedding, xóa dense và sparse index cũ, rồi ghi tập chunk mới. Nếu cấu hình hoặc dependency bắt buộc thiếu, reindex trả lỗi và không báo thành công.

## Reset semantics

- Dense store cung cấp thao tác xóa toàn bộ collection KB và tạo lại collection rỗng.
- Sparse index cung cấp thao tác xóa toàn bộ tài liệu trong bộ nhớ.
- Reindex không được trả `already_seeded`; đó chỉ là hành vi của automatic seed.
- Reset chỉ diễn ra trong explicit reindex, không xảy ra khi đọc status hoặc khi application khởi động.

## Verification

- Loader bỏ qua mọi file trong `INPUT/input`.
- Loader vẫn gom Screen và ViewModel từ `INPUT/DD` theo screen ID.
- Explicit reindex gọi clear cho dense và sparse trước khi upsert.
- Reindex báo lỗi khi Qdrant không sẵn sàng hoặc không có DD sample.

