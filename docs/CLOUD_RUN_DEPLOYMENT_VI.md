# Hướng Dẫn Deploy Dự Án BD-to-DD Toolkit Lên Google Cloud Run (Option 2 - Demo Setup)

Tài liệu này hướng dẫn chi tiết từng bước để triển khai dự án **BD-to-DD Toolkit** lên Google Cloud Run dành cho môi trường **Demo/Thử nghiệm** (chi phí tối ưu, tự động scale to 0 khi rảnh).

---

## 1. Chuẩn Bị Trước Khi Deploy

1. **Cài đặt Google Cloud SDK (`gcloud` CLI)**:
   Nếu chưa cài đặt `gcloud`, tải và cài đặt tại: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

2. **Đăng nhập và chọn Project**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```

3. **Bật các Google Cloud API cần thiết**:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
   ```

---

## 2. Phương Án Triển Khai (1-Click Deploy Script)

Dự án đã được tích hợp sẵn file script `deploy_cloud_run.sh`. Bạn chỉ cần thực hiện 2 lệnh sau:

```bash
# 1. Khai báo API Key Gemini của bạn (nếu có)
export GEMINI_API_KEY="your-gemini-api-key-here"

# 2. Thực thi script deploy tự động
./deploy_cloud_run.sh
```

---

## 3. Quy Trình Hoạt Động Của Môi Trường Demo Trên Cloud Run

| Thành Phần | Cấu Hình Trên Cloud Run | Giải Thích |
| :--- | :--- | :--- |
| **Backend Service** | `bd-to-dd-backend` | Container Python FastAPI. Chạy trên Cloud Run với cờ `--no-cpu-throttling` để các tác vụ ngầm sinh thiết kế không bị freeze CPU. |
| **Frontend Service** | `bd-to-dd-frontend` | Container Next.js SSR/Standalone. Nhận request từ người dùng và giao tiếp với Backend Service qua REST API. |
| **Database (SQLite)** | `sqlite:////tmp/test.db` | Cơ sở dữ liệu SQLite nằm tại thư mục `/tmp` tạm thời của Cloud Run. Tự khởi tạo lại dữ liệu khi container khởi động. |
| **Vector DB (Qdrant)** | `QDRANT_URL=:memory:` | Chạy Vector Store dạng **In-Memory** trên RAM của container Backend. Không cần cài đặt cluster Qdrant ngoài. |
| **Sparse Index (BM25)** | `/tmp/bm25_index.json` | File index từ khóa BM25 lưu tạm trong `/tmp`. |

---

## 4. Deploy Thủ Công (Nếu Không Dùng Script)

Nếu bạn muốn deploy thủ công từng bước bằng lệnh `gcloud`:

### Bước 4.1: Deploy Backend Service
```bash
gcloud run deploy bd-to-dd-backend \
  --source ./backend \
  --region asia-east1 \
  --allow-unauthenticated \
  --no-cpu-throttling \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "GEMINI_API_KEY=your-api-key,QDRANT_URL=:memory:,DATABASE_URL=sqlite:////tmp/test.db,TMP_DIR=/tmp,ARTIFACTS_DIR=/tmp/artifacts,BM25_INDEX_PATH=/tmp/bm25_index.json"
```

Lấy URL Backend sau khi deploy xong (Ví dụ: `https://bd-to-dd-backend-xxx-de.a.run.app`).

### Bước 4.2: Deploy Frontend Service
```bash
gcloud run deploy bd-to-dd-frontend \
  --source ./frontend \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "NEXT_PUBLIC_API_BASE_URL=https://bd-to-dd-backend-xxx-de.a.run.app/api/v1"
```

---

## 5. Lưu Ý Cho Môi Trường Production (Tương Lai)

Khi nâng cấp dự án từ Demo lên môi trường **Production chính thức**:
1. Thay thế SQLite `/tmp` bằng **Google Cloud SQL (PostgreSQL)**.
2. Thay thế Qdrant In-Memory bằng **Qdrant Cloud Cluster** chuyên dụng via `QDRANT_URL` và `QDRANT_API_KEY`.
3. Lưu trữ tài liệu thiết kế và file upload lên **Google Cloud Storage (GCS Bucket)**.
