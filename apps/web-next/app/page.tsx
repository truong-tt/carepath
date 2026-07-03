import type { Metadata } from "next";
import type { CSSProperties } from "react";
import LandingFx from "./landing-fx";
import "./css/phosphor/style.css";
import "./css/landing.css";

// Pixel-faithful port of apps/web/index.html. Same copy, sections, classes;
// styling comes verbatim from the copied styles.css + landing.css.

export const metadata: Metadata = {
  title: "CarePath · Trợ lý ghi chép y khoa AI cho phòng khám Việt Nam",
  description:
    "CarePath biến bản ghi âm buổi khám thành bản nháp bệnh án SOAP — hiểu cả tiếng Việt lẫn thuật ngữ tiếng Anh, để bác sĩ duyệt lần cuối.",
  openGraph: {
    type: "website",
    title: "CarePath · Trợ lý ghi chép y khoa AI",
    description:
      "Bác sĩ nói, CarePath soạn bệnh án SOAP nháp — hiểu cả tiếng Việt lẫn thuật ngữ tiếng Anh.",
    images: ["/assets/carepath-logo.png"],
  },
};

const accent = (v: string) => ({ "--accent": `var(${v})` }) as CSSProperties;

const WAVE_HEIGHTS = [
  0.3, 0.7, 0.45, 0.9, 0.55, 1, 0.4, 0.75, 0.5, 0.85, 0.35, 0.65,
  0.95, 0.5, 0.7, 0.3, 0.8, 0.45, 0.6, 0.9, 0.4, 0.55, 0.75, 0.35,
];

const HERO_SOAP = [
  { key: "S", ac: "--c-s", title: "Chủ quan", en: "Subjective", text: "BN nam 54 tuổi, đau ngực trái khi gắng sức 3 ngày, kèm khó thở nhẹ." },
  { key: "O", ac: "--c-o", title: "Khách quan", en: "Objective", text: "Mạch 92, HA 148/90 mmHg. Phổi trong, tim đều, không tiếng thổi." },
  { key: "A", ac: "--c-a", title: "Đánh giá", en: "Assessment", text: "Theo dõi cơn đau thắt ngực, tăng huyết áp chưa kiểm soát." },
  { key: "P", ac: "--c-p", title: "Kế hoạch", en: "Plan", text: "ECG, men tim. Hội chẩn tim mạch. Hẹn tái khám sau 3 ngày." },
];

const AUDIENCES = [
  {
    icon: "ph-stethoscope",
    who: "Bác sĩ",
    desc: "Ghi chú lâm sàng đầy đủ để chẩn đoán và điều trị.",
    docs: [{ label: "Bệnh án SOAP", live: true }, { label: "Thư chuyển tuyến" }],
  },
  {
    icon: "ph-first-aid",
    who: "Điều dưỡng",
    desc: "Bàn giao và y lệnh rõ ràng cho ca trực.",
    docs: [{ label: "Bàn giao điều dưỡng" }, { label: "Y lệnh & theo dõi" }],
  },
  {
    icon: "ph-user",
    who: "Bệnh nhân",
    desc: "Tóm tắt dễ hiểu về buổi khám và cách dùng thuốc.",
    docs: [{ label: "Tóm tắt sau khám" }, { label: "Hướng dẫn dùng thuốc" }],
  },
  {
    icon: "ph-hand-heart",
    who: "Người chăm sóc",
    desc: "Hướng dẫn chăm sóc và lịch nhắc tại nhà.",
    docs: [{ label: "Kế hoạch chăm sóc tại nhà" }, { label: "Lịch thuốc & tái khám" }],
  },
];

const FEATURE_CELLS = [
  { icon: "ph-translate", title: "Hiểu Việt-Anh", text: `Nhận đúng "BP", "ECG", "stent" trong câu tiếng Việt.` },
  { icon: "ph-list-checks", title: "Đánh dấu thiếu sót", text: "Thiếu tiền sử hay liều thuốc, CarePath nêu rõ để bổ sung." },
  { icon: "ph-copy", title: "Sao chép nhanh", text: "Một cú nhấp để dán bản nháp đã định dạng vào hồ sơ." },
  { icon: "ph-lock-key", title: "Riêng tư theo buổi khám", text: "Bản ghi chỉ dùng để soạn bệnh án cho buổi khám đó." },
];

