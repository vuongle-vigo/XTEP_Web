"""
FastAPI server: Webapp check công - phát hiện sai sót chấm công.
Wrap logic từ main.py (xac_dinh_ca_lam, phat_hien_sai_sot, kiem_tra_bang_cong).

Chạy:
    cd BE
    uvicorn api:app --reload --port 8000
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import shutil

# Import trực tiếp các hàm từ main.py và services
from main import (
    xac_dinh_ca_lam,
    phat_hien_sai_sot,
    kiem_tra_bang_cong,
    in_bao_cao,
    lay_calam_theo_filename,
)
from services import (
    list_uploaded_files,
    save_uploaded_file,
    get_file_path,
    delete_uploaded_file,
    get_raw_data,
    UPLOAD_DIR,
    BASE_DIR,
)
from calam import parse_ca_lam, DAY_MAP
from openpyxl.utils.exceptions import InvalidFileException

app = FastAPI(
    title="XTEP - Check Công Sai Sót",
    description="API phát hiện sai sót chấm công từ file Excel bảng công",
    version="1.0.0",
)

# CORS cho Next.js dev (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://103.90.224.132:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Models =====
class CheckResult(BaseModel):
    filename: str
    summary: dict
    details: dict  # {nhanvien: {day: [issues]}}


# ===== Health =====
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "XTEP Check Công"}


# ===== Files =====
@app.get("/api/files")
def api_list_files():
    """Danh sách file đã upload."""
    return {"files": list_uploaded_files()}


@app.post("/api/files/upload")
async def api_upload_file(file: UploadFile = File(...)):
    """Upload 1 file Excel (.xlsx)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ")
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file .xlsx")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File rỗng")

    try:
        info = save_uploaded_file(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lưu file: {e}")

    return {
        "filename": file.filename,
        "size": info["size"],
        "uploaded_at": info["uploaded_at"],
    }


@app.delete("/api/files/{filename}")
def api_delete_file(filename: str):
    """Xóa file đã upload."""
    ok = delete_uploaded_file(filename)
    if not ok:
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return {"deleted": filename}


@app.get("/api/files/{filename}/raw")
def api_get_raw_data(filename: str):
    """Trả về data thô: bangcong, tangca, chamcong, thu_ngay."""
    data = get_raw_data(filename)
    if not data:
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return data


# ===== Check (phát hiện sai sót) =====
@app.get("/api/check/{filename}")
def api_check(filename: str, calamfile: str = "ca_lam_xtep.xlsx"):
    """
    Chạy kiểm tra bảng công -> trả về danh sách sai sót.
    Mỗi nhân viên có issues theo từng ngày.
    """
    file_path = get_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{filename}' chưa được upload")

    # Tìm ca_lam_xtep.xlsx ở BE root
    calam_full_path = BASE_DIR / calamfile
    calamfile_to_use = str(calam_full_path) if calam_full_path.exists() else calamfile

    # Cache: tránh chạy lại kiem_tra_bang_cong + build summary khi file + ca_lam không đổi
    from check_cache import get as cache_get, set as cache_set, clear_if_calam_changed, make_cache_key
    clear_if_calam_changed(calamfile_to_use)

    cache_key = make_cache_key(filename, file_path, calamfile_to_use)
    if cache_key is None:
        raise HTTPException(status_code=404, detail=f"File '{filename}' không tồn tại trên ổ đĩa")

    cached = cache_get(filename, file_path, calamfile_to_use)
    if cached is not None:
        return cached

    try:
        result = kiem_tra_bang_cong(str(file_path), calamfile=calamfile_to_use)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {e}")

    # Build summary
    total_issues = 0
    issue_types = {
        "di_muon": 0,
        "ve_som": 0,
        "lam_thieu": 0,
        "may_thieu_bc_tc": 0,
        "tc_trong_ca": 0,
        "khac": 0,
    }
    employees_with_issues = 0
    days_with_issues = set()

    for nv, days in result.items():
        employees_with_issues += 1
        for day, issues in days.items():
            days_with_issues.add(day)
            for issue in issues:
                total_issues += 1
                il = issue.lower()
                if "đi muộn" in il or "di muon" in il:
                    issue_types["di_muon"] += 1
                elif "về sớm" in il or "ve som" in il:
                    issue_types["ve_som"] += 1
                elif "làm thiếu" in il or "lam thieu" in il:
                    issue_types["lam_thieu"] += 1
                elif "máy < bc+tc" in il or "may < bc+tc" in il:
                    issue_types["may_thieu_bc_tc"] += 1
                elif "ghi tc" in il:
                    issue_types["tc_trong_ca"] += 1
                else:
                    issue_types["khac"] += 1

    summary = {
        "total_issues": total_issues,
        "employees_with_issues": employees_with_issues,
        "days_with_issues": len(days_with_issues),
        "issue_types": issue_types,
    }

    payload = {
        "filename": filename,
        "summary": summary,
        "details": result,
    }

    # Cache toàn bộ response (đã có summary) để lần sau trả thẳng
    cache_set(filename, file_path, calamfile_to_use, payload)

    return payload


# ===== Helpers =====
@app.get("/api/ca-lam")
def api_ca_lam(filename: str):
    """Trả về ca làm tương ứng với file (theo tên cửa hàng)."""
    calamfile = BASE_DIR / "ca_lam_xtep.xlsx"
    if not calamfile.exists():
        raise HTTPException(
            status_code=404,
            detail="Chưa có file ca_lam_xtep.xlsx trong BE/. Hãy đặt file này vào thư mục BE.",
        )

    from calam import parse_ca_lam
    ca_lam_dict = parse_ca_lam(str(calamfile))
    calam = lay_calam_theo_filename(filename, ca_lam_dict)
    return {"filename": filename, "calam": calam}


@app.get("/api/info")
def api_info():
    """Thông tin hệ thống."""
    return {
        "upload_dir": str(UPLOAD_DIR),
        "base_dir": str(BASE_DIR),
        "has_ca_lam_file": (BASE_DIR / "ca_lam_xtep.xlsx").exists(),
        "day_map": DAY_MAP,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
