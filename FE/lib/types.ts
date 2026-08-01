// Shared types for the XTEP Check Cong webapp
// Phản ánh output của BE/api.py

export type ChamCongValue = number | "V" | "Off" | "NaN";

export type ChamCongPair = [ChamCongValue, ChamCongValue];

export type BangCongMap = Record<string, number>;
export type TangCaMap = Record<string, number>;
export type ChamCongMap = Record<string, ChamCongPair>;
export type ThuNgayItem = [number, string]; // [ngay, thu]

export interface UploadedFile {
  filename: string;
  size: number;
  uploaded_at: string;
  has_ca_lam_info: boolean;
}

export interface IssueSummary {
  total_issues: number;
  employees_with_issues: number;
  days_with_issues: number;
  issue_types: {
    di_muon: number;
    ve_som: number;
    lam_thieu: number;
    may_thieu_bc_tc: number;
    tc_trong_ca: number;
    khac: number;
  };
}

export interface CheckResult {
  filename: string;
  summary: IssueSummary;
  details: Record<string, Record<string, string[]>>;
}

export interface RawData {
  bangcong: Record<string, BangCongMap>;
  tangca: Record<string, TangCaMap>;
  chamcong: Record<string, ChamCongMap>;
  thu_ngay: ThuNgayItem[];
}

export interface SystemInfo {
  upload_dir: string;
  base_dir: string;
  has_ca_lam_file: boolean;
  day_map: Record<string, number>;
}

// Frontend issue classification
export type IssueCategory =
  | "di_muon"
  | "ve_som"
  | "lam_thieu"
  | "may_thieu_bc_tc"
  | "tc_trong_ca"
  | "khac";

export interface CategorizedIssue {
  text: string;
  category: IssueCategory;
}

export const CATEGORY_META: Record<
  IssueCategory,
  { label: string; color: string; bg: string; ring: string; icon: string }
> = {
  di_muon: {
    label: "Đi muộn",
    color: "text-amber-700",
    bg: "bg-amber-50",
    ring: "ring-amber-200",
    icon: "⏰",
  },
  ve_som: {
    label: "Về sớm",
    color: "text-orange-700",
    bg: "bg-orange-50",
    ring: "ring-orange-200",
    icon: "🏃",
  },
  lam_thieu: {
    label: "Làm thiếu giờ",
    color: "text-purple-700",
    bg: "bg-purple-50",
    ring: "ring-purple-200",
    icon: "⏳",
  },
  may_thieu_bc_tc: {
    label: "Máy < BC+TC",
    color: "text-red-700",
    bg: "bg-red-50",
    ring: "ring-red-200",
    icon: "🚨",
  },
  tc_trong_ca: {
    label: "TC nằm trong ca",
    color: "text-pink-700",
    bg: "bg-pink-50",
    ring: "ring-pink-200",
    icon: "📝",
  },
  khac: {
    label: "Khác",
    color: "text-slate-700",
    bg: "bg-slate-50",
    ring: "ring-slate-200",
    icon: "⚠️",
  },
};

export function categorizeIssue(text: string): IssueCategory {
  const il = text.toLowerCase();
  if (il.includes("đi muộn")) return "di_muon";
  if (il.includes("về sớm")) return "ve_som";
  if (il.includes("làm thiếu")) return "lam_thieu";
  if (il.includes("máy < bc+tc")) return "may_thieu_bc_tc";
  if (il.includes("ghi tc")) return "tc_trong_ca";
  return "khac";
}

export function formatHour(value: number | string | undefined): string {
  if (value === undefined || value === null) return "—";
  if (typeof value === "string") return value;
  if (isNaN(value)) return "—";
  const h = Math.floor(value);
  const m = Math.round((value - h) * 60);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

// Match kiểu "giờ thực" = số có phần thập phân >= 2 chữ số (vd 14.77h, 21.5h không match).
// Tránh convert nhầm "số tiếng" dạng 6.0h, 8.0h (TC=, BC=, máy=...).
// Giữ nguyên định dạng "HhMp" (vd 7h14p, 8h) - đã dễ đọc.
function convertHourTokenToHHMM(match: string): string {
  const num = parseFloat(match);
  if (!isFinite(num)) return match;
  const h = Math.floor(num);
  const m = Math.round((num - h) * 60);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

export function formatIssueText(text: string): string {
  if (!text) return text;
  // Match theo thứ tự ưu tiên: range "14.77-22.00h" -> "14:46-22:00"
  // (regex range phải đứng trước regex đơn để tránh nuốt 2 số riêng)
  let out = text.replace(/(\d{1,2}\.\d{2})-(\d{1,2}\.\d{2})h/g, (_full, a, b) => {
    return `${convertHourTokenToHHMM(a)}-${convertHourTokenToHHMM(b)}`;
  });
  // Match giờ đơn "14.77h" -> "14:46" (chỉ khi có >= 2 chữ số thập phân)
  out = out.replace(/(\d{1,2}\.\d{2})h/g, (_full, num) => {
    return convertHourTokenToHHMM(num);
  });
  return out;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(iso: string | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function dayNameVi(thu: string): string {
  const map: Record<string, string> = {
    T2: "Thứ 2",
    T3: "Thứ 3",
    T4: "Thứ 4",
    T5: "Thứ 5",
    T6: "Thứ 6",
    T7: "Thứ 7",
    CN: "Chủ nhật",
  };
  return map[thu] || thu;
}
