/**
 * Render public/og.png from the site's own design tokens and webfont.
 *
 * Rendered in a browser rather than drawn by hand so the share card cannot
 * drift away from the page it advertises: same Be Vietnam Pro, same navy,
 * same seal vermilion, same rules. Re-run after changing the palette.
 *
 *   node scripts/make-og.mjs
 */
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, "../public/og.png");
const fontsDir = resolve(here, "../node_modules/@fontsource/be-vietnam-pro/files");

const html = `<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><style>
@font-face{font-family:"BVP";font-weight:400;src:url("file:///${fontsDir.replaceAll("\\", "/")}/be-vietnam-pro-vietnamese-400-normal.woff2") format("woff2")}
@font-face{font-family:"BVP";font-weight:500;src:url("file:///${fontsDir.replaceAll("\\", "/")}/be-vietnam-pro-vietnamese-500-normal.woff2") format("woff2")}
@font-face{font-family:"BVP";font-weight:800;src:url("file:///${fontsDir.replaceAll("\\", "/")}/be-vietnam-pro-vietnamese-800-normal.woff2") format("woff2")}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1200px;height:630px;font-family:"BVP",sans-serif;background:#fff;color:#10141a;display:grid;grid-template-columns:1fr 1fr}
.left{padding:64px 40px 64px 64px;display:flex;flex-direction:column;justify-content:center}
.eyebrow{font-size:15px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#6b7686;margin-bottom:20px}
/* 46px keeps the Vietnamese headline to four lines with no orphan at 1200px.
   Leading stays 1.18 for the same measured reason as the page: stacked
   diacritics collide below it. */
h1{font-size:46px;font-weight:800;letter-spacing:-.03em;line-height:1.18}
h1 em{font-style:normal;color:#c41e22}
p{margin-top:24px;font-size:21px;line-height:1.55;color:#414a57;max-width:26ch}
.right{background:#0f2e5c;padding:56px 64px 56px 40px;display:flex;flex-direction:column;justify-content:center}
.doc{background:#fff;border:2px solid #10141a;box-shadow:10px 10px 0 rgba(255,255,255,.16)}
.doc__cap{padding:14px 20px;border-bottom:1px solid #c3ccda;text-align:center}
.doc__cap b{display:block;font-size:20px;font-weight:800;letter-spacing:.02em}
.doc__cap span{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#6b7686}
.row{padding:13px 20px;border-bottom:1px solid #c3ccda}
.row:last-child{border-bottom:0}
.row.held{background:#fbe6e6;border-left:4px solid #c41e22}
.vi{font-size:16px;font-weight:600;line-height:1.35}
.en{margin-top:5px;padding-left:11px;border-left:2px solid #dbe4f0;font-size:15px;color:#414a57;line-height:1.35}
.seal{display:inline-block;margin-top:6px;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#96181b;border:1.5px solid #c41e22;padding:3px 7px}
</style></head><body>
<div class="left">
  <div class="eyebrow">CarePath</div>
  <h1>Người bệnh nước ngoài rời phòng khám với tờ giấy <em>họ không đọc được.</em></h1>
  <p>CarePath dịch cả buổi khám và cả giấy tờ, rồi giữ lại phần nguy hiểm cho tới khi bác sĩ xác nhận.</p>
</div>
<div class="right">
  <div class="doc">
    <div class="doc__cap"><span>Phòng khám đa khoa</span><b>ĐƠN THUỐC</b></div>
    <div class="row held">
      <div class="vi">Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần</div>
      <div class="seal">Chờ bác sĩ xác nhận</div>
    </div>
    <div class="row">
      <div class="vi">Không uống rượu trong thời gian dùng thuốc</div>
      <div class="en">Do not drink alcohol while taking this medicine</div>
    </div>
    <div class="row">
      <div class="vi">Tái khám sau 5 ngày</div>
      <div class="en">Return for review after 5 days</div>
    </div>
  </div>
</div>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.setContent(html, { waitUntil: "networkidle" });
// Runs in the page, not in node — hence the string form.
await page.evaluate("document.fonts.ready");
await page.screenshot({ path: out });
await browser.close();
console.log(`wrote ${out}`);
