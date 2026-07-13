import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

async function tabTo(page: Page, target: Locator) {
  for (let attempt = 0; attempt < 140; attempt += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) {
      return;
    }
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

test("keyboard-only visitor submits a pilot request", async ({
  page,
}) => {
  await page.route("**/api/leads", async (route) => {
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

  const submit = page.getByRole("button", {
    name: "Gửi yêu cầu thí điểm",
  });
  await tabTo(page, submit);
  await page.keyboard.press("Enter");

  await expect(page.getByText("Đã gửi yêu cầu thí điểm.")).toBeVisible();
});

test("the decision gateway has no serious axe violations", async ({
  page,
}) => {
  await page.goto("/");
  await expectNoSeriousAxeViolations(page);
});

test("safety cards stay in the document flow while scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  const cards = page.locator("[data-safety-card]");
  await cards.first().scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 500);

  await expect(cards).toHaveCount(3);
  for (const card of await cards.all()) {
    await expect(card).toHaveCSS("transform", "none");
  }
});

test("both product choices remain discoverable across release viewports", async ({
  page,
}) => {
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

    await expect(
      page.getByRole("heading", {
        level: 1,
        name: "Bạn muốn hỗ trợ việc gì hôm nay?",
      }),
    ).toBeVisible();

    for (const [key, name] of [
      ["scribe", "Ghi chép bệnh án AI: Bắt đầu ghi chép"],
      ["interpreter", "Phiên dịch khám bệnh trực tiếp: Đăng ký nhận cập nhật"],
    ]) {
      const choice = page.locator(`.product-accordion__panel--${key}`);
      await expect(choice).toBeVisible();
      await expect(choice).toHaveAttribute("aria-label", name);
      expect(await choice.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
      expect(await choice.locator(".product-accordion__cta").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    }

    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      ),
    ).toBeLessThanOrEqual(0);

    await page.locator("main#top").focus();
    await page.keyboard.press("Tab");
    await expect(page.locator(".product-accordion__panel--scribe")).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(page.locator(".product-accordion__panel--interpreter")).toBeFocused();

    if (viewport.width <= 1023) {
      const menu = page.locator(".site-nav__menu");
      const summary = menu.locator("summary");
      if (viewport.width === 390) {
        await summary.focus();
        await page.keyboard.press("Enter");
        await expect(menu).toHaveAttribute("open", "");
        await expect(menu.getByRole("link", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
        await expect(menu.getByRole("link", { name: "Ghi chép bệnh án AI" })).toBeVisible();
        await page.keyboard.press("Tab");
        await expect(
          menu.getByRole("link", { name: "Phiên dịch khám bệnh trực tiếp" }),
        ).toBeFocused();
        await page.keyboard.press("Enter");
        await expect(menu).not.toHaveAttribute("open", "");
        await expect(page).toHaveURL(/#products$/);
      } else {
        await summary.click();
        await expect(menu.getByRole("link", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
        await expect(menu.getByRole("link", { name: "Ghi chép bệnh án AI" })).toBeVisible();
      }
    }

  }

  await expect(
    page.locator(".product-accordion__panel--scribe"),
  ).toHaveAttribute("href", "/ghi-chep-lam-sang/");
  await expect(
    page.locator(".product-accordion__panel--interpreter"),
  ).toHaveAttribute("href", "#pilot");

  await page.locator(".product-accordion__panel--interpreter").click();
  await expect(page).toHaveURL(/#pilot$/);
  await expect(page.getByRole("combobox", { name: "Chức năng quan tâm" })).toHaveValue("interpreter");

  await page.getByRole("combobox", { name: "Chức năng quan tâm" }).selectOption("scribe");
  await expect(
    page.getByRole("combobox", { name: "Chức năng quan tâm" }),
  ).toHaveValue("scribe");
  await page.getByRole("combobox", { name: "Chức năng quan tâm" }).selectOption("interpreter");
  await expect(
    page.getByRole("combobox", { name: "Chức năng quan tâm" }),
  ).toHaveValue("interpreter");
});

test("clinical notes use the canonical path and return to the landing page", async ({ page }) => {
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
    page.getByRole("heading", { name: "Bạn muốn hỗ trợ việc gì hôm nay?" }),
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
      await expect(menu.getByRole("link", { name: "An toàn" })).toBeVisible();
      if (width === 390) await expectNoSeriousAxeViolations(page);
      await menu.getByRole("link", { name: "An toàn" }).tap();
      await expect(menu).not.toHaveAttribute("open", "");
      await expect(page).toHaveURL(/#safety$/);
    }
  });
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("keeps the decision gateway static", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    expect(
      await page.evaluate(() =>
        matchMedia("(prefers-reduced-motion: reduce)").matches,
      ),
    ).toBe(true);
    const productPanels = page.locator(".product-accordion__panel");
    await expect(productPanels).toHaveCount(2);
    for (let index = 0; index < 2; index += 1) {
      await expect(productPanels.nth(index)).toBeVisible();
      await expect(productPanels.nth(index).locator("dl")).toBeVisible();
    }
    expect(
      await page.locator(".product-accordion").evaluate(
        (element) => getComputedStyle(element).display,
      ),
    ).toBe("grid");

    await expect(page.locator(".product-story")).toHaveCount(0);
    await expect(page.locator(".marquee")).toHaveCount(0);
  });
});
