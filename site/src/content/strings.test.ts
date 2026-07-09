import { describe, expect, it } from "vitest";
import { strings } from "./strings";

function collectStrings(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(collectStrings);
  if (typeof value === "object" && value !== null) {
    return Object.values(value).flatMap(collectStrings);
  }
  return [];
}

describe("Vietnamese copy", () => {
  it("is NFC-normalized and retains required diacritics", () => {
    const copy = collectStrings(strings.vi);

    expect(copy.every((value) => value === value.normalize("NFC"))).toBe(true);
    expect(copy).toContain("Hỗ trợ AI, bác sĩ xác nhận.");
    expect(copy).toContain("Chờ bác sĩ duyệt");
    expect(copy).toContain("Thông báo sử dụng AI");
    expect(copy).toContain(
      "Công cụ phiên dịch không lưu âm thanh; người dùng luôn được biết đây là AI và có thể yêu cầu con người hỗ trợ.",
    );
  });
});
