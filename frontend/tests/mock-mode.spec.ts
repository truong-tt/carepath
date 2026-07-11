import { expect, test } from "@playwright/test";

test("consent gates the mock-mode typed interpreter loop", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: /Hold to talk/ })).toHaveCount(0);
  await page.getByLabel(/Bản dịch AI có thể có lỗi/).check();
  await page.getByLabel(/Có thể yêu cầu thông dịch viên bất cứ lúc nào/).check();
  await page.getByRole("button", { name: "Tiếp tục phiên dịch" }).click();

  await expect(page.getByRole("heading", { name: "Live interpreter" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Connected");
  await page.getByLabel("Typed fallback").fill("xin chao");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("xin chao", { exact: true })).toBeVisible();
  await expect(page.getByText("[vi->en] xin chao", { exact: true })).toBeVisible();

  await page.getByLabel("Typed fallback").fill("uống 500 mg");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Blocked pending doctor confirmation.")).toBeVisible();
  await expect(page.getByText("high: dose_number").first()).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();
  await expect(page.getByText("Blocked pending doctor confirmation.")).toHaveCount(0);
  await expect(page.getByText("high · confirmed")).toBeVisible();

  await page.getByRole("button", { name: "Human interpreter" }).click();
  await expect(page.getByRole("heading", { name: "Human interpreter requested" })).toBeVisible();
});