const FAQS = [
  {
    q: "CarePath có thay thế bác sĩ không?",
    a: "Không. CarePath chỉ tạo bản nháp để bác sĩ rà soát, chỉnh sửa và phê duyệt. Bác sĩ luôn là người quyết định cuối cùng.",
  },
  {
    q: "CarePath tạo những loại tài liệu nào?",
    a: "Mục tiêu là cả bộ tài liệu cho ê-kíp chăm sóc: bệnh án SOAP cho bác sĩ, bàn giao cho điều dưỡng, tóm tắt sau khám cho bệnh nhân và hướng dẫn chăm sóc cho người nhà. Bản demo hiện tập trung vào bệnh án SOAP cho bác sĩ.",
  },
  {
    q: "Dữ liệu buổi khám được dùng thế nào?",
    a: "Tệp âm thanh chỉ được dùng để tạo bản nháp bệnh án cho buổi khám đó. Đây là bản trình diễn MVP, hãy chỉ dùng dữ liệu thử nghiệm, không dùng dữ liệu bệnh nhân thật.",
  },
  {
    q: "Hỗ trợ định dạng âm thanh nào?",
    a: "WAV, MP3, M4A, OGG và FLAC. Bạn có thể kéo thả tệp hoặc bấm để chọn từ máy.",
  },
  {
    q: "Có xử lý được tiếng Việt lẫn tiếng Anh không?",
    a: "Có. CarePath được thiết kế cho lời khám pha trộn Việt-Anh và ghi đúng các thuật ngữ y khoa tiếng Anh trong bệnh án.",
  },
  {
    q: "Bản nháp chính xác đến đâu?",
    a: "Đây là bản nháp, không phải bệnh án hoàn chỉnh. Chất lượng phụ thuộc vào độ rõ của bản ghi, và mọi kết quả đều cần bác sĩ kiểm tra trước khi sử dụng.",
  },
];

