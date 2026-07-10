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

test("keyboard-only visitor completes the demo and submits a pilot request", async ({
  page,
}) => {
  await page.route("**/api/leads", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
  await page.goto("/");

  await expect(
    page.getByText("Bản mô phỏng — không phải bản dịch trực tiếp").first(),
  ).toBeVisible();
  await expect(
    page.getByRole("list", { name: "Tiến độ bản mô phỏng" }).getByRole("listitem").first(),
  ).toHaveClass(/is-complete/);

  const start = page.getByRole("button", { name: "Bắt đầu" });
  await tabTo(page, start);
  await page.keyboard.press("Enter");

  const next = page.getByRole("button", { name: "Lượt tiếp theo" });
  await tabTo(page, next);
  for (let turn = 0; turn < 6; turn += 1) {
    await page.keyboard.press("Enter");
  }

  const dialog = page.getByRole("dialog", {
    name: "Xác nhận thông tin quan trọng",
  });
  await expect(dialog).toBeVisible();
  await expect(
    page.getByText("Bị chặn cho đến khi bác sĩ xác nhận."),
  ).toBeVisible();

  const confirm = page.getByRole("button", {
    name: "Xác nhận và tiếp tục",
  });
  await tabTo(page, confirm);
  await page.keyboard.press("Enter");

  await tabTo(page, next);
  await page.keyboard.press("Enter");
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Tải bản ghi demo" }),
  ).toBeVisible();

  const name = page.getByRole("textbox", { name: "Họ và tên" });
  await tabTo(page, name);
  await page.keyboard.type("Nguyen Minh Anh");

  const role = page.getByRole("textbox", { name: "Vai trò" });
  await tabTo(page, role);
  await page.keyboard.type("Giam doc phong kham");

  const contact = page.getByRole("textbox", { name: "Email hoặc Zalo" });
  await tabTo(page, contact);
  await page.keyboard.type("minhanh@example.com");

  const submit = page.getByRole("button", {
    name: "Chuẩn bị yêu cầu thí điểm",
  });
  await tabTo(page, submit);
  await page.keyboard.press("Enter");

  await expect(page.getByText("Đã gửi yêu cầu thí điểm.")).toBeVisible();
  await expect(
    page.getByRole("list", { name: "Tiến độ bản mô phỏng" }).getByRole("listitem").nth(3),
  ).toHaveClass(/is-complete/);
});

test("initial and confirmation states have no serious axe violations", async ({
  page,
}) => {
  await page.goto("/");
  await expectNoSeriousAxeViolations(page);

  const next = page.getByRole("button", { name: "Lượt tiếp theo" });
  for (let turn = 0; turn < 6; turn += 1) {
    await next.click();
  }
  await expect(
    page.getByRole("dialog", { name: "Xác nhận thông tin quan trọng" }),
  ).toBeVisible();
  await expectNoSeriousAxeViolations(page);
});

test("both product choices stay above the fold across release viewports", async ({
  page,
}) => {
  const viewports = [
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
        name: "Một hành trình chăm sóc. Hai sản phẩm CarePath.",
      }),
    ).toBeVisible();

    for (const name of ["Khám phá Interpreter", "Khám phá Scribe"]) {
      const choice = page.getByRole("link", { exact: true, name });
      await expect(choice).toBeVisible();
      const box = await choice.boundingBox();
      expect(box).not.toBeNull();
      expect((box?.y ?? 0) + (box?.height ?? 0)).toBeLessThanOrEqual(
        viewport.height,
      );
    }

    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      ),
    ).toBeLessThanOrEqual(0);

    if (viewport.width <= 1023) {
      const menu = page.locator(".site-nav__menu");
      const summary = menu.locator("summary");
      if (viewport.width === 390) {
        await summary.focus();
        await page.keyboard.press("Enter");
        await expect(menu).toHaveAttribute("open", "");
        await expect(menu.getByRole("link", { name: "Interpreter" })).toBeVisible();
        await expect(menu.getByRole("link", { name: "Scribe" })).toBeVisible();
        await page.keyboard.press("Tab");
        await expect(
          menu.getByRole("link", { name: "Interpreter" }),
        ).toBeFocused();
        await page.keyboard.press("Enter");
        await expect(menu).not.toHaveAttribute("open", "");
      } else {
        await summary.click();
        await expect(menu.getByRole("link", { name: "Interpreter" })).toBeVisible();
        await expect(menu.getByRole("link", { name: "Scribe" })).toBeVisible();
      }
    }

    if (viewport.width === 1440) {
      const lineCounts = await page
        .locator(".evidence .section-intro h2, .evidence-slide__copy h3")
        .evaluateAll((elements) =>
          elements.map((element) => {
            const lineHeight = Number.parseFloat(getComputedStyle(element).lineHeight);
            return Math.round(element.getBoundingClientRect().height / lineHeight);
          }),
        );
      expect(lineCounts.every((count) => count <= 3)).toBe(true);
    }
  }

  await expect(
    page.getByRole("link", { exact: true, name: "Mở công cụ Interpreter" }),
  ).toHaveAttribute("href", "https://carepath-e2e.example/console/");
  await expect(
    page.getByRole("link", { exact: true, name: "Mở công cụ Scribe" }),
  ).toHaveAttribute("href", "#/scribe");

  await page.getByRole("link", { exact: true, name: "Thí điểm Scribe" }).click();
  await expect(
    page.getByRole("combobox", { name: "Sản phẩm quan tâm" }),
  ).toHaveValue("scribe");
  await page.getByRole("link", { exact: true, name: "Thí điểm Interpreter" }).click();
  await expect(
    page.getByRole("combobox", { name: "Sản phẩm quan tâm" }),
  ).toHaveValue("interpreter");
});

test("returning from Scribe restores focus to the landing page", async ({ page }) => {
  let healthRequested = false;
  await page.route("https://carepath-e2e.example/api/v1/health", async (route) => {
    healthRequested = true;
    await route.fulfill({ status: 200, json: { asr_ready: true, llm_ready: true } });
  });
  await page.goto("/#/scribe");
  await expect(page.getByText("Hệ thống sẵn sàng")).toBeVisible();
  expect(healthRequested).toBe(true);
  await expectNoSeriousAxeViolations(page);
  await page.locator(".nav-cta").click();

  await expect(page).toHaveURL(/#top$/);
  await expect(page.locator("main#top")).toBeFocused();
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

  test("disables autoplay and continuous marquee motion", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    expect(
      await page.evaluate(() =>
        matchMedia("(prefers-reduced-motion: reduce)").matches,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Bắt đầu" }).click();
    await page.waitForTimeout(4200);

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

    await expect(
      page.getByText("Hội thoại sẽ xuất hiện tại đây."),
    ).toBeVisible();
    const state = await page.evaluate(() => ({
      marqueeAnimation: getComputedStyle(
        document.querySelector(".marquee__track")!,
      ).animationName,
      transcriptTurns: document.querySelectorAll(".turn").length,
      reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
    }));
    expect(JSON.stringify(state, null, 2)).toMatchSnapshot(
      "reduced-motion-state.txt",
    );
  });
});
