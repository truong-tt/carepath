import { useState } from "react";

type Step = "conversation" | "clarified" | "draft" | "review";

const steps: Array<{ key: Step; label: string }> = [
  { key: "conversation", label: "1. Cuộc trao đổi" },
  { key: "clarified", label: "2. Nội dung được làm rõ" },
  { key: "draft", label: "3. Bản nháp có cấu trúc" },
  { key: "review", label: "4. Bác sĩ kiểm tra" },
];

export const soapDraft: Array<{ key: "s" | "o" | "a" | "p"; label: string; text: string }> = [
  {
    key: "s",
    label: "Triệu chứng chủ quan",
    text: "Đau tức ngực thoáng qua từ sáng, khó thở nhẹ. Chưa dùng thuốc.",
  },
  {
    key: "o",
    label: "Thông tin khách quan",
    text: "Chưa có kết quả khám hoặc cận lâm sàng trong nội dung ghi âm.",
  },
  { key: "a", label: "Nhận định", text: "Chờ bác sĩ nhập hoặc xác nhận." },
  { key: "p", label: "Kế hoạch", text: "Chờ bác sĩ nhập hoặc xác nhận." },
];

export default function ScribeShowcase() {
  const [step, setStep] = useState<Step>("conversation");

  return (
    <div className="scribe-panel guided-sample">
      <div className="scribe-panel__header">
        <p className="demo__brand">Ca khám mẫu đã làm sạch</p>
        <p className="demo__disclosure">Mô phỏng — không phải bệnh án thật</p>
      </div>
      <div className="scribe-tabs" aria-label="Các bước của ca khám mẫu">
        {steps.map(({ key, label }) => (
          <button
            aria-controls="guided-sample-panel"
            aria-pressed={step === key}
            className="scribe-tab"
            key={key}
            onClick={() => setStep(key)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      <div className="scribe-doc" id="guided-sample-panel">
        {step === "conversation" && (
          <>
            <p className="sample-speaker"><strong>Bệnh nhân:</strong> Tôi bị đau tức ngực thoáng qua từ sáng, hơi khó thở. Tôi chưa dùng thuốc.</p>
            <p className="sample-speaker"><strong>Bác sĩ:</strong> Anh đã có kết quả điện tâm đồ hoặc xét nghiệm nào chưa?</p>
            <p className="sample-speaker"><strong>Bệnh nhân:</strong> Chưa có.</p>
            <p className="scribe-caption">CarePath chỉ bắt đầu từ điều đã được nói trong cuộc trao đổi.</p>
          </>
        )}
        {step === "clarified" && (
          <>
            <p className="scribe-doc__text" lang="vi">
              Bệnh nhân đau tức ngực thoáng qua từ sáng, khó thở nhẹ. Chưa dùng
              thuốc. <mark className="scribe-mark scribe-mark--fix">Chưa có kết quả điện tâm đồ</mark> hoặc xét nghiệm trong nội dung ghi âm.
            </p>
            <p className="scribe-caption">Thông tin phủ định và thuật ngữ được làm rõ nhưng vẫn cần bác sĩ đối chiếu với âm thanh.</p>
          </>
        )}
        {step === "draft" && (
          <>
            <p className="scribe-status">Bản nháp — cần bác sĩ kiểm tra</p>
            <dl className="soap-note">
              {soapDraft.map((row) => (
                <div key={row.key}>
                  <dt><span aria-hidden="true">{row.key.toUpperCase()}</span>{row.label}</dt>
                  <dd lang="vi">{row.text}</dd>
                </div>
              ))}
            </dl>
            <p className="scribe-caption">CarePath không tự điền nhận định hay kế hoạch khi cuộc trao đổi chưa cung cấp.</p>
          </>
        )}
        {step === "review" && (
          <div className="review-checklist">
            <h3>Trước khi sử dụng bản nháp</h3>
            <ul>
              <li>Đối chiếu triệu chứng, thời điểm và thông tin phủ định với âm thanh.</li>
              <li>Kiểm tra phần còn thiếu hoặc chưa chắc chắn.</li>
              <li>Tự nhập hoặc xác nhận Nhận định và Kế hoạch.</li>
            </ul>
            <a className="button-link button-link--primary" href="/ghi-chep-lam-sang/">
              Mở công cụ và tải tệp âm thanh
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
