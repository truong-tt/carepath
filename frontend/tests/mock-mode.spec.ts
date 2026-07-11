import { expect, test, type Locator, type Page } from "@playwright/test";

async function tabTo(page: Page, target: Locator) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Keyboard focus did not reach the expected control.");
}

async function startTypedConsole(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByLabel(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/).check();
  await page.getByLabel(/Tôi đã được giải thích rằng có thể yêu cầu phiên dịch viên trực tiếp/).check();
  await page.getByRole("button", { name: "Bắt đầu phiên dịch" }).click();
  await page.getByRole("button", { name: "Tiếp tục bằng văn bản" }).click();
  return page.locator(".input-region").filter({ has: page.getByRole("heading", { name: "Bác sĩ · Tiếng Việt" }) });
}

test("consent gates the mock-mode typed interpreter loop", async ({ page }) => {
  let clinicalRequests = 0;
  let webSockets = 0;
  await page.addInitScript(() => {
    let microphoneRequests = 0;
    const getUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    Object.defineProperty(window, "carepathMicrophoneRequests", { get: () => microphoneRequests });
    Object.defineProperty(window, "carepathSpeechCalls", { value: 0, writable: true });
    Object.defineProperty(window, "speechSynthesis", { value: { cancel() {}, speak() { (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls += 1; } } });
    Object.defineProperty(window, "SpeechSynthesisUtterance", { value: class { lang = ""; constructor(text: string) { void text; } } });
    navigator.mediaDevices.getUserMedia = async (...args) => {
      microphoneRequests += 1;
      return getUserMedia(...args);
    };
  });
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
  expect(await page.evaluate(() => (window as Window & { carepathMicrophoneRequests: number }).carepathMicrophoneRequests)).toBe(0);

  await page.getByLabel(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/).check();
  await page.getByLabel(/Tôi đã được giải thích rằng có thể yêu cầu phiên dịch viên trực tiếp/).check();
  await page.getByRole("button", { name: "Bắt đầu phiên dịch" }).click();
  await expect(page.getByRole("heading", { name: "Kiểm tra micrô trước khi bắt đầu" })).toBeVisible();
  await page.getByRole("button", { name: "Tiếp tục bằng văn bản" }).click();

  await expect(page.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  await expect(page.getByRole("status")).toContainText("Sẵn sàng");
  const doctorRegion = page.locator(".input-region").filter({ has: page.getByRole("heading", { name: "Bác sĩ · Tiếng Việt" }) });
  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();

  await expect(page.getByText("xin chao", { exact: true })).toBeVisible();
  await expect(page.getByText("[vi->en] xin chao", { exact: true })).toBeVisible();

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("uống 500 mg");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();

  await expect(page.getByText("Đã chặn, chờ bác sĩ xác nhận.")).toBeVisible();
  await page.getByRole("button", { name: "Mở bản xem xét" }).click();
  await expect(page.getByText("Cao: Liều lượng").first()).toBeVisible();
  await page.getByRole("button", { name: "Xác nhận và phát" }).click();
  await expect(page.getByText("Đã chặn, chờ bác sĩ xác nhận.")).toHaveCount(0);
  await expect(page.getByText("Cao · Đã xác nhận")).toBeVisible();

  await page.getByRole("button", { name: "Yêu cầu phiên dịch viên trực tiếp" }).click();
  await expect(page.getByRole("heading", { name: "Đã yêu cầu phiên dịch viên trực tiếp" })).toBeVisible();
  await expect(page.getByText("Đã tạm dừng phát tự động. Chỉ tiếp tục sau khi bác sĩ xác nhận phát cục bộ.")).toBeVisible();
  const speechCalls = await page.evaluate(() => (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls);
  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao sau leo thang");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await expect(page.getByText("[vi->en] xin chao sau leo thang", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls)).toBe(speechCalls);
  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("uống 500 mg sau leo thang");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await page.getByRole("button", { name: "Mở bản xem xét" }).click();
  await page.getByRole("button", { name: "Xác nhận và phát" }).click();
  expect(await page.evaluate(() => (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls)).toBe(speechCalls);
});

test("keeps playback fail-closed after a failed escalation until the clinician resumes", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "carepathSpeechCalls", { value: 0, writable: true });
    Object.defineProperty(window, "carepathSpeechCancels", { value: 0, writable: true });
    Object.defineProperty(window, "speechSynthesis", {
      value: {
        cancel() { (window as Window & { carepathSpeechCancels: number }).carepathSpeechCancels += 1; },
        speak() { (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls += 1; },
      },
    });
    Object.defineProperty(window, "SpeechSynthesisUtterance", { value: class { lang = ""; constructor(text: string) { void text; } } });
  });
  await page.route("**/api/sessions/*/escalate", (route) => route.fulfill({ status: 500 }));
  const doctorRegion = await startTypedConsole(page);
  const speechCalls = () => page.evaluate(() => (window as Window & { carepathSpeechCalls: number }).carepathSpeechCalls);

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao truoc khi leo thang");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await expect(page.getByText("[vi->en] xin chao truoc khi leo thang", { exact: true })).toBeVisible();
  const beforeEscalation = await speechCalls();
  const beforeEscalationCancels = await page.evaluate(() => (window as Window & { carepathSpeechCancels: number }).carepathSpeechCancels);

  await page.getByRole("button", { name: "Yêu cầu phiên dịch viên trực tiếp" }).click();
  expect(await page.evaluate(() => (window as Window & { carepathSpeechCancels: number }).carepathSpeechCancels)).toBe(beforeEscalationCancels + 1);
  await expect(page.getByText("Không thể đánh dấu đã yêu cầu phiên dịch viên.")).toBeVisible();

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao sau that bai");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await expect(page.getByText("[vi->en] xin chao sau that bai", { exact: true })).toBeVisible();
  expect(await speechCalls()).toBe(beforeEscalation);

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("uong 500 mg sau that bai");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await page.getByRole("button", { name: "Mở bản xem xét" }).click();
  await page.getByRole("button", { name: "Xác nhận và phát" }).click();
  expect(await speechCalls()).toBe(beforeEscalation);

  await page.getByRole("button", { name: "Tiếp tục phát tự động trên thiết bị này" }).click();
  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("xin chao sau tiep tuc");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await expect(page.getByText("[vi->en] xin chao sau tiep tuc", { exact: true })).toBeVisible();
  expect(await speechCalls()).toBe(beforeEscalation + 1);

  await doctorRegion.getByLabel("Nhập văn bản thay thế").fill("uong 500 mg sau tiep tuc");
  await doctorRegion.getByRole("button", { name: "Gửi" }).click();
  await page.getByRole("button", { name: "Mở bản xem xét" }).click();
  await page.getByRole("button", { name: "Xác nhận và phát" }).click();
  await expect.poll(speechCalls).toBe(beforeEscalation + 2);
});

test("supports keyboard-only onboarding through session end", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "carepathMicrophoneRequests", { value: 0, writable: true });
    const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = async (...args) => {
      (window as Window & { carepathMicrophoneRequests: number }).carepathMicrophoneRequests += 1;
      return original(...args);
    };
  });
  await page.goto("/");

  const next = page.getByRole("button", { name: "Tiếp tục" });
  await tabTo(page, next);
  await page.keyboard.press("Enter");
  await tabTo(page, next);
  await page.keyboard.press("Enter");

  const aiConsent = page.getByLabel(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/);
  const humanConsent = page.getByLabel(/Tôi đã được giải thích rằng có thể yêu cầu phiên dịch viên trực tiếp/);
  await expect(aiConsent).not.toBeChecked();
  await expect(humanConsent).not.toBeChecked();
  await tabTo(page, aiConsent);
  await page.keyboard.press("Space");
  await tabTo(page, humanConsent);
  await page.keyboard.press("Space");
  const start = page.getByRole("button", { name: "Bắt đầu phiên dịch" });
  await tabTo(page, start);
  await page.keyboard.press("Enter");

  await expect(page.getByRole("heading", { name: "Kiểm tra micrô trước khi bắt đầu" })).toBeVisible();
  expect(await page.evaluate(() => (window as Window & { carepathMicrophoneRequests: number }).carepathMicrophoneRequests)).toBe(0);
  const typed = page.getByRole("button", { name: "Tiếp tục bằng văn bản" });
  await tabTo(page, typed);
  await page.keyboard.press("Enter");

  const end = page.getByRole("button", { name: "Kết thúc phiên" });
  await tabTo(page, end);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Bắt đầu phiên dịch" })).toBeDisabled();
});

