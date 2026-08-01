from tangca import get_tangca_info
from bangcong import get_bangcong_info
from thongke import get_chamcong_info, get_thu_ngay
from calam import parse_ca_lam
from common import remove_accents


def xac_dinh_ca_lam(cham_cong, ca_lam_list):
    """Tìm ca làm có tổng lệch giờ vào/ra nhỏ nhất."""
    if not isinstance(cham_cong, (list, tuple)) or len(cham_cong) < 2:
        return None
    
    cc_in, cc_out = cham_cong
    
    if not isinstance(cc_in, (int, float)) or not isinstance(cc_out, (int, float)):
        return None
    if cc_out <= cc_in:
        return None
    if not ca_lam_list:
        return None
    
    best_ca = None
    min_diff = float('inf')
    
    for ca in ca_lam_list:
        if not isinstance(ca, (list, tuple)) or len(ca) < 2:
            continue
        ca_in, ca_out = ca
        if not isinstance(ca_in, (int, float)) or not isinstance(ca_out, (int, float)):
            continue
        
        # diff = abs(cc_in - ca_in) + abs(cc_out - ca_out)
        diff = abs(cc_in - ca_in)
        
        if diff < min_diff:
            min_diff = diff
            best_ca = ca
    
    return best_ca


def phat_hien_sai_sot(bangcong_gio, chamcong, tangca_gio, ca_lam):
    """
    Phát hiện SAI SÓT gây thiệt hại cho công ty.
    - Lệch 1 phút cũng báo (không tolerance)
    - Vào sớm / Ra trễ / Làm thừa → KHÔNG phải sai sót
    - Máy > BC+TC → KHÔNG phải sai sót (NV làm thêm, chưa ghi TC = user tự xử)
    - Chỉ báo khi máy < BC+TC (NV ghi nhiều hơn thực tế → thiệt hại công ty)
    """
    issues = []
    
    if ca_lam is None:
        if bangcong_gio is None or bangcong_gio == 0:
            return []
        
        if not isinstance(chamcong, (list, tuple)) or len(chamcong) < 2:
            return [f"BC={bangcong_gio}h nhưng không có chấm công máy"]
        
        cc_in, cc_out = chamcong
        
        if cc_in in ("V", "Off") or cc_out in ("V", "Off"):
            return [f"Máy ghi vắng nhưng BC={bangcong_gio}h"]
        
        if not isinstance(cc_in, (int, float)) or not isinstance(cc_out, (int, float)):
            return [f"Chấm công không hợp lệ: {chamcong}"]
        
        if cc_out <= cc_in:
            return [f"Chấm công vào/ra không hợp lệ: ({cc_in}, {cc_out})"]
        
        issues.append(f"Không xác định được ca làm (CC: {cc_in:.2f}-{cc_out:.2f}h)")
        
        cc_duration = cc_out - cc_in
        tc = tangca_gio or 0
        tong_ghi = bangcong_gio + tc
        diff = cc_duration - tong_ghi
        
        if diff < 0:
            issues.append(f"Máy={cc_duration*60:.0f}p < BC+TC={tong_ghi*60:.0f}p (thiếu {abs(diff)*60:.0f}p)")
        
        return issues
    
    if bangcong_gio is None:
        return [f"BC=None, máy={chamcong}"]
    
    if not isinstance(chamcong, (list, tuple)) or len(chamcong) < 2:
        return [f"BC={bangcong_gio}h nhưng không có chấm công máy"]
    
    cc_in, cc_out = chamcong
    
    if cc_in in ("V", "Off") or cc_out in ("V", "Off"):
        return [f"Máy ghi vắng ({cc_in}) nhưng BC={bangcong_gio}h"] if bangcong_gio > 0 else []
    
    if cc_in == "NaN" or cc_out == "NaN":
        return [f"Máy không ghi nhận được giờ nhưng BC={bangcong_gio}h"] if bangcong_gio > 0 else []
    
    if not isinstance(cc_in, (int, float)) or not isinstance(cc_out, (int, float)):
        return [f"Chấm công không hợp lệ: {chamcong}"]
    
    if cc_out <= cc_in:
        return [f"CC vào/ra không hợp lệ: ({cc_in}, {cc_out})"]
    
    ca_in, ca_out = ca_lam
    
    if bangcong_gio == 0:
        if cc_in > 0 or cc_out > 0:
            issues.append(f"BC=0h (nghỉ) nhưng máy ghi ({cc_in:.2f}, {cc_out:.2f})")
        return issues
    
    if cc_in > ca_in:
        issues.append(f"Đi muộn {(cc_in - ca_in) * 60:.0f}p (vào {cc_in:.2f}h, ca {ca_in:.2f}h)")
    
    if cc_out < ca_out:
        issues.append(f"Về sớm {(ca_out - cc_out) * 60:.0f}p (ra {cc_out:.2f}h, ca {ca_out:.2f}h)")
    
    cc_duration = cc_out - cc_in
    ca_duration = ca_out - ca_in
    if cc_duration < ca_duration:
        issues.append(f"Làm thiếu {(ca_duration - cc_duration) * 60:.0f}p so với ca (máy={cc_duration*60:.0f}p, ca={ca_duration*60:.0f}p)")
    
    tc = tangca_gio or 0
    tong_ghi = bangcong_gio + tc
    diff_tong = cc_duration - tong_ghi
    
    if diff_tong < 0:
        issues.append(f"Máy < BC+TC: máy={cc_duration*60:.0f}p, BC+TC={tong_ghi*60:.0f}p (thiếu {abs(diff_tong)*60:.0f}p - ghi nhiều hơn thực tế)")
    
    if tc > 0 and ca_in <= cc_in and cc_out <= ca_out:
        issues.append(f"Ghi TC={tc}h nhưng giờ máy ({cc_in:.2f}-{cc_out:.2f}h) nằm trong ca ({ca_in:.2f}-{ca_out:.2f}h)")
    
    return issues


