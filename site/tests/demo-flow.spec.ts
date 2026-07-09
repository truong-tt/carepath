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

test("phone layout has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
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
