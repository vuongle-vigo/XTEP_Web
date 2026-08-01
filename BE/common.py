import unicodedata
import re
import pandas as pd 
def remove_accents(text):
    """Chuyển thành chữ thường, không dấu"""
    if not isinstance(text, str):
        return text
    
    # Bước 1: Chuyển về chữ thường
    text = text.lower()
    
    # Bước 2: Bỏ dấu bằng unicodedata
    # NFD tách ký tự và dấu ra riêng
    text = unicodedata.normalize('NFD', text)
    
    # Bỏ các ký tự dấu (combining characters)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    return text

def safe_float_or_none(value):
    """Convert sang float, nếu không được thì trả về None"""
    if pd.isna(value):
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None