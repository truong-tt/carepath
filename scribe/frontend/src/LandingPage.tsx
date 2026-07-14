import { useRef, useState } from "react";
import logoUrl from "./assets/carepath.svg";
import { copyFor } from "./content/strings";
import { scenarios } from "./demo/scenarios";
import LeadForm from "./LeadForm";
import { leadContact, zaloHref } from "./leads";
import ScribeShowcase from "./scribe/ScribeShowcase";

const scribeHref = "/ghi-chep-lam-sang/";

export function formatMinutes(total: number): string {
  const rounded = Math.max(0, Math.round(total));
  const hours = Math.floor(rounded / 60);
  const minutes = rounded % 60;
  if (hours === 0) return `${minutes} phút`;
  if (minutes === 0) return `${hours} giờ`;
  return `${hours} giờ ${minutes} phút`;
}

export default function LandingPage() {
  const copy = copyFor("vi");
  const menuRef = useRef<HTMLDetailsElement>(null);
  const [patients, setPatients] = useState(28);
  const [minutesPerPatient, setMinutesPerPatient] = useState(5);
  const [afterHours, setAfterHours] = useState("sometimes");
  const [workplace, setWorkplace] = useState("clinic");
  const dailyMinutes = patients * minutesPerPatient;

  const navLinks = (
    <>
      <a href="#calculator">Thời gian ghi chép</a>
      <a href="#demo">Ca khám mẫu</a>
      <a href="#evidence">Bằng chứng</a>
      <a href="#start">Bắt đầu</a>
    </>
  );

  return (
    <div className="site-shell">
      <nav className="site-nav" aria-label="Điều hướng chính">
        <a className="site-nav__brand" href="#top" aria-label="CarePath">
          <img src={logoUrl} alt="" />
          <span>CarePath</span>
        </a>
        <div className="site-nav__links">{navLinks}</div>
        <details className="site-nav__menu" ref={menuRef}>
          <summary>Mở điều hướng</summary>
          <div
            onClick={(event) => {
              if (menuRef.current && (event.target as HTMLElement).closest("a")) {
                menuRef.current.open = false;
              }
            }}
          >
            {navLinks}
          </div>
        </details>
        <a className="nav-cta" href={scribeHref}>Bắt đầu ghi chép</a>
      </nav>

      <aside
        className="interpreter-status"
        aria-labelledby="interpreter-status-title"
        data-interpreter-status
      >
        <strong id="interpreter-status-title">Phiên dịch khám bệnh trực tiếp</strong>
        <span>Đang phát triển — hiện chưa thể truy cập trên web.</span>
      </aside>

      <main className="landing-main" id="top" tabIndex={-1}>
        <section className="onboarding-hero" aria-labelledby="onboarding-title">
          <h1 id="onboarding-title">
            Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.
          </h1>
          <div className="onboarding-hero__body">
            <div className="onboarding-hero__copy">
              <p>
                CarePath chuẩn bị ghi chú lâm sàng từ cuộc trao đổi để bác sĩ
                kiểm tra và xác nhận.
              </p>
              <div className="onboarding-hero__actions">
                <a className="button-link button-link--primary" href="#demo">
                  Trải nghiệm ca khám mẫu
                </a>
                <a className="button-link button-link--secondary" href="#calculator">
                  Tính thời gian ghi chép
                </a>
              </div>
              <small>
                Dùng tệp âm thanh đã được phép sử dụng. Bản nháp không tự đi vào hồ sơ.
              </small>
            </div>

            <div className="hero-proof" aria-label="Từ cuộc trao đổi đến bản nháp">
              <p className="hero-proof__title">Từ cuộc trao đổi đến bản nháp</p>
              <div className="hero-proof__stage">
                <span>Trong ghi âm</span>
                <p>
                  <strong>Bệnh nhân:</strong> Tôi bị đau tức ngực thoáng qua từ
                  sáng, hơi khó thở.
                </p>
              </div>
              <div className="hero-proof__stage hero-proof__stage--draft">
                <span>Bản nháp cho bác sĩ kiểm tra</span>
                <dl>
                  <div>
                    <dt>Triệu chứng chủ quan</dt>
                    <dd>Đau tức ngực thoáng qua từ sáng, khó thở nhẹ. Chưa dùng thuốc.</dd>
                  </div>
                  <div>
                    <dt>Thông tin khách quan</dt>
                    <dd>Chưa có kết quả cận lâm sàng trong nội dung ghi âm.</dd>
                  </div>
                </dl>
              </div>
              <p className="hero-proof__caption">
                Ca khám mẫu đã làm sạch. Nhận định và kế hoạch luôn thuộc về bác sĩ.
              </p>
            </div>
          </div>
        </section>

        <section className="burden-section" id="calculator" aria-labelledby="burden-title">
          <header className="compact-heading">
            <h2 id="burden-title">Một buổi khám không nên biến thành hai ca làm việc.</h2>
            <p>
              Hãy bắt đầu bằng thời gian bác sĩ đang dành cho ghi chép, không
              phải bằng một lời hứa tiết kiệm chưa được kiểm chứng.
            </p>
          </header>

          <div className="burden-layout">
            <form className="burden-calculator" onSubmit={(event) => event.preventDefault()}>
              <h3>Ước tính gánh nặng hiện tại</h3>
              <p>Con số chỉ dựa trên câu trả lời của bạn và không được gửi đi.</p>
              <div className="calculator-fields">
                <label>
                  Số người bệnh mỗi ngày
                  <input
                    max="200"
                    min="0"
                    onChange={(event) => setPatients(Math.min(200, Math.max(0, Number(event.target.value))))}
                    type="number"
                    value={patients}
                  />
                </label>
                <label>
                  Phút ghi chép cho mỗi người bệnh
                  <input
                    max="120"
                    min="0"
                    onChange={(event) => setMinutesPerPatient(Math.min(120, Math.max(0, Number(event.target.value))))}
                    type="number"
                    value={minutesPerPatient}
                  />
                </label>
                <label>
                  Bạn thường hoàn tất bệnh án sau giờ làm?
                  <select onChange={(event) => setAfterHours(event.target.value)} value={afterHours}>
                    <option value="never">Hiếm khi</option>
                    <option value="sometimes">Một vài ngày trong tuần</option>
                    <option value="often">Gần như mỗi ngày</option>
                  </select>
                </label>
                <label>
                  Nơi làm việc chính
                  <select onChange={(event) => setWorkplace(event.target.value)} value={workplace}>
                    <option value="clinic">Phòng khám</option>
                    <option value="hospital">Bệnh viện</option>
                    <option value="other">Cơ sở khác</option>
                  </select>
                </label>
              </div>
              <output className="calculator-result" aria-live="polite">
                <span>Thời gian ghi chép ước tính hiện tại</span>
                <strong>{formatMinutes(dailyMinutes)} mỗi ngày</strong>
                <small>{formatMinutes(dailyMinutes * 5)} cho 5 ngày làm việc</small>
              </output>
              <p className="calculator-formula">
                Công thức: {patients} người bệnh × {minutesPerPatient} phút. Tần
                suất ngoài giờ và nơi làm việc giúp bạn tự đối chiếu bối cảnh,
                không làm thay đổi phép tính.
              </p>
            </form>

            <div className="workflow-comparison">
              <article>
                <h3>Khi chưa có bản nháp</h3>
                <p>Nhớ lại cuộc trao đổi, gõ lại từng mục, rồi tự tìm phần còn thiếu.</p>
              </article>
              <article>
                <h3>Khi dùng CarePath</h3>
                <p>
                  Tải tệp đã được phép sử dụng, đọc lại lời chép và bắt đầu từ
                  một bản nháp có cấu trúc.
                </p>
              </article>
              <p>Bác sĩ vẫn là người sửa, bổ sung và quyết định bản cuối.</p>
            </div>
          </div>
        </section>

        <section className="demo-section" id="demo" aria-labelledby="demo-title">
          <header className="compact-heading compact-heading--wide">
            <h2 id="demo-title">Thử một ca khám mẫu trước khi tải tệp của bạn.</h2>
            <p>
              Đi qua bốn bước ngắn để thấy nội dung nào đến từ cuộc trao đổi,
              nội dung nào được làm rõ và phần nào bác sĩ phải tự xác nhận.
            </p>
          </header>
          <ScribeShowcase />
        </section>

        <section className="evidence-section" id="evidence" aria-labelledby="evidence-title">
          <header className="compact-heading compact-heading--wide">
            <h2 id="evidence-title">Bằng chứng được đặt đúng giới hạn.</h2>
            <p>
              Nhu cầu là có thật. Kết quả quốc tế đáng để học hỏi. Hiệu quả của
              CarePath tại Việt Nam vẫn cần được đo trong thí điểm.
            </p>
          </header>
          <div className="evidence-grid">
            <article>
              <h3>Bối cảnh Việt Nam</h3>
              <p>
                Một định mức ban hành năm 2015 từng đặt 33–45 lượt khám mỗi ngày
                tùy hạng bệnh viện, tương đương khoảng 11–15 phút cho mỗi lượt
                trong 8 giờ. Đây là mốc lịch sử, không phải số đo hiện tại.
              </p>
              <a href="https://baohiemxahoi.gov.vn/tintuc/Pages/linh-vuc-bao-hiem-xa-hoi.aspx?CateID=0&ItemID=8449">
                Xem nguồn Bảo hiểm xã hội Việt Nam
              </a>
            </article>
            <article>
              <h3>Kinh nghiệm quốc tế</h3>
              <p>
                Các nghiên cứu quan sát tại Singapore và Hoa Kỳ ghi nhận ít thời
                gian ghi chép hơn, nhiều giao tiếp bằng mắt hơn hoặc giảm kiệt
                sức sau khi dùng công cụ ghi chép môi trường. Đây không phải kết
                quả của CarePath.
              </p>
              <div className="evidence-links">
                <a href="https://medinform.jmir.org/2026/1/e85580">Nghiên cứu JMIR 2026</a>
                <a href="https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2839542">
                  Nghiên cứu JAMA Network Open
                </a>
              </div>
            </article>
            <article>
              <h3>Điều CarePath còn phải chứng minh</h3>
              <p>
                Chưa có dữ liệu triển khai CarePath tại Việt Nam. Thí điểm cần đo
                thời gian hoàn tất bệnh án, lỗi bác sĩ phải sửa và mức chấp nhận
                của người dùng trước khi đưa ra tuyên bố hiệu quả.
              </p>
            </article>
          </div>
        </section>

        <section className="trust-section" aria-labelledby="trust-title">
          <div>
            <h2 id="trust-title">Bác sĩ kiểm tra trước khi sử dụng.</h2>
            <p>
              CarePath hỗ trợ ghi chép, không thay thế nhận định lâm sàng và
              không tự đưa nội dung vào hồ sơ.
            </p>
          </div>
          <ul>
            <li>Luôn giữ nội dung nguồn để đối chiếu.</li>
            <li>Phần thiếu hoặc chưa chắc chắn phải được nhìn thấy.</li>
            <li>Không tự tạo chẩn đoán, tư vấn hoặc đơn thuốc.</li>
            <li>Âm thanh thô không được lưu sau khi xử lý yêu cầu.</li>
          </ul>
        </section>

        <section className="start-section" id="start" aria-labelledby="start-title">
          <div className="start-section__copy">
            <h2 id="start-title">Bắt đầu từ một tệp âm thanh đã được phép sử dụng.</h2>
            <p>
              Công cụ sẽ chỉ cho bạn từng bước tải tệp, tạo bản nháp và kiểm tra
              trước khi sử dụng.
            </p>
            <a className="button-link button-link--light" href={scribeHref}>
              Bắt đầu ghi chép
            </a>
          </div>
          <details className="pilot-disclosure">
            <summary>Dành cho cơ sở muốn thí điểm CarePath</summary>
            <div>
              <p>
                Để lại bối cảnh làm việc nếu cơ sở muốn cùng xác định cách thử
                nghiệm phù hợp. Biểu mẫu này chỉ dành cho Ghi chép bệnh án AI.
              </p>
              <LeadForm
                clinic=""
                specialty=""
                scenario={scenarios[0]}
                transcript=""
                language="vi"
                interest="scribe"
                hideInterestField
              />
            </div>
          </details>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <img src={logoUrl} alt="" />
          <strong>{copy.footer.promise}</strong>
        </div>
        <p>{copy.footer.honesty}</p>
        <div>
          <a href={`mailto:${leadContact.email}`}>{copy.footer.contact}</a>
          <a href={zaloHref}>Zalo · {leadContact.phone}</a>
        </div>
      </footer>
    </div>
  );
}
