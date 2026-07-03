// CarePath demo — drives POST /api/v1/soap-notes and renders the SOAP draft.
(() => {
  "use strict";

  const API = {
    health: "/api/v1/health",
    soap: "/api/v1/soap-notes",
  };

  const el = (id) => document.getElementById(id);

  const dom = {
    form: el("soapForm"),
    dropzone: el("dropzone"),
    audioInput: el("audioInput"),
    fileChip: el("fileChip"),
    fileName: el("fileName"),
    fileSize: el("fileSize"),
    clearFile: el("clearFile"),
    contextInput: el("contextInput"),
    submitBtn: el("submitBtn"),
    uploadCard: el("uploadCard"),
    progressCard: el("progressCard"),
    errorCard: el("errorCard"),
    errorText: el("errorText"),
    retryBtn: el("retryBtn"),
    resultCard: el("resultCard"),
    reviewBanner: el("reviewBanner"),
    soapS: el("soapS"),
    soapO: el("soapO"),
    soapA: el("soapA"),
    soapP: el("soapP"),
    missingCard: el("missingCard"),
    missingList: el("missingList"),
    metaLine: el("metaLine"),
    copyBtn: el("copyBtn"),
    newBtn: el("newBtn"),
    healthBadge: el("healthBadge"),
  };

  let selectedFile = null;
  let stepTimers = [];
  let lastSoap = null;

  // ---------- Helpers ----------
  const fmtBytes = (n) => {
    if (!n && n !== 0) return "";
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
    return `${(n / 1024 / 1024).toFixed(1)} MB`;
  };

  const show = (node, visible) => { node.hidden = !visible; };

  // ---------- Lightweight SOAP markdown renderer (bullets + bold) ----------
  const escapeHtml = (s) =>
    s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // Escape first, then introduce only our own <strong> — safe against injection.
  const inlineMd = (s) => escapeHtml(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  const isBullet = (l) => /^[-*•]\s+/.test(l);
  const isNumbered = (l) => /^\d+[.)]\s+/.test(l);
  const stripMarker = (l) => l.replace(/^([-*•]|\d+[.)])\s+/, "");

  function renderRich(el, text) {
    el.textContent = "";
    const raw = (text || "").trim();
    if (!raw) return;
    const lines = raw.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    let i = 0;
    while (i < lines.length) {
      if (isBullet(lines[i]) || isNumbered(lines[i])) {
        const numbered = isNumbered(lines[i]);
        const list = document.createElement("ul");
        list.className = "soap-list" + (numbered ? " soap-list--num" : "");
        while (i < lines.length && (isBullet(lines[i]) || isNumbered(lines[i]))) {
          const li = document.createElement("li");
          li.innerHTML = inlineMd(stripMarker(lines[i]));
          list.appendChild(li);
          i++;
        }
        el.appendChild(list);
      } else {
        const p = document.createElement("p");
        p.innerHTML = inlineMd(lines[i]);
        el.appendChild(p);
        i++;
      }
    }
  }

  // ---------- Health badge ----------
  async function loadHealth() {
    const dot = dom.healthBadge.querySelector(".health-dot");
    const text = dom.healthBadge.querySelector(".health-text");
    try {
      const res = await fetch(API.health);
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json();
      const ready = data.asr_ready && data.llm_ready;
      const mock = String(data.asr_provider).includes("mock") || String(data.llm_provider) === "offline";
      dot.className = "health-dot " + (ready ? (mock ? "health-dot--degraded" : "health-dot--ok") : "health-dot--degraded");
      text.textContent = mock ? "Chế độ demo" : (ready ? "Hệ thống sẵn sàng" : "Một phần dịch vụ chưa sẵn sàng");
      dom.healthBadge.title = text.textContent;
    } catch (_) {
      dot.className = "health-dot health-dot--down";
      text.textContent = "Mất kết nối máy chủ";
      dom.healthBadge.title = "Không gọi được /api/v1/health";
    }
  }

  // ---------- File selection ----------
  function setFile(file) {
    selectedFile = file || null;
    if (selectedFile) {
      dom.fileName.textContent = selectedFile.name;
      dom.fileSize.textContent = fmtBytes(selectedFile.size);
      show(dom.fileChip, true);
    } else {
      show(dom.fileChip, false);
      dom.audioInput.value = "";
    }
    dom.submitBtn.disabled = !selectedFile;
  }

  dom.audioInput.addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) setFile(file);
  });

  dom.clearFile.addEventListener("click", () => setFile(null));

  // Keyboard activation of the dropzone label
  dom.dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); dom.audioInput.click(); }
  });

  // Drag & drop
  ["dragenter", "dragover"].forEach((evt) =>
    dom.dropzone.addEventListener(evt, (e) => { e.preventDefault(); dom.dropzone.classList.add("is-drag"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dom.dropzone.addEventListener(evt, (e) => { e.preventDefault(); dom.dropzone.classList.remove("is-drag"); })
  );
  dom.dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  // ---------- Progress stepper (cosmetic) ----------
  function startStepper() {
    const steps = dom.progressCard.querySelectorAll(".step");
    steps.forEach((s) => s.classList.remove("is-active", "is-done"));
    stepTimers.forEach(clearTimeout);
    stepTimers = [];

    const activate = (i) => {
      steps.forEach((s, idx) => {
        s.classList.toggle("is-done", idx < i);
        s.classList.toggle("is-active", idx === i);
      });
    };
    activate(0);
    stepTimers.push(setTimeout(() => activate(1), 1400));
    stepTimers.push(setTimeout(() => activate(2), 3200));
  }

  function finishStepper() {
    stepTimers.forEach(clearTimeout);
    stepTimers = [];
    dom.progressCard.querySelectorAll(".step").forEach((s) => {
      s.classList.remove("is-active");
      s.classList.add("is-done");
    });
  }

  // ---------- View state ----------
  function toState(state) {
    show(dom.uploadCard, state === "idle");
    show(dom.progressCard, state === "loading");
    show(dom.errorCard, state === "error");
    show(dom.resultCard, state === "result");
    if (state !== "result") dom.resultCard.classList.remove("in");
  }

  function revealResult() {
    // Restart the staggered SOAP entrance animation.
    dom.resultCard.classList.remove("in");
    void dom.resultCard.offsetWidth; // force reflow
    dom.resultCard.classList.add("in");
  }

  // ---------- Submit ----------
  dom.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    const body = new FormData();
    body.append("audio", selectedFile);
    const ctx = dom.contextInput.value.trim();
    if (ctx) body.append("encounter_context", ctx);

    dom.submitBtn.classList.add("is-loading");
    toState("loading");
    startStepper();

    try {
      const res = await fetch(API.soap, { method: "POST", body });
      const raw = await res.text();
      let data = null;
      try { data = raw ? JSON.parse(raw) : null; } catch (_) { /* non-JSON error body */ }

      if (!res.ok) {
        const detail = (data && (data.detail || data.message)) || raw || `HTTP ${res.status}`;
        throw new Error(detail);
      }
      finishStepper();
      renderResult(data);
      toState("result");
      revealResult();
      dom.resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      dom.errorText.textContent = err && err.message ? err.message : "Lỗi không xác định.";
      toState("error");
    } finally {
      dom.submitBtn.classList.remove("is-loading");
    }
  });

  dom.retryBtn.addEventListener("click", () => toState("idle"));
  dom.newBtn.addEventListener("click", () => { setFile(null); dom.contextInput.value = ""; toState("idle"); window.scrollTo({ top: 0, behavior: "smooth" }); });

  // ---------- Render ----------
  function renderResult(data) {
    const soap = (data && data.soap) || {};
    lastSoap = soap;

    renderRich(dom.soapS, soap.subjective);
    renderRich(dom.soapO, soap.objective);
    renderRich(dom.soapA, soap.assessment);
    renderRich(dom.soapP, soap.plan);

    show(dom.reviewBanner, soap.review_required !== false);

    const missing = Array.isArray(soap.missing_information) ? soap.missing_information.filter(Boolean) : [];
    dom.missingList.innerHTML = "";
    if (missing.length) {
      for (const item of missing) {
        const li = document.createElement("li");
        li.textContent = item;
        dom.missingList.appendChild(li);
      }
      show(dom.missingCard, true);
    } else {
      show(dom.missingCard, false);
    }

    const meta = (data && data.metadata) || {};
    const bits = [];
    if (meta.latency_ms != null) bits.push(`Xử lý trong ${(meta.latency_ms / 1000).toFixed(1)}s`);
    dom.metaLine.textContent = bits.length ? `${bits.join(" · ")} · CarePath` : "CarePath";
  }

  // ---------- Copy ----------
  dom.copyBtn.addEventListener("click", async () => {
    if (!lastSoap) return;
    const s = lastSoap;
    const md = (v) => (v || "-").replace(/\*\*/g, ""); // drop bold markers, keep bullets
    const text = [
      "BỆNH ÁN SOAP (bản nháp, cần bác sĩ kiểm tra)",
      "",
      `S - Chủ quan:\n${md(s.subjective)}`,
      "",
      `O - Khách quan:\n${md(s.objective)}`,
      "",
      `A - Đánh giá:\n${md(s.assessment)}`,
      "",
      `P - Kế hoạch:\n${md(s.plan)}`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      const old = dom.copyBtn.textContent;
      dom.copyBtn.textContent = "Đã sao chép ✓";
      setTimeout(() => { dom.copyBtn.textContent = old; }, 1600);
    } catch (_) {
      dom.copyBtn.textContent = "Không sao chép được";
    }
  });

  // ---------- Init ----------
  toState("idle");
  loadHealth();
})();
