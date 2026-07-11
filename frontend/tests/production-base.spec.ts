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

test("reaches internal review only through the canonical hash route", async ({ page }) => {
  await page.goto("/phien-dich-y-khoa/#/kiem-duyet");

  await expect(page.getByRole("heading", { name: "Translation review" })).toBeVisible();
  await page.getByRole("link", { name: "Quay lại phiên dịch" }).click();
  await expect(page.getByText("Hôm nay bạn là ai?")).toBeVisible();
});
