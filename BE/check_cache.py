"""
Cache kết quả `kiem_tra_bang_cong` theo (file_mtime, file_size, ca_lam_mtime).

Tránh chạy lại toàn bộ pipeline (đọc Excel 4 lần + parse ca_lam + duyệt NV/ngày)
mỗi lần FE gọi /api/check/{filename}.

Cache tự invalidate khi:
- file upload thay đổi (mtime/size đổi) -> cache key khác, tính lại
- ca_lam_xtep.xlsx thay đổi (mtime đổi) -> cache key khác, tính lại
- file bị xoá -> gọi invalidate(filename)
- server restart -> cache trống, tính lại (chấp nhận được)

Cache là in-memory dict, an toàn cho 1 worker uvicorn. Khi scale nhiều worker
mỗi worker có cache riêng, nhưng vẫn đúng (chỉ chậm hơn).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


_CACHE: dict[str, dict] = {}
# Track ca_lam version đã dùng cho mỗi entry, để clear nhanh khi ca_lam đổi
_LAST_CALAM_KEY: Optional[tuple] = None


def _file_signature(path: Path) -> Optional[tuple]:
    """Trả về (mtime, size) của file, hoặc None nếu không tồn tại."""
    if not path.exists():
        return None
    st = path.stat()
    return (st.st_mtime, st.st_size)


def make_cache_key(filename: str, file_path: Path, calamfile: str) -> Optional[tuple]:
    """Tạo cache key cho 1 filename.

    Key = (filename, file_signature, calam_signature).
    Trả None nếu file không tồn tại.
    """
    file_sig = _file_signature(file_path)
    if file_sig is None:
        return None
    calam_path = Path(calamfile)
    calam_sig = _file_signature(calam_path) if calam_path.exists() else (0, 0)
    return (filename, file_sig, calam_sig)


def get(filename: str, file_path: Path, calamfile: str) -> Optional[dict]:
    """Lấy kết quả cached nếu còn hợp lệ (file + ca_lam không đổi)."""
    key = make_cache_key(filename, file_path, calamfile)
    if key is None:
        return None
    entry = _CACHE.get(filename)
    if entry and entry.get("key") == key:
        return entry.get("result")
    return None


def set(filename: str, file_path: Path, calamfile: str, result: dict) -> None:
    """Lưu kết quả vào cache."""
    key = make_cache_key(filename, file_path, calamfile)
    if key is None:
        return
    _CACHE[filename] = {"key": key, "result": result}


def invalidate(filename: Optional[str] = None) -> None:
    """Xoá cache.

    - Nếu truyền filename: chỉ xoá entry của file đó (dùng khi upload/delete).
    - Nếu None: xoá toàn bộ cache (dùng khi ca_lam đổi).
    """
    global _LAST_CALAM_KEY
    if filename is None:
        _CACHE.clear()
        _LAST_CALAM_KEY = None
    else:
        _CACHE.pop(filename, None)


def clear_if_calam_changed(calamfile: str) -> None:
    """Xoá toàn bộ cache nếu ca_lam_xtep.xlsx thay đổi so với lần trước."""
    global _LAST_CALAM_KEY
    calam_path = Path(calamfile)
    sig = _file_signature(calam_path) if calam_path.exists() else (0, 0)
    if _LAST_CALAM_KEY != sig:
        _CACHE.clear()
        _LAST_CALAM_KEY = sig


def stats() -> dict:
    """Thông tin cache (debug/log)."""
    return {"size": len(_CACHE), "filenames": list(_CACHE.keys())}