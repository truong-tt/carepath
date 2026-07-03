import type { Metadata } from "next";
import ToolClient from "./tool-client";

export const metadata: Metadata = {
  title: "CarePath · Tạo bệnh án SOAP",
  description:
    "CarePath: trợ lý ghi chép y khoa bằng AI cho nhân viên y tế Việt Nam. Ghi âm hoặc tải lên bản ghi âm buổi khám và nhận bệnh án SOAP nháp.",
};

export default function ToolPage() {
  return <ToolClient />;
}
