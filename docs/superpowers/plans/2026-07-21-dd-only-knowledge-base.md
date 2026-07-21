# DD-only Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chỉ ingest `INPUT/DD/**` và thay thế sạch KB cũ khi explicit reindex.

**Architecture:** Thu hẹp sample loader về DD-only. Bổ sung hợp đồng `clear()` cho dense/sparse stores và để explicit reindex chuẩn bị dữ liệu, reset hai index, rồi ingest tập mới.

**Tech Stack:** Python, unittest, FastAPI service layer, Qdrant, in-memory BM25, Gemini Embedding.

## Global Constraints

- `INPUT/input/**` không được ingest vào KB.
- Chỉ `INPUT/DD/**` tạo reviewed samples.
- Thiếu dependency bắt buộc phải báo lỗi rõ ràng.
- Không xóa file nguồn trong `INPUT`.

---

### Task 1: DD-only sample loader

**Files:**
- Modify: `backend/tests/test_input_loader.py`
- Modify: `backend/app/infrastructure/persistence/input_loader.py`

- [ ] Viết test tạo đồng thời file trong `INPUT/input` và `INPUT/DD`, khẳng định chỉ sample `dd-*` được trả về.
- [ ] Chạy test và xác nhận test thất bại vì loader còn ingest `INPUT/input`.
- [ ] Đổi `load()` để chỉ gọi `_load_dd_samples()` và loại bỏ code input-ingestion không còn dùng.
- [ ] Chạy toàn bộ `test_input_loader.py`.

### Task 2: Replace semantics for explicit reindex

**Files:**
- Modify: `backend/app/domain/repositories/vector_store_repository.py`
- Modify: `backend/app/infrastructure/vectorstore/qdrant_repository.py`
- Modify: `backend/app/infrastructure/search/bm25_repository.py`
- Modify: `backend/app/application/use_cases/ingest_reviewed_dd.py`
- Modify: `backend/tests/test_ingestion_use_case.py`
- Modify: adapter-specific tests as required

- [ ] Viết test xác nhận explicit reindex gọi `clear()` trên dense và sparse stores trước `upsert_chunks()`.
- [ ] Chạy test và xác nhận thất bại vì chưa có reset contract.
- [ ] Thêm `clear()` vào protocols và adapters.
- [ ] Đổi `reindex()` để luôn rebuild thay vì dùng nhánh `already_seeded`.
- [ ] Chạy test ingestion và adapter.

### Task 3: Clear and rebuild configured KB

**Files:**
- Không sửa file nguồn.

- [ ] Chạy lint/syntax validation và backend test suite.
- [ ] Gọi explicit reindex trên runtime đã cấu hình để xóa KB cũ và nạp lại DD-only.
- [ ] Kiểm tra status/sample IDs không còn `screen-*` từ `INPUT/input` và chỉ còn `dd-*`.
- [ ] Nếu runtime/dependency không sẵn sàng, báo chính xác cấu hình còn thiếu và không tuyên bố dữ liệu đã được xóa.

