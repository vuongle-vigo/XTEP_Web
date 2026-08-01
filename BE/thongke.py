import pandas as pd
import json
from calam import DAY_MAP, time_to_float
from common import remove_accents

SHEET_NAME = "ThongKe"
COL_START_NGAY = 4
ROW_START_NGAY = 4

COL_START_THU = 4
ROW_START_THU = 5

COL_START_CHAMCONG = 4
ROW_START_CHAMCONG = 7

def get_thu_ngay(filename):
    df = pd.read_excel(filename, sheet_name="ThongKe")
    thu_ngay = []
    for i in range(COL_START_THU, COL_START_THU + 31):
        thu = df.iloc[ROW_START_THU, i]
        ngay = df.iloc[ROW_START_NGAY, i]
        if thu not in DAY_MAP.keys():
            break
        thu_ngay.append((ngay, DAY_MAP[thu]))
    return thu_ngay

def get_chamcong_info(filename):
    df = pd.read_excel(filename, sheet_name=SHEET_NAME)
    nhanvien_col = df.iloc[:, 2].dropna()
    nhanvien = []

    for nhanvien_item in nhanvien_col[1:]:
        nhanvien.append(remove_accents(nhanvien_item))

    thu_ngay = get_thu_ngay(filename)
    chamcong_info = {}
    for index, nhanvien_item in enumerate(nhanvien):
        chamcong = {}
        for i in range(COL_START_CHAMCONG, COL_START_CHAMCONG + len(thu_ngay)):
            checkin = df.iloc[ROW_START_CHAMCONG + index * 2, i]
            checkout = df.iloc[ROW_START_CHAMCONG + index * 2 + 1, i]
            if not pd.isna(checkin) and checkin != "V" and checkin != "Off":
                checkin = time_to_float(checkin)
            if not pd.isna(checkout):
                checkout = time_to_float(checkout)
            if pd.isna(checkin):
                checkin = "NaN"
            if pd.isna(checkout):
                checkout = "NaN"
            if checkin == "V" or checkin == "Off":
                checkout = checkin
            chamcong[thu_ngay[i-COL_START_CHAMCONG][0]] = (checkin, checkout)  
        chamcong_info[nhanvien_item] = chamcong
    return chamcong_info

data = get_chamcong_info('1. ROYAL.xlsx')
with open('chamcong_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
