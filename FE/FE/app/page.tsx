"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { UploadZone } from "@/components/upload-zone";
import {
  UploadedFile,
  CheckResult,
  IssueSummary,
  CATEGORY_META,
  IssueCategory,
  categorizeIssue,
  formatBytes,
  formatDateTime,
  formatIssueText,
} from "@/lib/types";
import {
  FileSpreadsheet,
  AlertTriangle,
  Users,
  TrendingUp,
  Trash2,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Loader2,
  Search,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

function emptySummary(): IssueSummary {
  return {
    total_issues: 0,
    employees_with_issues: 0,
    days_with_issues: 0,
    issue_types: {
      di_muon: 0,
      ve_som: 0,
      lam_thieu: 0,
      may_thieu_bc_tc: 0,
      tc_trong_ca: 0,
      khac: 0,
    },
  };
}

export default function HomePage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [checks, setChecks] = useState<Record<string, CheckResult | null>>({});
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [filterCat, setFilterCat] = useState<IssueCategory | "all">("all");
  const [search, setSearch] = useState("");
  const [expandedNVs, setExpandedNVs] = useState<Record<string, boolean>>({});
  const [selectedDay, setSelectedDay] = useState<Record<string, string | null>>(
    {}
  );
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = async () => {
    setLoadingFiles(true);
    try {
      const data = await api.listFiles();
      const sortedFiles = [...data.files].sort((a, b) =>
        a.filename.localeCompare(b.filename, "en", { numeric: false })
      );
      setFiles(sortedFiles);
      const map: Record<string, CheckResult | null> = {};
      await Promise.all(
        sortedFiles.map(async (f) => {
          try {
            map[f.filename] = await api.check(f.filename);
          } catch {
            map[f.filename] = null;
          }
        })
      );
      setChecks(map);
      if (sortedFiles.length > 0) {
        const firstWithIssues = sortedFiles.find(
          (f) => (map[f.filename]?.summary?.total_issues ?? 0) > 0
        );
        setSelected(firstWithIssues?.filename ?? sortedFiles[0].filename);
      } else {
        setSelected(null);
      }
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const aggregate = useMemo(() => {
    const s = emptySummary();
    Object.values(checks).forEach((r) => {
      if (!r) return;
      s.total_issues += r.summary.total_issues;
      s.employees_with_issues += r.summary.employees_with_issues;
      Object.entries(r.summary.issue_types).forEach(([k, v]) => {
        s.issue_types[k as IssueCategory] += v;
      });
    });
    s.days_with_issues = Object.values(checks).reduce(
      (acc, r) => acc + (r?.summary?.days_with_issues ?? 0),
      0
    );
    return s;
  }, [checks]);

  const selectedResult = selected ? checks[selected] : null;
  const selectedSummary = selectedResult?.summary;

  const filteredEmployees = useMemo(() => {
    if (!selectedResult) return [];
    return Object.entries(selectedResult.details).filter(([nv, days]) => {
      if (search && !nv.toLowerCase().includes(search.toLowerCase()))
        return false;
      if (filterCat === "all") return true;
      return Object.values(days).some((issues) =>
        issues.some((i) => categorizeIssue(i) === filterCat)
      );
    });
  }, [selectedResult, search, filterCat]);

  const handleDelete = async (filename: string) => {
    if (!confirm(`Xóa file "${filename}"?`)) return;
    setDeleting(filename);
    try {
      await api.deleteFile(filename);
      if (selected === filename) setSelected(null);
      await load();
    } catch (e: any) {
      alert(`Lỗi: ${e.message}`);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/30">
          <Sparkles className="w-5 h-5 text-white" strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
            XTEP Check Công
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            Phát hiện sai sót chấm công tự động từ bảng công Excel
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={<FileSpreadsheet className="w-4 h-4" />}
          label="File đã upload"
          value={files.length}
          color="from-sky-500 to-blue-600"
          bg="bg-sky-50"
          text="text-sky-600"
          darkBg="dark:bg-sky-950/50"
          darkText="dark:text-sky-300"
        />
        <StatCard
          icon={<AlertTriangle className="w-4 h-4" />}
          label="Tổng sai sót"
          value={aggregate.total_issues}
          color="from-amber-500 to-orange-600"
          bg="bg-amber-50"
          text="text-amber-600"
          darkBg="dark:bg-amber-950/50"
          darkText="dark:text-amber-300"
        />
        <StatCard
          icon={<Users className="w-4 h-4" />}
          label="NV bị ảnh hưởng"
          value={aggregate.employees_with_issues}
          color="from-purple-500 to-pink-600"
          bg="bg-purple-50"
          text="text-purple-600"
          darkBg="dark:bg-purple-950/50"
          darkText="dark:text-purple-300"
        />
        <StatCard
          icon={<TrendingUp className="w-4 h-4" />}
          label="Thiệt hại (ghi nhiều)"
          value={aggregate.issue_types.may_thieu_bc_tc}
          color="from-red-500 to-rose-600"
          bg="bg-red-50"
          text="text-red-600"
          darkBg="dark:bg-red-950/50"
          darkText="dark:text-red-300"
        />
      </div>

      <UploadZone onUploaded={load} collapsed={files.length > 0} />

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4">
        {/* File list */}
        <div className="card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {files.length} file
            </div>
          </div>
          {loadingFiles ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin mx-auto text-brand-500" />
            </div>
          ) : files.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500 dark:text-slate-400">
              Chưa có file nào
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[600px] overflow-y-auto">
              {files.map((f) => {
                const c = checks[f.filename];
                const hasIssues = (c?.summary?.total_issues ?? 0) > 0;
                const isSelected = selected === f.filename;
                return (
                  <div
                    key={f.filename}
                    onClick={() => {
                      setSelected(f.filename);
                      setExpandedNVs({});
                      setSelectedDay({});
                    }}
                    className={cn(
                      "p-3 cursor-pointer transition-colors group",
                      isSelected
                        ? "bg-brand-50 border-l-4 border-brand-500 dark:bg-brand-500/15 dark:border-brand-400"
                        : "hover:bg-slate-50/60 border-l-4 border-transparent dark:hover:bg-slate-800/60"
                    )}
                  >
                    <div className="flex items-start gap-2">
                      <FileSpreadsheet
                        className={cn(
                          "w-4 h-4 mt-0.5 shrink-0",
                          isSelected
                            ? "text-brand-600 dark:text-brand-400"
                            : "text-emerald-600 dark:text-emerald-400"
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div
                          className={cn(
                            "text-sm font-medium truncate",
                            isSelected
                              ? "text-brand-700 dark:text-brand-300"
                              : "text-slate-900 dark:text-slate-100"
                          )}
                        >
                          {f.filename}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-2">
                          <span>{formatBytes(f.size)}</span>
                          <span>{formatDateTime(f.uploaded_at)}</span>
                        </div>
                        <div className="mt-1.5">
                          {c === undefined ? (
                            <span className="text-[10px] text-slate-400">
                              ...
                            </span>
                          ) : c === null ? (
                            <span className="badge-error text-[10px]">
                              Lỗi
                            </span>
                          ) : hasIssues ? (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-300 text-[10px] font-medium border border-red-200 dark:border-red-900/50">
                              <AlertTriangle className="w-2.5 h-2.5" />
                              {c.summary.total_issues} lỗi
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 text-[10px] font-medium border border-emerald-200 dark:border-emerald-900/50">
                              <CheckCircle2 className="w-2.5 h-2.5" />
                              Sạch
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(f.filename);
                        }}
                        disabled={deleting === f.filename}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-red-50 dark:hover:bg-red-950/50 text-red-600 dark:text-red-400"
                      >
                        {deleting === f.filename ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div className="space-y-4">
          {!selected ? (
            <div className="card p-12 text-center text-slate-500 dark:text-slate-400">
              <FileSpreadsheet className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-700" />
              <div className="mt-3 font-medium text-slate-900 dark:text-slate-100">
                Chọn file để xem chi tiết
              </div>
              <div className="text-sm mt-1">
                Hoặc upload file mới ở khu vực phía trên
              </div>
            </div>
          ) : !selectedResult ? (
            <div className="card p-12 text-center text-slate-500 dark:text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-brand-500" />
              <div className="mt-3">Đang phân tích {selected}...</div>
            </div>
          ) : (
            <FileDetail
              filename={selected}
              result={selectedResult}
              filterCat={filterCat}
              setFilterCat={setFilterCat}
              search={search}
              setSearch={setSearch}
              expandedNVs={expandedNVs}
              setExpandedNVs={setExpandedNVs}
              selectedDay={selectedDay}
              setSelectedDay={setSelectedDay}
              filteredEmployees={filteredEmployees}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ===== Sub-components =====

function StatCard({
  icon,
  label,
  value,
  color,
  bg,
  text,
  darkBg,
  darkText,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
  bg: string;
  text: string;
  darkBg: string;
  darkText: string;
}) {
  return (
    <div className="card p-4 hover:shadow-md transition-all">
      <div className="flex items-center justify-between">
        <div
          className={cn(
            "w-9 h-9 rounded-lg flex items-center justify-center",
            bg,
            text,
            darkBg,
            darkText
          )}
        >
          {icon}
        </div>
      </div>
      <div className="mt-2.5">
        <div className="text-2xl font-bold text-slate-900 dark:text-white">
          {value}
        </div>
        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 font-medium">
          {label}
        </div>
      </div>
      <div className={cn("mt-2.5 h-1 rounded-full bg-gradient-to-r", color)} />
    </div>
  );
}

function FileDetail({
  filename,
  result,
  filterCat,
  setFilterCat,
  search,
  setSearch,
  expandedNVs,
  setExpandedNVs,
  selectedDay,
  setSelectedDay,
  filteredEmployees,
}: {
  filename: string;
  result: CheckResult;
  filterCat: IssueCategory | "all";
  setFilterCat: (c: IssueCategory | "all") => void;
  search: string;
  setSearch: (s: string) => void;
  expandedNVs: Record<string, boolean>;
  setExpandedNVs: React.Dispatch<
    React.SetStateAction<Record<string, boolean>>
  >;
  selectedDay: Record<string, string | null>;
  setSelectedDay: React.Dispatch<
    React.SetStateAction<Record<string, string | null>>
  >;
  filteredEmployees: [string, Record<string, string[]>][];
}) {
  const { summary } = result;

  return (
    <>
      {/* File header */}
      <div className="card px-4 py-3 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-900/50 dark:to-emerald-800/50 flex items-center justify-center shrink-0">
          <FileSpreadsheet className="w-4 h-4 text-emerald-700 dark:text-emerald-300" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-slate-900 dark:text-slate-100 truncate text-sm">
            {filename}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
            {summary.total_issues} lỗi · {summary.employees_with_issues} NV ·{" "}
            {summary.days_with_issues} ngày
          </div>
        </div>
      </div>

      {/* Category chips */}
      <div className="card p-3">
        <div className="flex flex-wrap gap-1.5">
          <CategoryChip
            active={filterCat === "all"}
            onClick={() => setFilterCat("all")}
            label="Tất cả"
            count={summary.total_issues}
          />
          {(Object.keys(summary.issue_types) as IssueCategory[]).map((k) => {
            const meta = CATEGORY_META[k];
            return (
              <CategoryChip
                key={k}
                active={filterCat === k}
                onClick={() => setFilterCat(k)}
                label={meta.label}
                count={summary.issue_types[k]}
                icon={meta.icon}
              />
            );
          })}
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Tìm nhân viên..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 text-sm bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
        />
      </div>

      {/* Employee list - compact */}
      {filteredEmployees.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
          <div className="mt-3 font-semibold text-slate-900 dark:text-slate-100">
            {search || filterCat !== "all"
              ? "Không có kết quả phù hợp"
              : "Bảng công này đã sạch"}
          </div>
        </div>
      ) : (
        <div className="card divide-y divide-slate-100 dark:divide-slate-800 overflow-hidden">
          {filteredEmployees.map(([nv, days]) => {
            const isOpen = expandedNVs[nv];
            const totalIssues = Object.values(days).reduce(
              (s, list) => s + list.length,
              0
            );
            const dayCount = Object.keys(days).length;
            return (
              <div key={nv}>
                {/* NV header */}
                <button
                  onClick={() => {
                    setExpandedNVs((p) => ({ ...p, [nv]: !p[nv] }));
                    if (!expandedNVs[nv] && !selectedDay[nv]) {
                      const firstDay = Object.keys(days).sort(
                        (a, b) => Number(a) - Number(b)
                      )[0];
                      if (firstDay) {
                        setSelectedDay((p) => ({ ...p, [nv]: firstDay }));
                      }
                    }
                  }}
                  className="w-full px-3 py-2 flex items-center gap-2.5 hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors text-left"
                >
                  {isOpen ? (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  )}
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-100 to-brand-200 dark:from-brand-900/50 dark:to-brand-800/50 flex items-center justify-center text-brand-700 dark:text-brand-300 font-semibold shrink-0 text-xs">
                    {titleCase(nv).charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900 dark:text-slate-100 capitalize text-sm leading-tight truncate">
                      {titleCase(nv)}
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">
                      {dayCount} ngày · {totalIssues} lỗi
                    </div>
                  </div>
                  <span className="badge-error text-[10px]">{totalIssues}</span>
                </button>

                {/* NV body */}
                {isOpen && (
                  <div className="bg-slate-50/40 dark:bg-slate-800/30 px-3 py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(days)
                        .sort((a, b) => Number(a[0]) - Number(b[0]))
                        .map(([day, issues]) => {
                          const damage = issues.some(
                            (i) =>
                              categorizeIssue(i) === "may_thieu_bc_tc"
                          );
                          const active = selectedDay[nv] === day;
                          return (
                            <button
                              key={day}
                              onClick={() =>
                                setSelectedDay((p) => ({ ...p, [nv]: day }))
                              }
                              className={cn(
                                "inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium border transition-all",
                                active
                                  ? damage
                                    ? "bg-red-500 text-white border-red-500 shadow-sm"
                                    : "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100"
                                  : damage
                                  ? "bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/50 hover:bg-red-100 dark:hover:bg-red-950/60"
                                  : "bg-white dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                              )}
                              title={`Ngày ${day} · ${issues.length} lỗi`}
                            >
                              <span>Ngày {day}</span>
                              <span
                                className={cn(
                                  "rounded-full px-1 text-[9px] font-bold",
                                  active
                                    ? "bg-white/20 dark:bg-black/20"
                                    : "bg-slate-100 dark:bg-slate-700"
                                )}
                              >
                                {issues.length}
                              </span>
                            </button>
                          );
                        })}
                    </div>

                    {selectedDay[nv] && days[selectedDay[nv]!] && (
                      <div className="mt-2 space-y-1">
                        {days[selectedDay[nv]!].map((issue, i) => {
                          const cat = categorizeIssue(issue);
                          const meta = CATEGORY_META[cat];
                          return (
                            <CategoryIssueRow
                              key={i}
                              issue={issue}
                              cat={cat}
                              meta={meta}
                            />
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

function CategoryIssueRow({
  issue,
  cat,
  meta,
}: {
  issue: string;
  cat: IssueCategory;
  meta: typeof CATEGORY_META[IssueCategory];
}) {
  const darkColors: Record<IssueCategory, string> = {
    di_muon: "dark:bg-amber-950/40 dark:ring-amber-900/50 dark:text-amber-200",
    ve_som: "dark:bg-orange-950/40 dark:ring-orange-900/50 dark:text-orange-200",
    lam_thieu: "dark:bg-purple-950/40 dark:ring-purple-900/50 dark:text-purple-200",
    may_thieu_bc_tc: "dark:bg-red-950/40 dark:ring-red-900/50 dark:text-red-200",
    tc_trong_ca: "dark:bg-pink-950/40 dark:ring-pink-900/50 dark:text-pink-200",
    khac: "dark:bg-slate-800/60 dark:ring-slate-700 dark:text-slate-200",
  };

  return (
    <div
      className={cn(
        "flex items-start gap-2 px-2 py-1.5 rounded-md text-[12px] leading-snug",
        meta.bg,
        meta.ring,
        "ring-1",
        darkColors[cat]
      )}
    >
      <span className="shrink-0 leading-none mt-0.5">{meta.icon}</span>
      <span className={cn("flex-1", meta.color, darkColors[cat].split(" ").pop())}>
        {formatIssueText(issue)}
      </span>
    </div>
  );
}

function CategoryChip({
  active,
  onClick,
  label,
  count,
  icon,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  count: number;
  icon?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all inline-flex items-center gap-1",
        active
          ? "bg-brand-500 text-white border-brand-500"
          : "bg-white dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
      )}
    >
      {icon && <span>{icon}</span>}
      {label}
      <span
        className={cn(
          "px-1.5 rounded-full text-[9px] font-bold",
          active
            ? "bg-white/20 dark:bg-black/20"
            : "bg-slate-100 dark:bg-slate-700"
        )}
      >
        {count}
      </span>
    </button>
  );
}

function titleCase(s: string) {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}