test("supports keyboard PTT, low-confidence recovery, and deletion", async ({ page }) => {
  await page.addInitScript(() => {
    const NativeWebSocket = window.WebSocket;
    const sockets: WebSocket[] = [];
    Object.defineProperty(window, "carepathSockets", { value: sockets });
    Object.defineProperty(window, "carepathTrackStops", { value: 0, writable: true });
    Object.defineProperty(window, "WebSocket", {
      value: class extends NativeWebSocket {
        constructor(url: string | URL, protocols?: string | string[]) {
          super(url, protocols);
          sockets.push(this);
        }
      },
    });
    Object.defineProperty(navigator.mediaDevices, "enumerateDevices", {
      value: async () => [{ deviceId: "mock-mic", groupId: "mock", kind: "audioinput", label: "Mock microphone", toJSON() { return {}; } }],
    });
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
      value: async () => ({
        getTracks: () => [{ stop() { (window as Window & { carepathTrackStops: number }).carepathTrackStops += 1; } }],
      }),
    });
    Object.defineProperty(window, "AudioContext", {
      value: class {
        createAnalyser() { return { fftSize: 32, getByteTimeDomainData(values: Uint8Array) { values.fill(128); } }; }
        createMediaStreamSource() { return { connect() {} }; }
        close() { return Promise.resolve(); }
      },
    });
    Object.defineProperty(window, "MediaRecorder", {
      value: class extends EventTarget {
        state: RecordingState = "inactive";
        start() { this.state = "recording"; }
        stop() { this.state = "inactive"; this.dispatchEvent(new Event("stop")); }
      },
    });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByLabel(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/).check();
  await page.getByLabel(/Tôi đã được giải thích rằng có thể yêu cầu phiên dịch viên trực tiếp/).check();
  await page.getByRole("button", { name: "Bắt đầu phiên dịch" }).click();
  await page.getByRole("button", { name: "Kiểm tra micrô" }).click();
  await expect(page.getByText("Micrô đã sẵn sàng.")).toBeVisible();
  await page.getByRole("button", { name: "Tiếp tục bằng micrô" }).click();

  const talk = page.getByRole("button", { name: "Nhấn giữ để nói" });
  await tabTo(page, talk);
  await page.keyboard.down("Space");
  await expect(page.getByRole("status")).toContainText("Đang ghi lời nói");
  await page.keyboard.up("Space");
  await expect(page.getByText("mock transcript", { exact: true })).toBeVisible();

  await page.evaluate(() => {
    const socket = (window as Window & { carepathSockets: WebSocket[] }).carepathSockets.at(-1);
    socket?.dispatchEvent(new MessageEvent("message", { data: JSON.stringify({
      type: "turn_result",
      low_confidence: true,
      requires_confirmation: false,
      turn: {
        id: "low-e2e", session_id: "e2e", seq: 2, speaker: "patient", src_lang: "en", tgt_lang: "vi",
        source_text: "hello", normalized_text: "hello", translation: "xin chào", asr_confidence: 0.4,
        mt_confidence: 0.9, risk_tier: "low", risk_spans: [], readback: null, status: "delivered",
        corrected_text: null, created_at: new Date(0).toISOString(),
      },
    }) }));
  });
  const typeRecovery = page.getByRole("button", { name: "Nhập văn bản" });
  await tabTo(page, typeRecovery);
  await page.keyboard.press("Enter");
  await expect(page.getByPlaceholder("Nhập nội dung cần dịch")).toBeFocused();
  const repeatRecovery = page.getByRole("button", { name: "Nói lại" });
  await tabTo(page, repeatRecovery);
  await page.keyboard.press("Enter");
  await expect(talk).toBeFocused();

  page.once("dialog", (dialog) => dialog.accept());
  const remove = page.getByRole("button", { name: "Xóa dữ liệu phiên" });
  await tabTo(page, remove);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Bắt đầu phiên dịch" })).toBeDisabled();
  expect(await page.evaluate(() => (window as Window & { carepathTrackStops: number }).carepathTrackStops)).toBeGreaterThan(1);
});
