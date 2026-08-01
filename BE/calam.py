import pandas as pd
from datetime import datetime
import json
import re 

DAY_MAP = {
    "T2": 0, "T3": 1, "T4": 2, "T5": 3,
    "T6": 4, "T7": 5, "CN": 6
}

DAY_NAMES = {v: k for k, v in DAY_MAP.items()}

def time_to_float(time_text):
    return round(datetime.strptime(time_text.strip(), '%H:%M').hour + datetime.strptime(time_text.strip(), '%H:%M').minute / 60, 3)

def format_time_to_float(time_text):
    """Tách ca '9:00 - 17:00' thành (9.0, 17.0)"""
    return time_to_float(time_text.split(' - ')[0]), time_to_float(time_text.split(' - ')[1])

def parse_day_range(day_str):
    """Parse 'T2 - T6' -> [0, 1, 2, 3, 4]"""
    days = []
    segments = day_str.split(',')
    
    for segment in segments:
        segment = segment.strip()
        if ' - ' in segment:
            parts = segment.split(' - ')
            start_day = parts[0].strip()
            end_day = parts[1].strip()
            if start_day in DAY_MAP and end_day in DAY_MAP:
                start_idx = DAY_MAP[start_day]
                end_idx = DAY_MAP[end_day]
                days.extend(range(start_idx, end_idx + 1))
        else:
            if segment in DAY_MAP:
                days.append(DAY_MAP[segment])
    
    return sorted(set(days))

def parse_schedule(text):
    """
    Parse text ca làm việc -> dict {weekday: [(start, end), ...]}
    """
    schedule = {i: [] for i in range(7)}
    current_days = list(range(7))  # Mặc định áp dụng tất cả ngày
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Kiểm tra dòng có chứa ngày không (T2 - T6:)
        day_match = re.match(r'^((?:T[2-7]|CN)\s*-\s*(?:T[2-7]|CN))(?:\s*-\s*(?:T[2-7]|CN))*\s*:', line)
        
        if day_match:
            # Tách phần ngày và phần giờ
            colon_idx = line.index(':')
            days_part = line[:colon_idx].strip()
            hours_part = line[colon_idx+1:].strip()
            current_days = parse_day_range(days_part)
            line_to_parse = hours_part
        else:
            line_to_parse = line
        
        # Parse các ca trong dòng (nếu có)
        if line_to_parse:
            shifts = re.findall(r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})', line_to_parse)
            for shift in shifts:
                start, end = format_time_to_float(shift)
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
        print(ten_cua_hang)
        ca_lam = ca_lams[i]
        shifts = ca_lam.strip().split('\n')
        ca_lam_dict[ten_cua_hang] = parse_schedule(ca_lam)

    with open('ca_lam_dict.json', 'w', encoding='utf-8') as f:
        json.dump(ca_lam_dict, f, ensure_ascii=False, indent=2)
    
    return ca_lam_dict
