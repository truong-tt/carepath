import type { Metadata, Viewport } from "next";
import { preload } from "react-dom";
import "./css/styles.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "CarePath · Trợ lý ghi chép y khoa AI cho phòng khám Việt Nam",
  description:
    "CarePath biến bản ghi âm buổi khám thành bản nháp bệnh án SOAP — hiểu cả tiếng Việt lẫn thuật ngữ tiếng Anh, để bác sĩ duyệt lần cuối.",
  icons: { icon: "/assets/carepath-mark.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  colorScheme: "light",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  preload("/assets/fonts/jakarta-latin.woff2", { as: "font", type: "font/woff2", crossOrigin: "anonymous" });
  preload("/assets/fonts/jakarta-vietnamese.woff2", { as: "font", type: "font/woff2", crossOrigin: "anonymous" });
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
