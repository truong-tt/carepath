import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

async function tabTo(page: Page, target: Locator) {
  for (let attempt = 0; attempt < 140; attempt += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Keyboard focus did not reach the expected control.");
}

async function expectNoSeriousAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const serious = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact ?? ""),
  );
  expect(serious).toEqual([]);
}

test("keyboard-only visitor submits Scribe pilot interest", async ({ page }) => {
  let payload: Record<string, unknown> | undefined;
  await page.route("**/api/leads", async (route) => {
    payload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({ status: 204, body: "" });
  });
  await page.goto("/");

  const name = page.getByRole("textbox", { name: "Họ và tên" });
  await tabTo(page, name);
  await page.keyboard.type("Nguyen Minh Anh");

  const role = page.getByRole("textbox", { name: "Vai trò" });
  await tabTo(page, role);
  await page.keyboard.type("Giam doc phong kham");

  const clinic = page.getByRole("textbox", { name: "Cơ sở y tế" });
  await tabTo(page, clinic);
  await page.keyboard.type("Phong kham Minh Anh");

  const specialty = page.getByRole("textbox", { name: "Chuyên khoa" });
  await tabTo(page, specialty);
  await page.keyboard.type("Noi tong quat");

  const contact = page.getByRole("textbox", { name: "Email hoặc Zalo" });
  await tabTo(page, contact);
  await page.keyboard.type("minhanh@example.com");

  const submit = page.getByRole("button", { name: "Gửi yêu cầu thí điểm" });
  await tabTo(page, submit);
  await page.keyboard.press("Enter");

  await expect(page.getByText("Đã gửi yêu cầu thí điểm.")).toBeVisible();
  expect(payload?.interest).toBe("scribe");
  await expect(page.getByRole("combobox", { name: "Chức năng quan tâm" })).toHaveCount(0);
});

test("Scribe story is clear, responsive, and keeps Interpreter unavailable", async ({ page }) => {
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
      name: "Tập trung vào người bệnh. Để CarePath soạn bản nháp sau buổi khám.",
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
    await expect(page.locator('a[href*="phien-dich-y-khoa"], a[href*="console"]')).toHaveCount(0);

    const primary = page.locator(".scribe-hero__actions").getByRole("link", {
      name: "Bắt đầu ghi chép",
    });
    await expect(primary).toHaveAttribute("href", "/ghi-chep-lam-sang/");
    await page.locator("main#top").focus();
    await page.keyboard.press("Tab");
    await expect(primary).toBeFocused();

    const secondStage = page.locator(".workflow-accordion details").nth(1);
    const secondSummary = secondStage.locator("summary");
    await secondSummary.focus();
    await page.keyboard.press("Enter");
    await expect(secondStage).toHaveAttribute("open", "");

    expect(
      await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
    ).toBeLessThanOrEqual(0);

    if (viewport.width === 390 || viewport.width === 1440) {
      await expectNoSeriousAxeViolations(page);
    }
  }
});

test("clinical notes keep the canonical path and return to the new landing", async ({ page }) => {
  let healthRequested = false;
  await page.route("https://carepath-e2e.example/api/v1/health", async (route) => {
    healthRequested = true;
    await route.fulfill({ status: 200, json: { asr_ready: true, llm_ready: true } });
  });
  await page.goto("/ghi-chep-lam-sang/");
  await expect(page.getByText("Hệ thống sẵn sàng")).toBeVisible();
  expect(healthRequested).toBe(true);
  await expectNoSeriousAxeViolations(page);
  await page.locator(".nav-cta").click();

  await expect(page).toHaveURL(/\/$/);
  await expect(
    page.getByRole("heading", {
      name: "Tập trung vào người bệnh. Để CarePath soạn bản nháp sau buổi khám.",
    }),
  ).toBeVisible();
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
      await expect(menu.getByRole("link", { name: "Bác sĩ kiểm tra" })).toBeVisible();
      if (width === 390) await expectNoSeriousAxeViolations(page);
      await menu.getByRole("link", { name: "Bác sĩ kiểm tra" }).tap();
      await expect(menu).not.toHaveAttribute("open", "");
      await expect(page).toHaveURL(/#safety$/);
    }
  });
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("disables the marquee, pinning, and panel transforms", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    expect(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(true);

    await expect(page.locator(".process-marquee__track")).toHaveCSS("animation-name", "none");
    const panels = page.locator(".scribe-story__visual");
    await expect(panels).toHaveCount(3);
    for (const panel of await panels.all()) {
      await expect(panel).toBeVisible();
      await expect(panel).toHaveCSS("transform", "none");
      await expect(panel).toHaveCSS("opacity", "1");
      await expect(panel).toHaveCSS("filter", "none");
    }
    await expect(page.locator(".scribe-story__heading")).toHaveCSS("position", "static");
  });
});
