"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggle = () => {
    const next = !isDark;
    if (next) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", next ? "dark" : "light");
    setIsDark(next);
  };

  // Tránh hydration mismatch
  if (!mounted) {
    return (
      <button
        className="w-9 h-9 rounded-lg border border-slate-200 bg-white"
        aria-hidden
      />
    );
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      title={isDark ? "Chuyển sang sáng" : "Chuyển sang tối"}
      className={cn(
        "w-9 h-9 rounded-lg border inline-flex items-center justify-center transition-all",
        isDark
          ? "bg-slate-800 border-slate-700 text-amber-300 hover:bg-slate-700"
          : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
      )}
    >
      {isDark ? (
        <Sun className="w-4 h-4" strokeWidth={2.2} />
      ) : (
        <Moon className="w-4 h-4" strokeWidth={2.2} />
      )}
    </button>
  );
}
