import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const HUB = "http://127.0.0.1:4173/thu-nghiem/";

/** One gated line and one delivered line, shaped like a real turn payload. */
const TURNS = [
  {
    id: "t1",
    session_id: "s",
    seq: 1,
    speaker: "document",
    src_lang: "vi",
    tgt_lang: "en",
    source_text: "Amoxicillin 500 mg Uống 1 viên, ngày 2 lần, sau ăn",
    normalized_text: "",
    translation: "Amoxicillin 500 mg - take 1 tablet, 2 times a day, after food",
    asr_confidence: 1,
    mt_confidence: 1,
    risk_tier: "high",
    risk_spans: [{ kind: "dose_number", severity: "high", term: "500 mg" }],
    readback: null,
    status: "awaiting_confirm",
    corrected_text: null,
    created_at: "",
    requires_confirmation: true,
  },
  {
    id: "t2",
    session_id: "s",
    seq: 2,
    speaker: "document",
    src_lang: "vi",
    tgt_lang: "en",
    source_text: "Tái khám sau 5 ngày",
    normalized_text: "",
    translation: "Return for review after 5 days",
    asr_confidence: 1,
    mt_confidence: 1,
    risk_tier: "low",
    risk_spans: [],
    readback: null,
    status: "delivered",
    corrected_text: null,
    created_at: "",
    requires_confirmation: false,
  },
];

async function stub(page: Page, providerMode: string, document?: unknown, status = 200) {
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok", provider_mode: providerMode } }),
  );
  await page.route("**/api/demo/document*", (route) =>
    route.fulfill({ status, json: document ?? { turns: TURNS, sample: true, remaining: 4 } }),
  );
}

test("a visitor sees the limits before running anything", async ({ page }) => {
  await stub(page, "ckey");
  await page.goto(HUB);

  const limits = page.getByRole("region", { name: "Giới hạn của bản thử" });
  await expect(limits).toBeVisible();
  await expect(limits).toContainText("5 lượt mỗi ngày");
  await expect(limits).toContainText("Không lưu ảnh");

  // Above the first panel, not in a footer after the result.
  const limitsBox = await limits.boundingBox();
  const panelBox = await page.getByRole("region", { name: /Ảnh đơn thuốc/ }).boundingBox();
  expect(limitsBox!.y).toBeLessThan(panelBox!.y);
});

test("the withheld line hides its English until the doctor view is opened", async ({ page }) => {
  await stub(page, "ckey");
  await page.goto(HUB);
  await page.getByRole("button", { name: "Xem ví dụ dựng sẵn" }).click();

  const gated = page.locator(".d-row.is-gated");
  await expect(gated).toHaveCount(1);
  await expect(gated).toContainText("Chờ bác sĩ xác nhận");

  // This is the product's whole claim: the patient does not see the dose line.
  await expect(page.locator(".d-rows")).not.toContainText("take 1 tablet");
  // The low-risk line was delivered and is visible.
  await expect(page.locator(".d-rows")).toContainText("Return for review after 5 days");

  await page.getByRole("button", { name: "Xem như bác sĩ" }).click();
  await expect(page.locator(".d-rows")).toContainText("take 1 tablet");
});

test("a scripted sample is labelled as one", async ({ page }) => {
  await stub(page, "ckey");
  await page.goto(HUB);
  await page.getByRole("button", { name: "Xem ví dụ dựng sẵn" }).click();

  await expect(page.getByText("Ví dụ dựng sẵn").first()).toBeVisible();
  await expect(page.getByText(/không phải ảnh bạn tải lên/)).toBeVisible();
  await expect(page.getByText("Kết quả demo — không dùng cho lâm sàng.")).toBeVisible();
});

test("running out of quota says so, and does not invent a result", async ({ page }) => {
  await stub(page, "ckey", { error: "Bạn đã dùng hết lượt thử hôm nay. Mời quay lại vào ngày mai." }, 429);
  await page.goto(HUB);
  await page.getByRole("button", { name: "Xem ví dụ dựng sẵn" }).click();

  await expect(page.getByRole("alert")).toContainText("hết lượt thử hôm nay");
  await expect(page.locator(".d-rows")).toHaveCount(0);
});

test("an unreadable document is reported, never replaced with the sample", async ({ page }) => {
  await stub(page, "ckey", { error: "unreadable" }, 422);
  await page.goto(HUB);
  await page.getByRole("button", { name: "Xem ví dụ dựng sẵn" }).click();

  await expect(page.getByRole("alert")).toContainText("Không đọc được giấy tờ này");
  await expect(page.locator(".d-rows")).toHaveCount(0);
});

test("scripted-only backends hide own-upload instead of faking a read", async ({ page }) => {
  await stub(page, "demo");
  await page.goto(HUB);

  await expect(page.getByText("Hiện chỉ chạy được ví dụ dựng sẵn")).toBeVisible();
  await expect(page.getByRole("button", { name: "Xem ví dụ dựng sẵn" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Tải ảnh/ })).toHaveCount(0);
  // The panel that has nothing to offer explains itself rather than sitting empty.
  await expect(page.getByText(/Chúng tôi không hiển thị kết quả dựng sẵn/)).toBeVisible();

  // The conversation panel is hidden entirely in scripted mode: the canned map
  // covers the scenario and nothing else, so a typed line would come back as a
  // "[vi->en] …" echo dressed up as a translation.
  await expect(page.getByRole("button", { name: "Dịch câu này" })).toHaveCount(0);
});

test("the conversation panel appears only when translation is real", async ({ page }) => {
  await stub(page, "ckey");
  await page.goto(HUB);
  await expect(page.getByRole("button", { name: "Dịch câu này" })).toBeVisible();
});

test("a backend with no reader shows no demo at all", async ({ page }) => {
  await stub(page, "mock");
  await page.goto(HUB);

  await expect(page.getByText("Bản thử đang tạm dừng")).toBeVisible();
  await expect(page.getByRole("button", { name: "Xem ví dụ dựng sẵn" })).toHaveCount(0);
});

test("an unreachable backend fails closed", async ({ page }) => {
  await page.route("**/api/health", (route) => route.abort());
  await page.goto(HUB);
  await expect(page.getByText("Bản thử đang tạm dừng")).toBeVisible();
});

for (const colorScheme of ["light", "dark"] as const) {
  test(`the demo hub is accessible in ${colorScheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme });
    const page = await context.newPage();
    await stub(page, "ckey");
    await page.goto(HUB);
    await page.getByRole("button", { name: "Xem ví dụ dựng sẵn" }).click();
    await expect(page.locator(".d-rows")).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((v) => ["serious", "critical"].includes(v.impact ?? "")),
    ).toEqual([]);
    await context.close();
  });
}
