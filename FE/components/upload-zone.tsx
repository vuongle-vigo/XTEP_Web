"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api";
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
} from "lucide-react";

type UploadResult = {
  file: File;
  status: "ok" | "error";
  message: string;
};

export function UploadZone({
  onUploaded,
  collapsed = false,
}: {
  onUploaded?: () => void;
  collapsed?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(!collapsed);
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);

  const handleFiles = async (files: FileList | File[]) => {
    const list = Array.from(files);
    if (list.length === 0) return;

    setUploading(true);
    const newResults: UploadResult[] = [];

    for (const file of list) {
      if (!file.name.toLowerCase().endsWith(".xlsx")) {
        newResults.push({
          file,
          status: "error",
          message: "Chỉ hỗ trợ file .xlsx",
        });
        continue;
      }
      try {
        await api.uploadFile(file);
        newResults.push({ file, status: "ok", message: "Upload thành công" });
      } catch (e: any) {
        newResults.push({
          file,
          status: "error",
          message: e.message || "Lỗi không xác định",
        });
      }
    }

    setResults(newResults);
    setUploading(false);
    if (newResults.some((r) => r.status === "ok")) onUploaded?.();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    handleFiles(e.dataTransfer.files);
  };

  if (collapsed && !open) {
    return (
      <div className="card p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-100 to-brand-200 dark:from-brand-900/50 dark:to-brand-800/50 flex items-center justify-center">
            <Upload className="w-4 h-4 text-brand-600 dark:text-brand-400" />
          </div>
          <div>
            <div className="font-medium text-slate-900 dark:text-slate-100 text-sm">
              Upload thêm file bảng công
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Hỗ trợ .xlsx · nhiều file
            </div>
          </div>
        </div>
        <button onClick={() => setOpen(true)} className="btn-primary">
          <Upload className="w-4 h-4" />
          Upload
          <ChevronDown className="w-3.5 h-3.5 -rotate-90" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative cursor-pointer card border-2 border-dashed transition-all p-8 lg:p-10 text-center ${
          drag
            ? "border-brand-400 bg-brand-50/50 dark:bg-brand-950/30"
            : "border-slate-300 dark:border-slate-700 hover:border-brand-400 hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) handleFiles(e.target.files);
            e.target.value = "";
          }}
        />

        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-100 to-brand-200 dark:from-brand-900/50 dark:to-brand-800/50 flex items-center justify-center mx-auto">
          {uploading ? (
            <Loader2 className="w-6 h-6 text-brand-600 dark:text-brand-400 animate-spin" />
          ) : (
            <Upload className="w-6 h-6 text-brand-600 dark:text-brand-400" />
          )}
        </div>

        <div className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
          {uploading ? "Đang upload..." : "Kéo thả file vào đây"}
        </div>
        <div className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          hoặc{" "}
          <span className="text-brand-600 dark:text-brand-400 font-medium">
            bấm để chọn file
          </span>
        </div>
        <div className="text-xs text-slate-400 dark:text-slate-500 mt-2">
          Hỗ trợ .xlsx · Có thể upload nhiều file cùng lúc
        </div>
      </div>

      {results.length > 0 && (
        <div className="card p-4">
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Kết quả upload ({results.length})
          </div>
          <div className="space-y-2">
            {results.map((r, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 p-2.5 rounded-xl border ${
                  r.status === "ok"
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/50"
                    : "bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/50"
                }`}
              >
                {r.status === "ok" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
                )}
                <FileSpreadsheet className="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                    {r.file.name}
                  </div>
                  <div
                    className={`text-xs ${
                      r.status === "ok"
                        ? "text-emerald-700 dark:text-emerald-300"
                        : "text-red-700 dark:text-red-300"
                    }`}
                  >
                    {r.message}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
