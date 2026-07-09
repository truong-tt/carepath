import { readdir, readFile } from "node:fs/promises";
import { extname, join } from "node:path";

async function filesUnder(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map((entry) => {
      const path = join(directory, entry.name);
      return entry.isDirectory() ? filesUnder(path) : [path];
    }),
  );
  return nested.flat();
}

const files = (await filesUnder("dist")).filter((path) =>
  [".html", ".js"].includes(extname(path)),
);
const output = (await Promise.all(files.map((path) => readFile(path, "utf8")))).join(
  "\n",
);

const required = [
  "Hỗ trợ AI, bác sĩ xác nhận.",
  "Bản mô phỏng — không phải bản dịch trực tiếp",
  "Thông báo sử dụng AI",
  "Công cụ phiên dịch",
  "Chờ bác sĩ duyệt",
  "Bản nháp SOAP chờ duyệt",
];
const forbidden = [
  "Ho tro AI, bac si xac nhan",
  "Ban mo phong",
  "Thong bao su dung AI",
  "Cong cu phien dich",
  "Cho bac si duyet",
];

for (const phrase of required) {
  if (!output.includes(phrase.normalize("NFC"))) {
    throw new Error(`Built output is missing required Vietnamese copy: ${phrase}`);
  }
}

for (const phrase of forbidden) {
  if (output.includes(phrase)) {
    throw new Error(`Built output contains stripped Vietnamese copy: ${phrase}`);
  }
}
