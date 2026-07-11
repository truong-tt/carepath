import { expect, test } from "@playwright/test";

test("consent gates the mock-mode typed interpreter loop", async ({ page }) => {
  let clinicalRequests = 0;
  let webSockets = 0;
  page.on("request", (request) => {
    if (request.url().includes("/api/")) {
      clinicalRequests += 1;
    }
  });
  page.on("websocket", (socket) => {
    if (socket.url().includes("/ws/")) {
      webSockets += 1;
    }
  });
  await page.goto("/");

  await expect(page.getByRole("button", { name: /Nhấn giữ để nói/ })).toHaveCount(0);
  await expect(page.getByText("Hôm nay bạn là ai?")).toBeVisible();
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await expect(page.getByText("Bạn cần dịch theo chiều nào?")).toBeVisible();
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Xem mô phỏng" }).click();
  await expect(page.getByText("Bản dịch được chuyển")).toBeVisible();
  await page.getByRole("button", { name: "Xem tình huống tiếp theo" }).click();
  await expect(page.getByText("Độ tin cậy thấp", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Xem tình huống tiếp theo" }).click();
  await expect(page.getByText("Đã chặn, chờ bác sĩ xác nhận", { exact: true })).toBeVisible();
  expect(clinicalRequests).toBe(0);
  expect(webSockets).toBe(0);

  await page.getByLabel(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/).check();
  await page.getByLabel(/Tôi đã được giải thích rằng có thể yêu cầu phiên dịch viên trực tiếp/).check();
  await page.getByRole("button", { name: "Bắt đầu phiên dịch" }).click();

  await expect(page.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Đã kết nối");
  const doctorRegion = page.locator(".input-region").filter({ has: page.getByRole("heading", { name: "Bác sĩ · Tiếng Việt" }) });
  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();

  await expect(page.getByText("xin chao", { exact: true })).toBeVisible();
  await expect(page.getByText("[vi->en] xin chao", { exact: true })).toBeVisible();

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("uống 500 mg");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();

  await expect(page.getByText("Đã chặn, chờ bác sĩ xác nhận.")).toBeVisible();
  await expect(page.getByText("Cao: Liều lượng").first()).toBeVisible();
  await page.getByRole("button", { name: "Xác nhận" }).click();
  await expect(page.getByText("Đã chặn, chờ bác sĩ xác nhận.")).toHaveCount(0);
  await expect(page.getByText("Cao · Đã xác nhận")).toBeVisible();

  await page.getByRole("button", { name: "Yêu cầu phiên dịch viên trực tiếp" }).click();
  await expect(page.getByRole("heading", { name: "Đã yêu cầu phiên dịch viên trực tiếp" })).toBeVisible();
});
