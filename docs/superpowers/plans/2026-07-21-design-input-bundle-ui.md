# Design Input Bundle UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho phép upload Markdown, nhiều ảnh UI và CSV như một bộ input trước khi sinh DD.

**Architecture:** Backend nhận bundle multipart và chuẩn hóa về hai document hiện có. Frontend quản lý ba nhóm file, upload bundle một lần rồi gọi generation pipeline hiện tại.

**Tech Stack:** FastAPI, Python unittest, Next.js 16, React 19, TypeScript, Tailwind CSS.

## Global Constraints

- Markdown bắt buộc; ảnh và CSV tùy chọn.
- Mọi ảnh phải qua Gemini Flash.
- Không đưa input runtime vào Knowledge Base.
- Không thay đổi các cổng Analysis Review và Designer Review.

---

### Task 1: Bundle API

- [ ] Viết test multipart bundle và test lỗi thiếu Markdown.
- [ ] Thêm endpoint `documents/design-input` để đọc, phân loại và ghép nội dung.
- [ ] Chạy backend image/upload tests.

### Task 2: Three-slot frontend

- [ ] Thay state Basic/UI cũ bằng Markdown, image list và CSV.
- [ ] Upload ba field vào bundle endpoint.
- [ ] Thay form bằng ba upload cards và mô tả luồng xử lý.
- [ ] Chạy ESLint, TypeScript và production build.

### Task 3: Runtime verification

- [ ] Rebuild backend/frontend containers.
- [ ] Kiểm tra bundle endpoint và trang frontend hoạt động.
- [ ] Xác nhận KB vẫn chỉ có sample `dd-*`.

