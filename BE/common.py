import unicodedata
import re
import pandas as pd

_VIETNAMESE_MAP = {
    "đ": "d", "Đ": "d",
    "ơ": "o", "Ơ": "o",
    "ô": "o", "Ô": "o",
    "ă": "a", "Ă": "a",
    "â": "a", "Â": "a",
    "ê": "e", "Ê": "e",
    "ô": "o",
    "ư": "u", "Ư": "u",
}
_VIETNAMESE_PATTERN = re.compile("|".join(map(re.escape, _VIETNAMESE_MAP.keys())))

def remove_accents(text):
    """Chuyển thành chữ thường, không dấu"""
    if not isinstance(text, str):
        return text

    # Bước 1: Chuyển về chữ thường
    text = text.lower()

    # Bước 2: Thay thế các nguyên âm tiếng Việt đặc biệt (precomposed) trước
    text = _VIETNAMESE_PATTERN.sub(lambda m: _VIETNAMESE_MAP[m.group(0)], text)

    # Bước 3: Bỏ dấu bằng unicodedata
    text = unicodedata.normalize('NFD', text)

    # Bỏ các ký tự dấu (combining characters)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    text = text.strip()

    return text

def safe_float_or_none(value):
    """Convert sang float, nếu không được thì trả về None"""
    if pd.isna(value):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def format_minutes(hours):
    """Convert số giờ (float) thành chuỗi 'XhYp'. VD: 8.67 -> '8h40p', 4.33 -> '4h20p'"""
    if hours is None:
        return "0p"
    total_min = round(float(hours) * 60)
    h = total_min // 60
    m = total_min % 60
    if h == 0:
        return f"{m}p"
    if m == 0:
        return f"{h}h"
    return f"{h}h{m}p"