import type { Metadata } from "next";
import "./globals.css";
import { ThemeToggle } from "@/components/theme-toggle";

export const metadata: Metadata = {
  title: "XTEP - Check Công",
  description: "Hệ thống phát hiện sai sót chấm công từ bảng công Excel",
};

// Inline script - chạy trước khi React hydrate để tránh flash
const themeScript = `
(function() {
  try {
    var t = localStorage.getItem('theme');
    var d = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (t === 'dark' || (!t && d)) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen gradient-bg">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <div className="flex justify-end mb-2">
            <ThemeToggle />
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
