# Hướng Dẫn Nâng Cấp Triển Khai Môi Trường Production Trên Google Cloud Run

Tài liệu này hướng dẫn chi tiết các bước thiết lập và triển khai môi trường **Production chính thức** cho dự án **BD-to-DD Toolkit** trên Google Cloud Run với đầy đủ hạ tầng lưu trữ bền vững (Persistent Data Storage).

---

## 1. Hạ Tầng Môi Trường Production

Khi chạy trên Production, hệ thống sử dụng 3 dịch vụ lưu trữ chuyên dụng thay thế cho bộ nhớ tạm ephemeral local:

| Thành Phần | Công Nghệ Môi Trường Demo | Công Nghệ Môi Trường Production | Lợi Ích Production |
| :--- | :--- | :--- | :--- |
| **Relational Database** | SQLite (`/tmp/test.db`) | **Google Cloud SQL (PostgreSQL)** | Lưu trữ bền vững dữ liệu Jobs & Projects, chia sẻ nhất quán giữa nhiều container. |
| **Dense Vector DB** | Qdrant In-Memory (`:memory:`) | **Qdrant Cloud Cluster** | Lưu trữ lâu dài toàn bộ Vector Embedding, hỗ trợ mở rộng hàng ngàn tài liệu không lo OOM. |
| **Object Storage** | Local File (`/tmp/artifacts`) | **Google Cloud Storage (GCS Bucket)** | Lưu trữ vĩnh viễn các file tài liệu Markdown/CSV upload và kết quả sinh ra. |

---

## 2. Các Biến Môi Trường Cần Thiết Cho Production

Khai báo các biến môi trường này trong file `.env` hoặc truyền trực tiếp vào Cloud Run:

```env
# 1. API Keys LLM & Embeddings
GEMINI_LLM_API_KEY=AIzaSy...
GEMINI_EMBEDDING_API_KEY=AIzaSy...

# 2. Database PostgreSQL / Cloud SQL
DATABASE_URL=postgresql://postgres:YourPassword@10.x.x.x:5432/bd_to_dd_db

# 3. Dedicated Qdrant Cloud Cluster
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster-id.asia-east1.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-cloud-api-key

# 4. Google Cloud Storage Bucket
GCS_BUCKET_NAME=your-gcp-project-bd-to-dd-assets
GCS_PREFIX=artifacts/
```

---

## 3. Quy Trình Triển Khai 1-Click (`deploy_production.sh`)

Mở Terminal và thực thi script tự động hóa triển khai Production:

```bash
# Khai báo cấu hình Production
export DATABASE_URL="postgresql://user:pass@cloudsql-ip:5432/bd_to_dd"
export QDRANT_URL="https://your-cluster-id.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your-qdrant-api-key"

# Chạy script deploy Production
./deploy_production.sh
```

---

## 4. Các Điểm Tối Ưu Đã Thực Hiện Cho Production

1. **SQLAlchemy Connection Pooling**:
   - Tối ưu bộ quản lý kết nối DB tại [database.py](file:///Users/huyngo/bd-to-dd-toolkit/backend/app/infrastructure/persistence/postgres/database.py): `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=1800` giúp tự động khôi phục kết nối hỏng và chịu tải lớn.

2. **Dịch Vụ GCS Persistent Storage**:
   - Tự động lưu trữ file qua [gcs_storage_service.py](file:///Users/huyngo/bd-to-dd-toolkit/backend/app/infrastructure/storage/gcs_storage_service.py) khi `GCS_BUCKET_NAME` được khai báo.

3. **Cloud Run Multi-Instance & Zero Downtime**:
   - Cấu hình `--min-instances 1` để loại bỏ thời gian Cold Start.
   - Hỗ trợ `--max-instances 10` tự động mở rộng theo lượng người dùng thực tế.
