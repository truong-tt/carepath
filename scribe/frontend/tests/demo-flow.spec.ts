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

test("keyboard-only visitor can submit a pilot request", async ({ page }) => {
  let payload: Record<string, unknown> | undefined;
  await page.route("**/api/leads", async (route) => {
    payload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({ status: 204, body: "" });
  });
  await page.goto("/");

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
  // Defaults to "both" and is selectable. It was pinned to "scribe" and hidden,
  // left over from the two-product site, so every enquiry from a page about the
  // bilingual visit arrived tagged as the other product.
  expect(payload?.interest).toBe("both");
  await expect(page.getByRole("combobox", { name: "Chức năng quan tâm" })).toBeVisible();
});

test("the landing page states the patient-safety problem, responsively", async ({ page }) => {
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
      name: "Người bệnh nước ngoài rời phòng khám với tờ giấy họ không đọc được.",
    });
    await expect(title).toBeVisible();
    const lineCount = await title.evaluate((element) => {
      const style = getComputedStyle(element);
      return Math.round(element.getBoundingClientRect().height / Number.parseFloat(style.lineHeight));
    });
    expect(lineCount).toBeLessThanOrEqual(viewport.width >= 1024 ? 4 : 6);

    // The "interpreter unavailable" banner contradicted the product once the
    // bilingual visit shipped, and the documentation-burden calculator sold the
    // use case that was rejected.
    await expect(page.locator("[data-interpreter-status]")).toHaveCount(0);
    await expect(page.getByRole("spinbutton", { name: "Số người bệnh mỗi ngày" })).toHaveCount(0);

    // Evidence, with its limits stated.
    await expect(page.getByText(/49,1%/)).toBeVisible();
    await expect(page.getByText(/không phải kết quả của CarePath/)).toBeVisible();

    await expect(page.getByRole("link", { name: "Bắt đầu ca khám" }).first()).toHaveAttribute(
      "href",
      "/kham-song-ngu/",
    );

    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
    if (viewport.width === 1440) {
      const heroHeight = await page.locator(".p-hero").evaluate((element) => element.getBoundingClientRect().height);
      expect(heroHeight).toBeLessThan(800);
    }

    // The page's most important sentence must be its largest type. A child
    // combinator silently dropped the h1 to the browser default once already,
    // and nothing in the build caught it.
    const headingSizes = await page.evaluate(() =>
      [...document.querySelectorAll("h1, h2, h3")].map((element) => ({
        tag: element.tagName,
        size: Number.parseFloat(getComputedStyle(element).fontSize),
      })),
    );
    const h1Size = headingSizes.find((heading) => heading.tag === "H1")?.size ?? 0;
    expect(h1Size).toBeGreaterThan(0);
    for (const heading of headingSizes) {
      expect(heading.size).toBeLessThanOrEqual(h1Size);
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

test("a non-Vietnamese reader can switch the whole page to English", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Switch to English" }).click();

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Foreign patients leave the clinic holding paper they cannot read.",
    }),
  ).toBeVisible();
  await expect(page.getByText(/49.1%/)).toBeVisible();
  await expect(page.getByText(/21.2 million/)).toBeVisible();
  // Limits travel with the claims.
  await expect(page.getByText(/not from CarePath/)).toBeVisible();
  await expect(page.getByText(/No clinical trial/)).toBeVisible();

  await page.getByRole("button", { name: "Chuyển sang tiếng Việt" }).click();
  await expect(page.getByText(/Chưa có thử nghiệm lâm sàng/)).toBeVisible();
});

