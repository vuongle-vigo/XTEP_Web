import pandas as pd
import json
from common import remove_accents, safe_float_or_none
from thongke import get_thu_ngay
from calam import DAY_MAP

SHEET_NAME = "TĂNG CA"

COL_NAME =  1
ROW_START_DATA = 4
COL_START_DATA = 3

def get_tangca_info(filename):
    df = None
    file = pd.ExcelFile(filename)
    for sheet_name in file.sheet_names:
        if sheet_name.strip() == SHEET_NAME:
            df = pd.read_excel(file, sheet_name=sheet_name)

    nhanvien = []
    index = 0
    while True:
        nhanvien_item = df.iloc[ROW_START_DATA + index, COL_NAME]
        if pd.isna(nhanvien_item):
            break
        nhanvien.append(remove_accents(nhanvien_item))
        index += 1

    thu_ngay = get_thu_ngay(filename)
    tangca_info = {}

    for index, nhanvien_item in enumerate(nhanvien):
        tangca = {}
        for i in range(COL_START_DATA, COL_START_DATA + len(thu_ngay)):
            hour = df.iloc[ROW_START_DATA + index, i]
            hour = safe_float_or_none(hour)
            if hour is None:
                hour = 0
            if hour > 0:
                tangca[thu_ngay[i-COL_START_DATA][0]] = hour
        tangca_info[nhanvien_item] = tangca
    return tangca_info

tangca_info = get_tangca_info('1. ROYAL.xlsx')
with open('tangca_info.json', 'w') as f:
    json.dump(tangca_info, f, indent=4)
