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

function structure(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(structure);
  if (typeof value === "object" && value !== null) {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [key, structure(child)]),
    );
  }
  return typeof value;
}

describe("Vietnamese copy", () => {
  it("is NFC-normalized and retains required diacritics", () => {
    const copy = collectStrings(strings.vi);

    expect(copy.every((value) => value === value.normalize("NFC"))).toBe(true);
    expect(copy).toContain("AI hỗ trợ, bác sĩ giữ quyền quyết định.");
    expect(copy).toContain("Chờ bác sĩ duyệt");
    expect(copy).toContain("Thông báo sử dụng AI");
    expect(copy).toContain(
      "Công cụ phiên dịch không lưu âm thanh; người dùng luôn được biết đây là AI và có thể yêu cầu con người hỗ trợ.",
    );
  });

  it("keeps complete Vietnamese and English structures in parity", () => {
    expect(structure(strings.en)).toEqual(structure(strings.vi));
    expect(collectStrings(strings.en).every((value) => value.trim().length > 0)).toBe(true);
    expect(collectStrings(strings.vi).every((value) => value.trim().length > 0)).toBe(true);
  });
});
