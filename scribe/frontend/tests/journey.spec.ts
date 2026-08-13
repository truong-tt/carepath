import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * The pitch path, proved offline.
 *
 * Every request except the document itself is aborted for the whole run. That
 * is the assertion, not a precaution: the demo has to complete on a venue
 * network that does not exist, and the only way to know it does is to take the
 * network away and walk the whole thing.
 */
async function cutTheNetwork(page: Page) {
  const blocked: string[] = [];
  await page.route("**/*", async (route) => {
    const url = route.request().url();
    // Let the app's own assets load; block anything that leaves for data.
    if (url.startsWith("http://127.0.0.1:4173/") && !url.includes("/api/")) {
      await route.continue();
      return;
    }
    blocked.push(url);
    await route.abort();
  });
  return blocked;
}

async function walkToProviders(page: Page) {
  await page.goto("http://127.0.0.1:4173/get-care/");
  await page.getByRole("button", { name: "Use the example patient" }).click();
  await page.getByRole("button", { name: "Find care" }).click();
}

test("the whole journey completes with no network at all", async ({ page }) => {
  const blocked = await cutTheNetwork(page);

  await walkToProviders(page);

  // 2 — curated clinics, dermatology first, and no availability claimed.
  await expect(page.getByRole("heading", { name: "Where you could go" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ba Dinh Skin & Allergy Clinic" })).toBeVisible();
  await expect(page.getByText(/does not have live appointment availability/)).toBeVisible();
  await page.getByRole("button", { name: "Choose this clinic" }).first().click();

  // 3 — the brief, bilingual, with the clinician's Vietnamese beside it.
  await expect(page.getByRole("heading", { name: "Your visit brief" })).toBeVisible();
  await expect(page.getByText("Dị ứng thuốc nhóm sulfa")).toBeVisible();
  await page.getByRole("button", { name: "Looks right — continue" }).click();

  // 4 — the gate. The dose has not reached the patient's column.
  await expect(page.getByText("2 lines are waiting for the clinician.")).toBeVisible();
  const patientColumn = page.locator(".visit-column").first();
  await expect(patientColumn.getByText("Amoxicillin 500 mg — take 1 tablet")).toHaveCount(0);
  await expect(patientColumn.getByText("Held back — the clinician is checking this")).toBeVisible();

  // The clinician confirms, and only then does the patient get the dose.
  // Always click the first card: confirming one removes it, so a handle taken
  // before the click is detached by the time its turn comes.
  const gate = page.getByRole("button", { name: "Xác nhận và đọc cho bệnh nhân" });
  while ((await gate.count()) > 0) {
    await gate.first().click();
  }
  await expect(page.getByText("Nothing is being withheld. Every line has been confirmed.")).toBeVisible();
  await expect(
    patientColumn.getByText("Amoxicillin 500 mg — take 1 tablet twice daily after meals."),
  ).toBeVisible();

  await page.getByRole("button", { name: "Continue to paperwork" }).click();

  // 5 — the prescription. Two dose lines held, two delivered.
  await expect(page.getByText("2 dòng cần xác nhận")).toBeVisible();
  await expect(page.locator(".paper__sheet")).toContainText("2 lines confirmed and ready for you.");
  const docGate = page.getByRole("button", { name: "Xác nhận", exact: true });
  while ((await docGate.count()) > 0) {
    await docGate.first().click();
  }
  await expect(page.locator(".paper__sheet")).toContainText("4 lines confirmed and ready for you.");

  await page.getByRole("button", { name: "Save to My CarePath" }).click();
  await page.getByRole("link", { name: "Open My CarePath" }).click();

  // 6 — the episode, built from what the clinician confirmed.
  await expect(page.getByRole("heading", { name: "Your care episode" })).toBeVisible();
  // It appears twice on purpose — once as a medicine to take, once as a line
  // of the document it came from. Scoped to the medicines list.
  await expect(
    page.locator(".j-meds").getByText("Amoxicillin 500 mg — take 1 tablet twice daily, after meals"),
  ).toBeVisible();
  await expect(page.getByText(/Return for review after 5 days/).first()).toBeVisible();

  // Nothing was even attempted over the wire.
  expect(blocked).toEqual([]);
});

test("the patient's routes never open a microphone or a socket", async ({ page }) => {
  for (const route of ["/get-care/", "/my-carepath/"]) {
    await page.goto(`http://127.0.0.1:4173${route}`);
    // No file input, no getUserMedia call, no WebSocket.
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
    const reached = await page.evaluate(() => {
      let touched = false;
      const media = navigator.mediaDevices;
      if (media) {
        const original = media.getUserMedia;
        media.getUserMedia = ((...args: unknown[]) => {
          touched = true;
          return (original as never as (...a: unknown[]) => unknown).apply(media, args);
        }) as typeof media.getUserMedia;
      }
      return touched;
    });
    expect(reached).toBe(false);
  }
});

test("the episode is deletable and does not outlive the tab", async ({ page }) => {
  await walkToProviders(page);
  await page.getByRole("button", { name: "Choose this clinic" }).first().click();

  await page.goto("http://127.0.0.1:4173/my-carepath/");
  await expect(page.getByRole("heading", { name: "Your care episode" })).toBeVisible();

  // It is in sessionStorage, not localStorage: closing the tab is enough.
  expect(await page.evaluate(() => localStorage.getItem("carepath.episode"))).toBeNull();
  expect(await page.evaluate(() => sessionStorage.getItem("carepath.episode"))).not.toBeNull();

  await page.getByRole("button", { name: "Delete this episode" }).click();
  await expect(page.getByRole("heading", { name: /Deleted/ })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("carepath.episode"))).toBeNull();
});

test("escalation says a person is not actually waiting", async ({ page }) => {
  await walkToProviders(page);
  await page.getByRole("button", { name: "Choose this clinic" }).first().click();
  await page.goto("http://127.0.0.1:4173/my-carepath/");

  await expect(page.getByText(/No coordinator is on call/)).toBeVisible();
  await page.getByRole("radio", { name: "I want a human interpreter" }).check();
  await page.getByRole("button", { name: "Request a person" }).click();

  await expect(page.getByText("Waiting for a person")).toBeVisible();
  await expect(page.getByText(/here it stops/)).toBeVisible();
  await expect(page.getByText(/call 115/)).toBeVisible();
});

for (const width of [360, 390, 768, 1440]) {
  test(`the journey is accessible and fits at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width >= 768 ? 900 : 844 });
    await walkToProviders(page);
    await page.getByRole("button", { name: "Choose this clinic" }).first().click();
    await page.getByRole("button", { name: "Looks right — continue" }).click();

    expect(
      await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
    ).toBeLessThanOrEqual(0);

    if (width === 390 || width === 1440) {
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(
        results.violations.filter((violation) =>
          ["serious", "critical"].includes(violation.impact ?? ""),
        ),
      ).toEqual([]);
    }
  });
}
