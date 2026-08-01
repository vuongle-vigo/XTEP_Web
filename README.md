# XTEP - Hệ thống Check Công

Webapp phát hiện **sai sót chấm công** từ file Excel bảng công của XTEP.

## Cấu trúc dự án

```
XTEP/
├── BE/                       # Backend (Python - FastAPI)
│   ├── main.py               # ⚠️ Logic gốc - KHÔNG sửa (trừ khi cần)
│   ├── common.py             # (giữ nguyên)
│   ├── calam.py              # (giữ nguyên)
│   ├── thongke.py            # (giữ nguyên)
│   ├── bangcong.py           # (giữ nguyên)
│   ├── tangca.py             # (giữ nguyên)
│   ├── ca_lam_xtep.xlsx      # File ca làm các cửa hàng
│   ├── api.py                # 🆕 FastAPI server (wrap logic từ main.py)
│   ├── services.py           # 🆕 Service: upload, lưu trữ, raw data
│   ├── requirements.txt      # 🆕
│   ├── uploads/              # 🆕 File upload từ FE
│   └── data/                 # 🆕 Metadata
└── FE/                       # Frontend (Next.js 14 + TypeScript + Tailwind)
    ├── app/
    │   ├── page.tsx          # Dashboard
    │   ├── upload/page.tsx   # Upload file
    │   ├── files/page.tsx    # Danh sách file
    │   ├── files/[filename]/page.tsx  # Chi tiết báo cáo từng file
    │   ├── issues/page.tsx   # Tổng hợp sai sót xuyên file
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/
    │   ├── app-shell.tsx
    │   ├── sidebar.tsx
    │   ├── topbar.tsx
    │   └── page-header.tsx
    └── lib/
        ├── api.ts            # API client
        ├── types.ts          # TypeScript types + helper
        └── utils.ts
```

## Cách chạy

### 1. Backend (BE)
```bash
cd BE
# Lần đầu: cài deps
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Chạy server
.\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8000
```
Backend chạy tại `http://localhost:8000`.

Docs API: `http://localhost:8000/docs`

### 2. Frontend (FE)
```bash
cd FE
npm install
npm run dev
```
Frontend chạy tại `http://localhost:3000`. (đã cấu hình Next.js rewrite proxy `/api/*` → `localhost:8000`)

## Các tính năng

### Backend API
- `GET  /api/health` — Health check
- `GET  /api/info` — Thông tin hệ thống
- `GET  /api/files` — Danh sách file đã upload
- `POST /api/files/upload` — Upload file `.xlsx`
- `DELETE /api/files/{filename}` — Xóa file
- `GET  /api/files/{filename}/raw` — Raw data (bangcong, tangca, chamcong, thu_ngay)
- `GET  /api/check/{filename}` — **Chạy kiểm tra và trả về sai sót** (gọi logic từ `main.py`)
- `GET  /api/ca-lam?filename=...` — Lấy ca làm theo cửa hàng

### Frontend (UI)
- **Dashboard** (`/`) — Tổng quan: số file, tổng sai sót, NV ảnh hưởng, sai sót nghiêm trọng
- **Upload** (`/upload`) — Kéo thả hoặc chọn file `.xlsx`
- **Files** (`/files`) — Bảng danh sách file + check status
- **File detail** (`/files/[filename]`) — Báo cáo chi tiết, filter theo loại sai sót, expandable từng NV
- **Issues** (`/issues`) — Tổng hợp sai sót tất cả file, filter, search

### Logic phát hiện sai sót (wrap từ `main.py`)
Các loại sai sót hệ thống phát hiện:
- 🚨 **Máy < BC+TC** (NV ghi nhiều hơn thực tế → thiệt hại công ty) — **nghiêm trọng**
- ⏰ **Đi muộn** so với ca
- 🏃 **Về sớm** so với ca
- ⏳ **Làm thiếu giờ** so với ca
- 📝 **Ghi TC nằm trong ca** (nghi vấn)
- ⚠️ **Khác**: BC=0 nhưng có máy, MCC không hợp lệ, không xác định được ca,...

## Cấu trúc file Excel đầu vào

File `.xlsx` cần có 3 sheet:
1. **BANGCONG** (BẢNG CÔNG) — Bảng công thủ công
2. **TANGCA** (TĂNG CA) — Giờ tăng ca
3. **ThongKe** — Dữ liệu chấm công máy

Cùng với file `ca_lam_xtep.xlsx` ở thư mục BE/ (đã có sẵn).
