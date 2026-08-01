import type {
  UploadedFile,
  CheckResult,
  RawData,
  SystemInfo,
} from "./types";

const API_BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return res.json();
}

export const api = {
  health: () => request<{ status: string; service: string }>("/health"),

  listFiles: () => request<{ files: UploadedFile[] }>("/files"),

  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ filename: string; size: number; uploaded_at: string }>(
      "/files/upload",
      { method: "POST", body: formData }
    );
  },

  deleteFile: (filename: string) =>
    request<{ deleted: string }>(`/files/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    }),

  getRawData: (filename: string) =>
    request<RawData>(`/files/${encodeURIComponent(filename)}/raw`),

  check: (filename: string) =>
    request<CheckResult>(`/check/${encodeURIComponent(filename)}`),

  getInfo: () => request<SystemInfo>("/info"),
};
