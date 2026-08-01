import pandas as pd
import json
from calam import DAY_MAP, time_to_float
from common import remove_accents, safe_float_or_none
from datetime import datetime
from thongke import get_thu_ngay

SHEET_NAME = "BẢNG CÔNG"

ROW_START_DATA = 4
COL_START_DATA = 3
COL_NAME = 1

COL_START_NGAY = 3
COL_START_THU = 3

ROW_START_NGAY = 2
ROW_START_THU = 3

def get_bangcong_info(filename):
    df = None

    file = pd.ExcelFile(filename)
    for sheet_name in file.sheet_names:
        if sheet_name.strip() == SHEET_NAME:
            df = pd.read_excel(filename, sheet_name=sheet_name)

    nhanvien = []
    index = 0
    while True:
        nhanvien_item = df.iloc[ROW_START_DATA + index, COL_NAME]
        if pd.isna(nhanvien_item):
            break
        nhanvien.append(remove_accents(nhanvien_item))
        index += 1

    thu_ngay = get_thu_ngay(filename)
    bangcong_info = {}

    for index, nhanvien_item in enumerate(nhanvien):
        bangcong = {}
        for i in range(COL_START_DATA, COL_START_DATA + len(thu_ngay)):
            hour_work = df.iloc[ROW_START_DATA + index, i]
            hour_work = safe_float_or_none(hour_work)
            if hour_work is None:
                hour_work = 0
            bangcong[thu_ngay[i-COL_START_DATA][0]] = hour_work

        bangcong_info[nhanvien_item] = bangcong
    return bangcong_info

bangcong_info = get_bangcong_info('1. ROYAL.xlsx')
with open('bangcong_info.json', 'w') as f:
    json.dump(bangcong_info, f, indent=4)