from tangca import get_tangca_info
from bangcong import get_bangcong_info
from thongke import get_chamcong_info, get_thu_ngay
from calam import parse_ca_lam
from common import remove_accents, format_minutes


NGHI_TOI_DA = 5
KEY_TONG_QUAN = "_tong"


def format_ca(ca_in, ca_out):
    """Format cặp giờ vào-ra của ca làm thành chuỗi 'X.XXh - Y.YYh'."""
    return f"{ca_in:.2f}h - {ca_out:.2f}h"


def co_cham_cong_may(time):
    """Kiểm tra time (in/out từ máy) có phải là chấm công hợp lệ không."""
    if not isinstance(time, (list, tuple)) or len(time) < 2:
        return False
    cc_in, cc_out = time
    if not isinstance(cc_in, (int, float)) or not isinstance(cc_out, (int, float)):
        return False
    if time == "V" or time == "Off" or time == "NaN" or time == "P":
        return False
    return cc_in > 0 and cc_out > 0


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
    - Quên checkin (cc_in NaN, có cc_out) / Quên checkout (cc_out NaN, có cc_in)
      → phân biệt rõ ràng.
    - Khi ca_lam=None (không tìm được ca) → fallback ca mặc định 9.00-17.00
      để vẫn phát hiện đi muộn/về sớm/làm thiếu.
    """
    issues = []

    if ca_lam is None:
        if bangcong_gio is None or bangcong_gio == 0:
            if not isinstance(chamcong, (list, tuple)) or len(chamcong) < 2:
                return []
            cc_in, cc_out = chamcong
            if cc_in == "NaN" and cc_out == "NaN":
                return []
            if cc_in == "NaN" and isinstance(cc_out, (int, float)) and cc_out > 0:
                return [f"BC=0h nhưng máy ghi checkout={cc_out:.2f}h - có vẻ QUÊN CHECKIN"]
            if cc_out == "NaN" and isinstance(cc_in, (int, float)) and cc_in > 0:
                return [f"BC=0h nhưng máy ghi checkin={cc_in:.2f}h - có vẻ QUÊN CHECKOUT"]
            if cc_in in ("V", "Off") or cc_out in ("V", "Off"):
                if tangca_gio > 0:
                    return [f"Máy ghi vắng, BC=0h nhưng ghi tăng ca = {tangca_gio}h"]
                else:
                    return []
            if isinstance(cc_in, (int, float)) and isinstance(cc_out, (int, float)) and cc_in > 0 and cc_out > cc_in:
                return [f"BC=0h (nghỉ) nhưng máy ghi ({cc_in:.2f}, {cc_out:.2f})"]
            return []

        if not isinstance(chamcong, (list, tuple)) or len(chamcong) < 2:
            return [f"BC={bangcong_gio}h nhưng không có chấm công máy"]

        cc_in, cc_out = chamcong

        if cc_in in ("V", "Off") or cc_out in ("V", "Off"):
            return [f"Máy ghi vắng nhưng BC={bangcong_gio}h"]

        if cc_in == "NaN" or cc_out == "NaN":
            if cc_in == "NaN" and isinstance(cc_out, (int, float)) and cc_out > 0:
                return [f"BC={bangcong_gio}h nhưng máy chỉ ghi checkout={cc_out:.2f}h - có vẻ QUÊN CHECKIN"]
            if cc_out == "NaN" and isinstance(cc_in, (int, float)) and cc_in > 0:
                return [f"BC={bangcong_gio}h nhưng máy chỉ ghi checkin={cc_in:.2f}h - có vẻ QUÊN CHECKOUT"]
            return [f"Máy không ghi nhận được giờ nhưng BC={bangcong_gio}h"]

        if not isinstance(cc_in, (int, float)) or not isinstance(cc_out, (int, float)):
            return [f"Chấm công không hợp lệ: {chamcong}"]

        if cc_out <= cc_in:
            return [f"Chấm công vào/ra không hợp lệ: ({cc_in}, {cc_out})"]

        # Không xác định được ca → fallback 9-17 để vẫn phát hiện đi muộn/về sớm/làm thiếu
        ca_lam = (9.0, 17.0)

    if bangcong_gio is None:
        return [f"BC=None, máy={chamcong}"]

    if not isinstance(chamcong, (list, tuple)) or len(chamcong) < 2:
        return [f"BC={bangcong_gio}h nhưng không có chấm công máy"]

    cc_in, cc_out = chamcong

    if cc_in in ("V", "Off") or cc_out in ("V", "Off"):
        return [f"Máy ghi vắng ({cc_in}) nhưng BC={bangcong_gio}h"] if bangcong_gio > 0 else []

    if cc_in == "NaN" or cc_out == "NaN":
        if cc_in == "NaN" and isinstance(cc_out, (int, float)) and cc_out > 0:
            return [f"BC={bangcong_gio}h nhưng máy chỉ ghi checkout={cc_out:.2f}h - có vẻ QUÊN CHECKIN"]
        if cc_out == "NaN" and isinstance(cc_in, (int, float)) and cc_in > 0:
            return [f"BC={bangcong_gio}h nhưng máy chỉ ghi checkin={cc_in:.2f}h - có vẻ QUÊN CHECKOUT"]
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
        issues.append(f"Đi muộn {format_minutes(cc_in - ca_in)} (vào {cc_in:.2f}h, ca {format_ca(ca_in, ca_out)})")

    if cc_out < ca_out:
        issues.append(f"Về sớm {format_minutes(ca_out - cc_out)} (ra {cc_out:.2f}h, ca {format_ca(ca_in, ca_out)})")

    cc_duration = cc_out - cc_in
    # ca_duration = ca_out - ca_in
    if cc_duration < bangcong_gio:
        issues.append(f"Làm thiếu {format_minutes(bangcong_gio - cc_duration)} so với bảng công {bangcong_gio} (máy={format_minutes(cc_duration)}, ca={bangcong_gio})")

    tc = tangca_gio or 0
    tong_ghi = bangcong_gio + tc
    diff_tong = cc_duration - tong_ghi
    if diff_tong < 0:
        issues.append(f"Máy < BC+TC: máy={format_minutes(cc_duration)}, BC={format_minutes(bangcong_gio)}, TC={format_minutes(tc)}, BC+TC={format_minutes(tong_ghi)} (thiếu {format_minutes(abs(diff_tong))} - ghi nhiều hơn thực tế)")

    if tc > 0 and ca_in <= cc_in and cc_out <= ca_out:
        issues.append(f"Ghi TC={tc}h nhưng giờ máy ({cc_in:.2f}-{cc_out:.2f}h) nằm trong ca ({format_ca(ca_in, ca_out)})")

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
    if not calam_info:
        return {}
    result = {}
    for nhanvien, time_in_out in thongke_info.items():
        issues = {}
        bangcong_info_item = bangcong_info.get(nhanvien)
        tangca_info_item = tangca_info.get(nhanvien)
        if not bangcong_info_item:
            issues[KEY_TONG_QUAN] = [
                f"Không tìm thấy bảng công cho {nhanvien}"
            ]
            result[nhanvien] = issues
            continue

        so_ngay_nghi_bc = 0
        ngay_nghi_list_bc = []

        so_ngay_nghi_cc = 0
        ngay_nghi_list_cc = []

        for day, time in time_in_out.items():
            thu = thu_ngay[day - 1][1]
            calam_info_item = calam_info.get(thu)
            print(f"{thu} : {calam_info_item}")
            calam_true = xac_dinh_ca_lam(time, calam_info_item)
            bangcong_day = bangcong_info_item[day]
            tangca_day = tangca_info_item.get(day) or 0 if tangca_info_item else 0
            sai_sot = phat_hien_sai_sot(bangcong_day, time, tangca_day, calam_true)
            if sai_sot:
                issues[day] = sai_sot

            if bangcong_day == 0:
                so_ngay_nghi_bc += 1
                ngay_nghi_list_bc.append(day)
            if not co_cham_cong_may(time):
                so_ngay_nghi_cc += 1
                ngay_nghi_list_cc.append(day)

        if so_ngay_nghi_bc > NGHI_TOI_DA:
            issues.setdefault(KEY_TONG_QUAN, []).append(
                f"Nghỉ bảng công {so_ngay_nghi_bc} ngày trong tháng (vượt ngưỡng {NGHI_TOI_DA} ngày): {sorted(ngay_nghi_list_bc)}"
            )
        if so_ngay_nghi_cc > NGHI_TOI_DA:
            issues.setdefault(KEY_TONG_QUAN, []).append(
                f"Nghỉ chấm công {so_ngay_nghi_cc} ngày trong tháng (vượt ngưỡng {NGHI_TOI_DA} ngày): {sorted(ngay_nghi_list_cc)}"
            )

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
        if KEY_TONG_QUAN in issues:
            for s in issues[KEY_TONG_QUAN]:
                print(f"  [TỔNG QUAN] {s}")
            del issues[KEY_TONG_QUAN]
        for day, sai_sot in issues.items():
            print(f"  Ngày {day}:")
            for s in sai_sot:
                print(f"    - {s}")
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
        in_bao_cao(filename)