"""
Service layer: lưu trữ file upload, quản lý danh sách file, đọc data thô.
"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

# Thư mục gốc của BE
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
META_FILE = DATA_DIR / "files_meta.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_files_meta() -> dict:
    """Đọc metadata file đã upload."""
    if not META_FILE.exists():
        return {}
    with open(META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_files_meta(meta: dict) -> None:
    """Lưu metadata."""
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_uploaded_files() -> list:
    """Trả về danh sách file đã upload, kèm metadata."""
    meta = load_files_meta()
    files = []
    for name, info in meta.items():
        path = UPLOAD_DIR / name
        if path.exists():
            files.append({
                "filename": name,
                "size": info.get("size", path.stat().st_size),
                "uploaded_at": info.get("uploaded_at"),
                "has_ca_lam_info": info.get("has_ca_lam_info", False),
            })
    files.sort(key=lambda x: x.get("uploaded_at") or "", reverse=True)
    return files


def save_uploaded_file(filename: str, content: bytes) -> dict:
    """Lưu file upload và update metadata."""
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(content)

    meta = load_files_meta()
    meta[filename] = {
        "size": len(content),
        "uploaded_at": datetime.now().isoformat(),
        "has_ca_lam_info": False,
    }
    save_files_meta(meta)
    return meta[filename]


def get_file_path(filename: str) -> Optional[Path]:
    """Lấy path tuyệt đối của file uploaded."""
    path = UPLOAD_DIR / filename
    if path.exists():
        return path
    return None


def delete_uploaded_file(filename: str) -> bool:
    """Xóa file upload."""
    path = UPLOAD_DIR / filename
    if path.exists():
        path.unlink()
    meta = load_files_meta()
    if filename in meta:
        del meta[filename]
        save_files_meta(meta)
    return True


def get_raw_data(filename: str) -> dict:
    """Trả về data thô của file: bangcong, tangca, chamcong, thu_ngay."""
    file_path = get_file_path(filename)
    if not file_path:
        return {}

    # Import trong hàm để tránh circular import
    from bangcong import get_bangcong_info
    from tangca import get_tangca_info
    from thongke import get_chamcong_info, get_thu_ngay

    return {
        "bangcong": get_bangcong_info(str(file_path)),
        "tangca": get_tangca_info(str(file_path)),
        "chamcong": get_chamcong_info(str(file_path)),
        "thu_ngay": get_thu_ngay(str(file_path)),
    }
