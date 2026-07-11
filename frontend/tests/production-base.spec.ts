import { expect, test } from "@playwright/test";

test("serves production assets from the canonical interpreter path", async ({ page }) => {
  await page.goto("/phien-dich-y-khoa/");

  await expect(page.getByText("Hôm nay bạn là ai?")).toBeVisible();
  expect(
    await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        .some((entry) => new URL(entry.name).pathname.startsWith("/phien-dich-y-khoa/assets/")),
    ),
  ).toBe(true);
});

test("keeps bilingual consent choices readable at phone width", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/phien-dich-y-khoa/");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Tiếp tục" }).click();

  const companion = page.getByText(/AI-generated translations can contain errors/);
  await expect(companion).toBeVisible();
  const bounds = await companion.boundingBox();
  expect(bounds?.width).toBeGreaterThan(180);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});

test("keeps onboarding controls visible with forced colors", async ({ page }) => {
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await page.goto("/phien-dich-y-khoa/");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Tiếp tục" }).click();

  await expect(page.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
  await expect(page.getByLabel(/bản dịch do AI tạo ra có thể có lỗi/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Bắt đầu phiên dịch" })).toBeVisible();
});

test("reaches internal review only through the canonical hash route", async ({ page }) => {
  await page.goto("/phien-dich-y-khoa/#/kiem-duyet");

  await expect(page.getByRole("heading", { name: "Translation review" })).toBeVisible();
  await page.getByRole("link", { name: "Quay lại phiên dịch" }).click();
  await expect(page.getByText("Hôm nay bạn là ai?")).toBeVisible();
});