def lay_calam_theo_filename(filename, ca_lam_dict):
    """Tìm ca làm tương ứng với tên file (theo tên cửa hàng)."""
    filename_norm = remove_accents(filename)
    for cuahang, calam in ca_lam_dict.items():
        if remove_accents(cuahang) in filename_norm:
            return calam
    return {}


def kiem_tra_bang_cong(filename, calamfile='ca_lam_xtep.xlsx'):
    """
    Kiểm tra bảng công cho 1 file cửa hàng.
    
    Args:
        filename: tên file bảng công (vd '1. ROYAL.xlsx')
        calamfile: file ca làm (mặc định 'ca_lam_xtep.xlsx')
    
    Returns:
        dict: {nhanvien: {day: [list_issues]}}
    """
    thu_ngay = get_thu_ngay(filename)
    tangca_info = get_tangca_info(filename)
    bangcong_info = get_bangcong_info(filename)
    thongke_info = get_chamcong_info(filename)
    ca_lam_dict = parse_ca_lam(calamfile)
    calam_info = lay_calam_theo_filename(filename, ca_lam_dict)
    
    result = {}
    for nhanvien, time_in_out in thongke_info.items():
        issues = {}
        bangcong_info_item = bangcong_info.get(nhanvien)
        tangca_info_item = tangca_info.get(nhanvien)
        if not bangcong_info_item:
            continue
        # if nhanvien != "tran phuc trung":
        #     continue
        # print(f"time_in_out: {time_in_out}")
        for day, time in time_in_out.items():
            thu = thu_ngay[day - 1][1]
            calam_info_item = calam_info.get(thu)
            calam_true = xac_dinh_ca_lam(time, calam_info_item)
            # print(f"calam_true: {calam_true}")
            bangcong_day = bangcong_info_item[day]
            tangca_day = tangca_info_item.get(day) or 0
            
            sai_sot = phat_hien_sai_sot(bangcong_day, time, tangca_day, calam_true)
            if sai_sot:
                issues[day] = sai_sot
        
        if issues:
            result[nhanvien] = issues
    
    return result


def in_bao_cao(filename, result=None):
    """In báo cáo ra console."""
    if result is None:
        result = kiem_tra_bang_cong(filename)
    
    print(f"\n=== Báo cáo: {filename} ===")
    for nhanvien, issues in result.items():
        print(f"\n--- {nhanvien} ---")
        for day, sai_sot in issues.items():
            print(f"  Ngày {day}:")
            for s in sai_sot:
                print(f"    - {s}")
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '1. ROYAL.xlsx'
    
    in_bao_cao(filename)