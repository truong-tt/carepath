import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

async function tabTo(page: Page, target: Locator) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Keyboard focus did not reach the expected control.");
}

async function expectNoSeriousAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    results.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact ?? ""),
    ),
  ).toEqual([]);
}

test("keyboard-only visitor can inspect the sample and submit Scribe pilot interest", async ({ page }) => {
  let payload: Record<string, unknown> | undefined;
  await page.route("**/api/leads", async (route) => {
    payload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({ status: 204, body: "" });
  });
  await page.goto("/");

  const firstSampleStep = page.getByRole("button", { name: "1. Cuộc trao đổi" });
  await tabTo(page, firstSampleStep);
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Chưa có kết quả điện tâm đồ")).toBeVisible();

  const pilot = page.getByText("Dành cho cơ sở muốn thí điểm CarePath");
  await tabTo(page, pilot);
  await page.keyboard.press("Enter");

  const name = page.getByRole("textbox", { name: "Họ và tên" });
  await tabTo(page, name);
  await page.keyboard.type("Nguyen Minh Anh");
  await page.getByRole("textbox", { name: "Vai trò" }).fill("Giam doc phong kham");
  await page.getByRole("textbox", { name: "Cơ sở y tế" }).fill("Phong kham Minh Anh");
  await page.getByRole("textbox", { name: "Chuyên khoa" }).fill("Noi tong quat");
  await page.getByRole("textbox", { name: "Email hoặc Zalo" }).fill("minhanh@example.com");
  await page.getByRole("button", { name: "Gửi yêu cầu thí điểm" }).click();

  await expect(page.getByText("Đã gửi yêu cầu thí điểm.")).toBeVisible();
  expect(payload?.interest).toBe("scribe");
  await expect(page.getByRole("combobox", { name: "Chức năng quan tâm" })).toHaveCount(0);
});

test("Vietnamese onboarding is compact, responsive, and keeps Interpreter unavailable", async ({ page }) => {
  const viewports = [
    { width: 320, height: 800 },
    { width: 360, height: 800 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    await page.goto("/");

    const title = page.getByRole("heading", {
      level: 1,
      name: "Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.",
    });
    await expect(title).toBeVisible();
    const lineCount = await title.evaluate((element) => {
      const style = getComputedStyle(element);
      return Math.round(element.getBoundingClientRect().height / Number.parseFloat(style.lineHeight));
    });
    expect(lineCount).toBeLessThanOrEqual(viewport.width >= 1024 ? 2 : 3);

    const status = page.locator("[data-interpreter-status]");
    await expect(status).toContainText("Phiên dịch khám bệnh trực tiếp");
    await expect(status).toContainText("Đang phát triển — hiện chưa thể truy cập trên web.");
    await expect(status.locator("a, button")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "EN" })).toHaveCount(0);
    await expect(page.locator('a[href*="phien-dich-y-khoa"], a[href*="console"]')).toHaveCount(0);

    await expect(page.getByRole("link", { name: "Trải nghiệm ca khám mẫu" })).toHaveAttribute("href", "#demo");
    await expect(page.getByText("2 giờ 20 phút mỗi ngày")).toBeVisible();
    await expect(page.getByText("Chờ bác sĩ nhập hoặc xác nhận.")).toHaveCount(0);

    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
    if (viewport.width === 1440) {
      const heroHeight = await page.locator(".onboarding-hero").evaluate((element) => element.getBoundingClientRect().height);
      expect(heroHeight).toBeLessThan(800);
    }

    if (viewport.width === 390 || viewport.width === 1440) {
      await expectNoSeriousAxeViolations(page);
      await page.screenshot({
        fullPage: true,
        path: `../../.codex/qa-evidence/cp-ux-11-${viewport.width}.png`,
      });
    }
  }
});

test("calculator updates transparently and the guided sample keeps decisions with the doctor", async ({ page }) => {
  await page.goto("/#calculator");
  await page.getByRole("spinbutton", { name: "Số người bệnh mỗi ngày" }).fill("28");
  await page.getByRole("spinbutton", { name: "Phút ghi chép cho mỗi người bệnh" }).fill("5");
  await expect(page.getByText("2 giờ 20 phút mỗi ngày")).toBeVisible();
  await expect(page.getByText("11 giờ 40 phút cho 5 ngày làm việc")).toBeVisible();
  await expect(page.getByText(/Công thức: 28 người bệnh × 5 phút/)).toBeVisible();

  await page.getByRole("button", { name: "3. Bản nháp có cấu trúc" }).click();
  await expect(page.getByText("Chờ bác sĩ nhập hoặc xác nhận.")).toHaveCount(2);
  await page.getByRole("button", { name: "4. Bác sĩ kiểm tra" }).click();
  await expect(page.getByText("Tự nhập hoặc xác nhận Nhận định và Kế hoạch.")).toBeVisible();
});

test("clinical notes expose guidance and upload together, then return to the sample", async ({ page }) => {
  await page.route("https://carepath-e2e.example/api/v1/health", async (route) => {
    await route.fulfill({ status: 200, json: { asr_ready: true, llm_ready: true } });
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ghi-chep-lam-sang/");
  await expect(page.getByText("Hệ thống sẵn sàng")).toBeVisible();
  await expect(page.getByText("Ba bước để tạo bản nháp")).toBeVisible();
  await expect(page.getByText("Kéo thả tệp âm thanh vào đây, hoặc bấm để chọn")).toBeVisible();
  await expect(page.getByRole("button", { name: "Tiếp tục tạo bản nháp" })).toHaveCount(0);
  await expectNoSeriousAxeViolations(page);
  await page.screenshot({
    fullPage: true,
    path: "../../.codex/qa-evidence/cp-ux-11-tool-390.png",
  });

  await page.getByRole("link", { name: "Xem ca khám mẫu trước" }).click();
  await expect(page).toHaveURL(/\/#demo$/);
  await expect(page.getByRole("heading", { name: "Thử một ca khám mẫu trước khi tải tệp của bạn." })).toBeVisible();
});

test.describe("touch navigation", () => {
  test.use({ hasTouch: true });

  test("keeps the menu in view and closes it after navigation", async ({ page }) => {
    for (const width of [320, 390, 760, 900]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/");
      const menu = page.locator(".site-nav__menu");
      await menu.locator("summary").tap();
      const panel = await menu.locator(":scope > div").boundingBox();
      expect(panel).not.toBeNull();
      expect(panel?.x ?? -1).toBeGreaterThanOrEqual(0);
      expect((panel?.x ?? 0) + (panel?.width ?? 0)).toBeLessThanOrEqual(width);
      await menu.getByRole("link", { name: "Ca khám mẫu" }).tap();
      await expect(menu).not.toHaveAttribute("open", "");
      await expect(page).toHaveURL(/#demo$/);
    }
  });
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("keeps content static without marquee or pinning", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".process-marquee, .scribe-story")).toHaveCount(0);
    await expect(page.locator(".onboarding-hero")).toHaveCSS("transform", "none");
    expect(await page.evaluate(() => document.getAnimations().filter((animation) => animation.playState === "running").length)).toBe(0);
  });
});

for (const colorScheme of ["light", "dark"] as const) {
  test(`keeps the main action readable in ${colorScheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme });
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:4173/");
    await expect(page.getByRole("link", { name: "Trải nghiệm ca khám mẫu" })).toBeVisible();
    await expectNoSeriousAxeViolations(page);
    await context.close();
  });
}
