import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const ROUTE = "http://127.0.0.1:4173/dich-giay-to/";

/** One held dose line and one delivered line, shaped like a real turn payload. */
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

async function stub(page: Page, providerMode = "ckey") {
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok", provider_mode: providerMode } }),
  );
  await page.route("**/api/sessions", (route) =>
    route.fulfill({ status: 201, json: { session_id: "s" } }),
  );
  await page.route("**/api/v1/visits/*/documents", (route) =>
    route.fulfill({ json: TURNS }),
  );
  await page.route("**/api/turns/*/confirm", (route) =>
    route.fulfill({ json: { ...TURNS[0], status: "confirmed", requires_confirmation: false } }),
  );
}

async function upload(page: Page) {
  await page.locator('input[type="file"]').setInputFiles({
    name: "don-thuoc.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("jpeg"),
  });
}

async function consent(page: Page) {
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Bắt đầu dịch giấy tờ" }).click();
}

// The reason this route can be a public door at all: reading a document needs
// no audio, so the route opens no socket and never asks for a microphone. If
// that ever stops being true it stops being a paperwork route, so it is
// asserted rather than left as an implementation detail.
test("the route never opens a socket and never asks for a microphone", async ({ page }) => {
  await stub(page);
  await page.addInitScript(() => {
    const w = window as unknown as { __sockets: string[]; __mic: number };
    w.__sockets = [];
    w.__mic = 0;
    const RealSocket = WebSocket;
    // @ts-expect-error test double
    window.WebSocket = function (url: string, protocols?: string | string[]) {
      w.__sockets.push(String(url));
      return new RealSocket(url, protocols);
    };
    if (navigator.mediaDevices) {
      navigator.mediaDevices.getUserMedia = () => {
        w.__mic += 1;
        return Promise.reject(new Error("blocked in test"));
      };
    }
  });

  await page.goto(ROUTE);
  await consent(page);
  await expect(page.getByText("Chụp giấy tờ")).toBeVisible();
  await upload(page);
  await expect(page.locator(".visit-docreview")).toContainText("Amoxicillin 500 mg");

  const probes = await page.evaluate(() => {
    const w = window as unknown as { __sockets: string[]; __mic: number };
    return { sockets: w.__sockets, mic: w.__mic };
  });
  expect(probes.sockets).toEqual([]);
  expect(probes.mic).toBe(0);
});

test("nothing is read before the clinician consents", async ({ page }) => {
  await stub(page);
  await page.goto(ROUTE);

  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Bắt đầu dịch giấy tờ" })).toBeDisabled();

  // The visit screen's wording, verbatim. Changing it is a safety decision.
  await expect(
    page.getByText(/CarePath là công cụ hỗ trợ dịch có thể sai/),
  ).toBeVisible();
  await expect(page.getByText(/quyền yêu cầu phiên dịch viên/)).toBeVisible();
});

// DEC-0022, extended to this surface: a held line's English is ABSENT, not
// hidden. A CSS-hidden string still ships to the browser.
test("a held dose line keeps its English out of the patient sheet", async ({ page }) => {
  await stub(page);
  await page.goto(ROUTE);
  await consent(page);
  await upload(page);

  const sheet = page.locator(".paper__sheet");
  await expect(sheet).toContainText("Return for review after 5 days");
  await expect(sheet).not.toContainText("take 1 tablet");

  // It is in the clinician's review pane, which is the only place it may be.
  await expect(page.locator(".visit-docreview")).toContainText("take 1 tablet");

  // Vietnamese left of the spine, English right of it, at the shared column.
  const geometry = await page.evaluate(() => {
    const row = document.querySelector(".paper__rows .p-reg") as HTMLElement | null;
    const vi = row?.querySelector(".p-reg__vi")?.getBoundingClientRect();
    const en = row?.querySelector(".p-reg__en")?.getBoundingClientRect();
    return vi && en ? { viRight: vi.right, enLeft: en.left } : null;
  });
  expect(geometry).not.toBeNull();
  expect(geometry!.enLeft).toBeGreaterThanOrEqual(geometry!.viRight);
});

test("confirming a held line moves it onto the patient sheet", async ({ page }) => {
  await stub(page);
  await page.goto(ROUTE);
  await consent(page);
  await upload(page);

  await expect(page.locator(".paper__rows > li")).toHaveCount(1);
  await page.getByRole("button", { name: "Xác nhận" }).click();

  await expect(page.locator(".paper__rows > li")).toHaveCount(2);
  await expect(page.locator(".paper__sheet")).toContainText("take 1 tablet");
  await expect(page.locator(".visit-docreview")).toHaveCount(0);
});

test("a backend that cannot read documents says so instead of offering to try", async ({ page }) => {
  await stub(page, "mock");
  await page.goto(ROUTE);

  await expect(page.getByText("Chưa đọc được giấy tờ")).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
});

test("the landing page offers the paperwork door", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173/");
  // Promoted to a hero CTA by the pivot: someone already holding Vietnamese
  // paper should not have to walk the first four steps of the journey.
  await expect(
    page.getByRole("link", { name: "I already have a prescription" }).first(),
  ).toHaveAttribute("href", "/dich-giay-to/");
});

for (const colorScheme of ["light", "dark"] as const) {
  test(`the paperwork route is accessible in ${colorScheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme });
    const page = await context.newPage();
    await stub(page);

    for (const width of [360, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: width >= 768 ? 900 : 844 });
      await page.goto(ROUTE);
      await consent(page);
      await upload(page);
      await expect(page.locator(".paper__sheet")).toBeVisible();

      // axe at the two widths the rest of the suite samples; the other two are
      // captured for the layout record.
      if (width === 390 || width === 1440) {
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
          .analyze();
        const serious = results.violations.filter((v) =>
          ["serious", "critical"].includes(v.impact ?? ""),
        );
        expect(serious, `axe ${colorScheme} ${width}`).toEqual([]);
      }

      expect(
        await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
      ).toBeLessThanOrEqual(0);

      await page.screenshot({
        fullPage: true,
        path: `../../docs/qa-evidence/cp-ux-19-${colorScheme}-${width}-paperwork.png`,
      });
    }

    await context.close();
  });
}
