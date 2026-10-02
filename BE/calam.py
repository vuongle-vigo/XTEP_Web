import pandas as pd
from datetime import datetime, time as datetime_time
import json
import re

DAY_MAP = {
    "T2": 0, "T3": 1, "T4": 2, "T5": 3,
    "T6": 4, "T7": 5, "CN": 6
}

DAY_NAMES = {v: k for k, v in DAY_MAP.items()}

def time_to_float(time_text):
    """Chuyển giờ ('7:30' hoặc datetime.time) -> float (7.5).

    Ô chứa chuỗi không phải 1 giờ đơn lẻ (vd '8:00-16:00', 'V', text lỗi)
    -> trả về None thay vì raise ValueError.
    """
    if isinstance(time_text, datetime_time):
        return round(time_text.hour + time_text.minute / 60, 3)
    if not isinstance(time_text, str):
        return None
    try:
        t = datetime.strptime(time_text.strip(), '%H:%M')
    except ValueError:
        return None
    return round(t.hour + t.minute / 60, 3)

def format_time_to_float(time_text):
    """Tách ca '9:00 - 17:00' thành (9.0, 17.0). Chấp nhận '9:00-17:00' (thiếu space)."""
    parts = re.split(r'\s*-\s*', time_text.strip())
    if len(parts) != 2:
        return None, None
    return time_to_float(parts[0]), time_to_float(parts[1])

DAY_TOKEN_RE = re.compile(r'\b(T[2-7]|CN)\b')

def parse_day_range(day_str):
    """Parse nhóm ngày -> danh sách weekday.

    VD: 'T2 - T6' -> [0, 1, 2, 3, 4]
        'T7 - CN - Ngày lễ' -> [5, 6]
        'T2, T4 - T6' -> [0, 2, 3, 4]

    Từ không phải mã thứ (vd 'Ngày lễ') bị bỏ qua. Trong 1 đoạn (tách bằng ','),
    token đầu và token cuối được hiểu là đầu-cuôi của dải ngày.
    """
    days = []
    for segment in day_str.split(','):
        tokens = DAY_TOKEN_RE.findall(segment)
        if not tokens:
            continue
        start_idx = DAY_MAP[tokens[0]]
        end_idx = DAY_MAP[tokens[-1]]
        lo, hi = min(start_idx, end_idx), max(start_idx, end_idx)
        days.extend(range(lo, hi + 1))
    return sorted(set(days))

def parse_schedule(text):
    """
    Parse text ca làm việc -> dict {weekday: [(start, end), ...]}.

    Định dạng mẫu:
        T2 - T6:
        9:00 - 17:00
        14:00 - 22:00
        T7 - CN - Ngày lễ:
        8:30 - 16:30
        14:00 - 22:00

    - Dòng nhóm ngày chứa mã thứ (T2..T7, CN) và dấu ':' (giờ có thể nằm ngay
      sau ':' hoặc ở các dòng tiếp theo). Từ khác trong nhóm ('Ngày lễ'...) bỏ qua.
    - Ca áp dụng cho nhóm ngày gần nhất phía trên; nếu chưa có nhóm nào
      thì áp dụng cho cả tuần.
    """
    schedule = {i: [] for i in range(7)}
    current_days = list(range(7))  # Mặc định áp dụng tất cả ngày

    for raw_line in text.strip().split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        head, sep, tail = line.partition(':')
        if sep and DAY_TOKEN_RE.search(head):
            current_days = parse_day_range(head)
            line_to_parse = tail.strip()
        else:
            line_to_parse = line

        # Parse các ca trong dòng (nếu có)
        if line_to_parse:
            shifts = re.findall(r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})', line_to_parse)
            for shift in shifts:
                start, end = format_time_to_float(shift)
                if start is None or end is None:
                    continue
                for day in current_days:
                    schedule[day].append((start, end))

    return schedule

def parse_ca_lam(filename):
    df = pd.read_excel(filename, sheet_name="Sheet1")

    ten_cua_hangs = df.iloc[:, 0]  # Cột 1
    ca_lams = df.iloc[:, 1]  # Cột 2

    ca_lam_dict = {}
    for i in range(len(ten_cua_hangs)):
        ten_cua_hang = ten_cua_hangs[i]
        ca_lam = ca_lams[i]
        shifts = ca_lam.strip().split('\n')
        ca_lam_dict[ten_cua_hang] = parse_schedule(ca_lam)

    with open('ca_lam_dict.json', 'w', encoding='utf-8') as f:
        json.dump(ca_lam_dict, f, ensure_ascii=False, indent=2)
    
    return ca_lam_dict