export default function LandingPage() {
  return (
    <div className="lp">
      <LandingFx />
      <a className="lp-skip" href="#noi-dung">Bỏ qua tới nội dung</a>
      <span id="lp-top-sentinel" aria-hidden="true"></span>

      {/* ============ NAV ============ */}
      <header className="lp-nav" id="lpNav">
        <div className="lp-container lp-nav-inner">
          <a className="lp-brand" href="/" aria-label="CarePath, trang chủ">
            <img src="/assets/carepath-mark.png" alt="" width={62} height={30} />
            <span className="lp-brand-name"><span className="nm-care">Care</span><span className="nm-path">Path</span></span>
          </a>

          <nav className="lp-nav-links" id="lpNavLinks" aria-label="Điều hướng chính">
            <a href="#thuat-ngu">Song ngữ</a>
            <a href="#quy-trinh">Cách dùng</a>
            <a href="#tai-lieu">Tài liệu</a>
            <a href="#an-toan">An toàn</a>
            <a href="#cau-hoi">Câu hỏi</a>
            <a className="lp-btn lp-btn-primary lp-btn-sm lp-nav-cta" href="/app">
              Dùng thử <i className="ph ph-arrow-right" aria-hidden="true"></i>
            </a>
          </nav>

          <button className="lp-burger" id="lpBurger" aria-label="Mở menu" aria-expanded="false" aria-controls="lpNavLinks">
            <span></span><span></span><span></span>
          </button>
        </div>
      </header>

      <main id="noi-dung">
        {/* ============ HERO ============ */}
        <section className="lp-hero">
          <div className="lp-container lp-hero-grid">
            <div className="lp-hero-copy reveal-on-scroll">
              <span className="lp-eyebrow">AI Scribe · Trợ lý ghi chép y khoa</span>
              <h1 className="lp-h1">
                Bác sĩ nói.<br />CarePath <span className="hl">soạn bệnh án</span>.
              </h1>
              <p className="lp-lead">
                Ghi âm buổi khám, CarePath soạn bản nháp bệnh án SOAP — hiểu cả tiếng Việt
                lẫn thuật ngữ tiếng Anh. Bác sĩ chỉ việc rà lại và duyệt.
              </p>
              <div className="lp-hero-cta">
                <a className="lp-btn lp-btn-primary" href="/app">
                  Thử với một bản ghi <i className="ph ph-arrow-right" aria-hidden="true"></i>
                </a>
                <a className="lp-btn lp-btn-ghost" href="#quy-trinh">Xem cách dùng</a>
              </div>
              <ul className="lp-strip" aria-label="Nguyên tắc thiết kế">
                <li><i className="ph ph-shield-check" aria-hidden="true"></i> Bác sĩ duyệt lần cuối</li>
                <li><i className="ph ph-translate" aria-hidden="true"></i> Hiểu thuật ngữ Việt-Anh</li>
                <li><i className="ph ph-file-text" aria-hidden="true"></i> Đúng cấu trúc SOAP</li>
              </ul>
            </div>

            {/* The real product pipeline: audio -> transcript -> SOAP. No stock photos. */}
            <div className="lp-hero-visual reveal-on-scroll">
              <div className="lp-preview">
                <figure className="lp-pipe-src">
                  <div className="lp-pipe-meta">
                    <i className="ph ph-microphone" aria-hidden="true"></i>
                    <span>Ghi âm buổi khám</span>
                    <span className="lp-pipe-time">04:12</span>
                  </div>
                  <div className="lp-wave" aria-hidden="true">
                    {WAVE_HEIGHTS.map((h, i) => (
                      <span key={i} style={{ "--h": h } as CSSProperties}></span>
                    ))}
                  </div>
                </figure>

                <div className="banner banner-review lp-preview-banner">
                  <i className="ph ph-warning" aria-hidden="true"></i>
                  <span>Bản nháp do AI tạo, <strong>cần bác sĩ duyệt</strong>.</span>
                </div>
                <div className="card soap-card lp-preview-card">
                  <div className="soap-inner">
                    {HERO_SOAP.map((s) => (
                      <article key={s.key} className="soap-section" style={accent(s.ac)}>
                        <div className="soap-badge">{s.key}</div>
                        <div className="soap-body">
                          <h3>{s.title} <span className="muted">/ {s.en}</span></h3>
                          <div className="soap-text"><p>{s.text}</p></div>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============ THE CODE-SWITCH PROBLEM (differentiator) ============ */}
        <section className="lp-section" id="thuat-ngu">
          <div className="lp-container">
            <p className="lp-kicker reveal-on-scroll"><span>01</span> Vấn đề</p>
            <div className="lp-lede-grid">
              <h2 className="lp-h2 reveal-on-scroll">Lời khám của bác sĩ Việt trộn cả tiếng Anh.</h2>
              <p className="lp-lede-sub reveal-on-scroll">
                &quot;BP&quot;, &quot;ECG&quot;, &quot;stent&quot;, &quot;troponin&quot; nói xen giữa câu tiếng Việt. CarePath hiểu
                và ghi đúng những thuật ngữ đó trong bệnh án, thay vì bỏ sót hay viết sai.
              </p>
            </div>

            <div className="lp-fix reveal-on-scroll">
              <span className="lp-fix-tag">Ví dụ thuật ngữ trong bệnh án</span>
              <p>&quot;...cho làm <b>ECG</b>, thử <b>troponin</b>, <b>HA 148/90 mmHg</b>...&quot;</p>
            </div>
          </div>
        </section>

        {/* ============ HOW IT WORKS ============ */}
        <section className="lp-section lp-section--paper" id="quy-trinh">
          <div className="lp-container">
            <p className="lp-kicker reveal-on-scroll"><span>02</span> Cách dùng</p>
            <h2 className="lp-h2 reveal-on-scroll">Ba bước để có bản nháp bệnh án</h2>

            <ol className="lp-flow">
              <li className="lp-flow-node reveal-on-scroll">
                <span className="lp-flow-num">1</span>
                <h3>Ghi âm buổi khám</h3>
                <p>Bật ghi âm khi khám, tải tệp lên CarePath khi xong.</p>
              </li>
              <li className="lp-flow-node reveal-on-scroll">
                <span className="lp-flow-num">2</span>
                <h3>Nhận bản nháp SOAP</h3>
                <p>CarePath soạn bệnh án SOAP cho buổi khám trong vài giây.</p>
              </li>
              <li className="lp-flow-node reveal-on-scroll">
                <span className="lp-flow-num">3</span>
                <h3>Rà soát &amp; duyệt</h3>
                <p>Bác sĩ chỉnh sửa, bổ sung và phê duyệt lần cuối.</p>
              </li>
            </ol>
          </div>
        </section>

        {/* ============ AUDIENCES -> DOCUMENTS ============ */}
        <section className="lp-section" id="tai-lieu">
          <div className="lp-container">
            <p className="lp-kicker reveal-on-scroll"><span>03</span> Tài liệu</p>
            <div className="lp-lede-grid">
              <h2 className="lp-h2 reveal-on-scroll">Một buổi khám, nhiều tài liệu</h2>
              <p className="lp-lede-sub reveal-on-scroll">Từ một bản ghi âm, CarePath hướng tới bộ tài liệu cho cả ê-kíp chăm sóc. Bản demo hiện tạo bệnh án SOAP cho bác sĩ.</p>
            </div>

            <ul className="lp-aud">
              {AUDIENCES.map((aud) => (
                <li key={aud.who} className="lp-aud-row reveal-on-scroll">
                  <div className="lp-aud-who">
                    <span className="lp-aud-icon"><i className={`ph ${aud.icon}`} aria-hidden="true"></i></span>
                    <div>
                      <h3>{aud.who}</h3>
                      <p>{aud.desc}</p>
                    </div>
                  </div>
                  <div className="lp-aud-docs">
                    {aud.docs.map((doc) =>
                      doc.live ? (
                        <span key={doc.label} className="lp-doc-chip lp-doc-chip--live"><i className="ph ph-check" aria-hidden="true"></i>{doc.label}</span>
                      ) : (
                        <span key={doc.label} className="lp-doc-chip">{doc.label}</span>
                      )
                    )}
                  </div>
                </li>
              ))}
            </ul>

            <p className="lp-aud-note reveal-on-scroll">
              <span className="lp-doc-chip lp-doc-chip--live lp-doc-chip--mini"><i className="ph ph-check" aria-hidden="true"></i>Có trong demo</span>
              <span>Bản demo hiện tạo bệnh án SOAP cho bác sĩ. Các tài liệu còn lại thuộc bộ tài liệu đầy đủ của CarePath.</span>
            </p>
          </div>
        </section>

        {/* ============ FEATURES ============ */}
        <section className="lp-section lp-section--paper" id="tinh-nang">
          <div className="lp-container">
            <p className="lp-kicker reveal-on-scroll"><span>04</span> Tính năng</p>
            <h2 className="lp-h2 reveal-on-scroll">Dựng quanh thực tế phòng khám Việt Nam</h2>

            <div className="lp-feat">
              <article className="lp-feat-lead reveal-on-scroll">
                <div className="lp-soap-keys" aria-hidden="true">
                  <span style={accent("--c-s")}>S</span>
                  <span style={accent("--c-o")}>O</span>
                  <span style={accent("--c-a")}>A</span>
                  <span style={accent("--c-p")}>P</span>
                </div>
                <h3>Đúng cấu trúc SOAP</h3>
                <p>Chủ quan, Khách quan, Đánh giá, Kế hoạch — mỗi thông tin về đúng mục, sẵn sàng để bác sĩ rà và ký.</p>
              </article>

              {FEATURE_CELLS.map((cell) => (
                <article key={cell.title} className="lp-feat-cell reveal-on-scroll">
                  <i className={`ph ${cell.icon} lp-feat-glyph`} aria-hidden="true"></i>
                  <h3>{cell.title}</h3>
                  <p>{cell.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ============ SAFETY ============ */}
        <section className="lp-safety" id="an-toan">
          <div className="lp-container lp-safety-inner reveal-on-scroll">
            <span className="lp-safety-icon"><i className="ph ph-shield-check" aria-hidden="true"></i></span>
            <h2 className="lp-h2">AI hỗ trợ, bác sĩ quyết định</h2>
            <p>
              CarePath chỉ tạo bản nháp. Mọi kết quả đều kèm cảnh báo cần kiểm tra và
              không được dùng cho chẩn đoán lâm sàng chính thức khi chưa có bác sĩ duyệt.
              Bản trình diễn này không thay thế phán đoán y khoa.
            </p>
          </div>
        </section>

        {/* ============ FAQ ============ */}
        <section className="lp-section" id="cau-hoi">
          <div className="lp-container lp-faq-wrap">
            <p className="lp-kicker reveal-on-scroll"><span>05</span> Câu hỏi</p>
            <h2 className="lp-h2 reveal-on-scroll">Câu hỏi thường gặp</h2>

            <div className="lp-faq reveal-on-scroll">
              {FAQS.map((f) => (
                <details key={f.q} className="lp-faq-item">
                  <summary>{f.q}<i className="ph ph-caret-down" aria-hidden="true"></i></summary>
                  <div className="lp-faq-body"><p>{f.a}</p></div>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* ============ FINAL CTA ============ */}
        <section className="lp-cta">
          <div className="lp-container lp-cta-inner reveal-on-scroll">
            <h2 className="lp-cta-title">Thử CarePath với một bản ghi</h2>
            <p>Tải lên một đoạn ghi âm buổi khám và xem bản nháp SOAP trong vài giây.</p>
            <a className="lp-btn lp-btn-onaccent" href="/app">
              Dùng thử <i className="ph ph-arrow-right" aria-hidden="true"></i>
            </a>
            {/* QR for desktop visitors: jump to the tool on a phone (recording lives there).
                Regenerate when the prod URL is final (Goal 5):
                npx qrcode -t svg -o public/qr-app.svg "https://<prod-domain>/app" */}
            <div className="lp-qr" aria-label="Mã QR mở trang ghi âm trên điện thoại">
              <img src="/qr-app.svg" alt="Mã QR dẫn tới trang ghi âm CarePath" width={112} height={112} />
              <span>Mở trên điện thoại để ghi âm</span>
            </div>
          </div>
        </section>
      </main>

      {/* ============ FOOTER ============ */}
      <footer className="lp-footer">
        <div className="lp-container lp-footer-inner">
          <div className="lp-footer-brand">
            <img src="/assets/carepath-mark.png" alt="" width={56} height={27} />
            <div>
              <span className="lp-brand-name"><span className="nm-care">Care</span><span className="nm-path">Path</span></span>
              <p className="lp-footer-tag">Trợ lý ghi chép y khoa AI cho nhân viên y tế Việt Nam.</p>
            </div>
          </div>
          <nav className="lp-footer-links" aria-label="Liên kết chân trang">
            <a href="#quy-trinh">Cách dùng</a>
            <a href="#tai-lieu">Tài liệu</a>
            <a href="#an-toan">An toàn</a>
            <a href="/app">Dùng thử</a>
          </nav>
        </div>
        <div className="lp-container lp-footer-base">
          <span>CarePath · Bản demo cho nhân viên y tế Việt Nam</span>
          <span className="lp-footer-disclaimer">Không dùng cho chẩn đoán lâm sàng chính thức.</span>
        </div>
      </footer>
    </div>
  );
}