test("clinical notes expose guidance and upload together, then return to the sample", async ({ page }) => {
  await page.route("https://carepath-e2e.example/api/v1/health", async (route) => {
    await route.fulfill({ status: 200, json: { asr_ready: true, llm_ready: true } });
  });
  await page.route("https://carepath-e2e.example/api/v1/soap-notes", async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        raw_transcript: "ban ghi tho khong duoc hien thi",
        corrected_transcript: "Bản ghi đã sửa không được hiển thị.",
        retrieved_terms: ["thuật ngữ ẩn"],
        soap: {
          subjective: "Đau đầu từ sáng nay.",
          objective: "Huyết áp **160/90 mmHg**.",
          assessment: "Tăng huyết áp chưa kiểm soát.",
          plan: "Tái khám sau một tuần.",
          review_required: true,
          missing_information: ["Tiền sử dị ứng"],
        },
        metadata: { latency_ms: 3200 },
      },
    });
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

  await page.getByRole("link", { name: "Xem cách hoạt động" }).click();
  await expect(page).toHaveURL(/\/#how$/);
  await expect(
    page.getByRole("heading", { name: "Đọc — đối chiếu — bác sĩ xác nhận." }),
  ).toBeVisible();
  await page.goto("/ghi-chep-lam-sang/");

  await page.locator('input[type="file"]').setInputFiles({
    name: "kham.wav",
    mimeType: "audio/wav",
    buffer: Buffer.from("RIFF"),
  });
  await page.getByRole("button", { name: "Tạo bản nháp SOAP" }).click();

  const result = page.getByLabel("Bản nháp y khoa theo bốn mục SOAP");
  await expect(result.getByText("Bản nháp SOAP — cần bác sĩ kiểm tra")).toHaveCount(1);
  await expect(result.getByText("Đau đầu từ sáng nay.")).toBeVisible();
  await expect(result.getByText("160/90 mmHg")).toBeVisible();
  await expect(result.getByText("Thông tin còn thiếu")).toBeVisible();
  await expect(result.getByText("Tiền sử dị ứng")).toBeVisible();
  await expect(result.getByText("Bản phiên âm tự động")).toHaveCount(0);
  await expect(result.getByText("Bản phiên âm sau hiệu chỉnh")).toHaveCount(0);
  await expect(result.getByText("Thuật ngữ đã đối chiếu")).toHaveCount(0);
  await expect(result.getByText("ban ghi tho khong duoc hien thi")).toHaveCount(0);
  await expect(result.getByText("Bản ghi đã sửa không được hiển thị.")).toHaveCount(0);
  await expect(result.getByText("thuật ngữ ẩn")).toHaveCount(0);
  const resultText = (await result.textContent()) ?? "";
  expect(resultText.indexOf("Đau đầu từ sáng nay.")).toBeLessThan(resultText.indexOf("Tiền sử dị ứng"));
  await expectNoSeriousAxeViolations(page);
  await page.screenshot({
    fullPage: true,
    path: "../../.codex/qa-evidence/cp-ux-14-result-390.png",
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(result).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
  await expectNoSeriousAxeViolations(page);
  await page.screenshot({
    fullPage: true,
    path: "../../.codex/qa-evidence/cp-ux-14-result-1440.png",
  });
});

test.describe("touch navigation", () => {
  test.use({ hasTouch: true });

  // The disclosure menu is gone: the four anchors wrap to their own row rather
  // than hide behind a hamburger. What still has to hold is that they stay
  // reachable and inside the viewport at every narrow width.
  test("keeps the section links reachable on a phone", async ({ page }) => {
    for (const width of [320, 390, 760, 900]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/");
      const link = page.locator(".p-nav__links").getByRole("link", { name: "Bằng chứng" });
      await link.scrollIntoViewIfNeeded();
      const box = await link.boundingBox();
      expect(box).not.toBeNull();
      expect(box?.x ?? -1).toBeGreaterThanOrEqual(0);
      expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(width);
      await link.tap();
      await expect(page).toHaveURL(/#evidence$/);
    }
  });
});

// Built on newContext rather than test.use: the describe-scoped test.use did
// not reach the browser here — matchMedia("(prefers-reduced-motion: reduce)")
// read false inside it, so this assertion passed for years by never running
// against the preference it names.
test("keeps content static for a visitor who asked for reduced motion", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/");

  expect(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(
    true,
  );
  await expect(page.locator(".process-marquee, .scribe-story")).toHaveCount(0);
  await expect(page.locator(".p-hero")).toHaveCSS("transform", "none");
  expect(
    await page.evaluate(
      () => document.getAnimations().filter((animation) => animation.playState === "running").length,
    ),
  ).toBe(0);

  await context.close();
});

test("the served page describes the product it actually is", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173/");

  // Asserted on the served HTML, before and after hydration: the title used to
  // be correct in index.html and then overwritten by JS with "Bớt gõ bệnh án",
  // the retired Scribe-led product.
  await expect(page).toHaveTitle(/Khám song ngữ cho người bệnh nước ngoài/);
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveTitle(/Khám song ngữ cho người bệnh nước ngoài/);

  const meta = (name: string) =>
    page.locator(`meta[property="${name}"], meta[name="${name}"]`).first();
  await expect(meta("og:url")).toHaveAttribute("content", /carepath-medicaltranslation/);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    /carepath-medicaltranslation/,
  );
  await expect(meta("og:image")).toHaveAttribute("content", /\/og\.png$/);
  await expect(meta("twitter:card")).toHaveAttribute("content", "summary_large_image");

  // The card has to exist, not just be declared.
  const og = await page.request.get("http://127.0.0.1:4173/og.png");
  expect(og.status()).toBe(200);
});

// The landing and the tools ran two unrelated design systems in one bundle:
// Be Vietnam Pro / navy / square on `/`, Geist / teal #0f766e / rounded on the
// tool routes, sharing no token, with both font families shipping everywhere.
// These assertions are what stops that forking again.
for (const path of ["/", "/kham-song-ngu/", "/ghi-chep-lam-sang/"]) {
  test(`renders ${path} in the one design world`, async ({ page }) => {
    const requested: string[] = [];
    page.on("request", (request) => requested.push(request.url()));

    await page.goto(`http://127.0.0.1:4173${path}`);
    await page.waitForLoadState("networkidle");

    const world = await page.evaluate(() => {
      const root = getComputedStyle(document.documentElement);
      return {
        blue: root.getPropertyValue("--p-blue").trim(),
        seal: root.getPropertyValue("--p-seal").trim(),
        // The legacy names must resolve through the print palette, not to the
        // teal literals they used to hold.
        teal: root.getPropertyValue("--teal").trim(),
        panelRadius: root.getPropertyValue("--r-panel").trim(),
        bodyFont: getComputedStyle(document.body).fontFamily,
      };
    });

    // Tokens are defined once, at the root, for every route.
    expect(world.blue).toBe("#0f2e5c");
    expect(world.seal).toBe("#c41e22");
    expect(world.teal).toBe("#0f2e5c");
    expect(world.panelRadius).toBe("0");
    expect(world.bodyFont).toContain("Be Vietnam Pro");
    expect(world.bodyFont).not.toContain("Geist");

    // Not one Geist byte on any route.
    expect(requested.filter((url) => /geist/i.test(url))).toEqual([]);
  });
}

for (const colorScheme of ["light", "dark"] as const) {
  test(`keeps the main action readable in ${colorScheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme });
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:4173/");
    await expect(page.getByRole("link", { name: "Bắt đầu ca khám" }).first()).toBeVisible();
    await expectNoSeriousAxeViolations(page);
    await context.close();
  });
}
