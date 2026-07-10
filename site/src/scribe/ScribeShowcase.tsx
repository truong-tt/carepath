import { useState } from "react";
import { copyFor } from "../content/strings";
import type { Language } from "../demo/types";

type Step = "raw" | "corrected" | "soap";

interface Segment {
  text: string;
  mark?: "miss" | "fix";
}

// Sanitized sample dictation for the simulation. Every SOAP line in this
// fixed example is traceable to the sample content below.
const rawSegments: Segment[] = [
  { text: "bệnh nhân nữ 54 tuổi tiền sử tăng huyết áp đang dùng " },
  { text: "am lô đi pin", mark: "miss" },
  { text: " " },
  { text: "5 mi li gam", mark: "miss" },
  { text: " mỗi sáng hôm nay đau đầu chóng mặt huyết áp tự đo tại nhà " },
  { text: "một sáu mươi trên chín mươi", mark: "miss" },
  {
    text: " không đau ngực không khó thở chẩn đoán tăng huyết áp chưa kiểm soát kế hoạch đo lại huyết áp tại phòng khám theo dõi huyết áp mỗi sáng tái khám sau một tuần",
  },
];

const correctedSegments: Segment[] = [
  { text: "Bệnh nhân nữ 54 tuổi, tiền sử tăng huyết áp, đang dùng " },
  { text: "amlodipin", mark: "fix" },
  { text: " " },
  { text: "5 mg", mark: "fix" },
  { text: " mỗi sáng. Hôm nay đau đầu, chóng mặt; huyết áp tự đo tại nhà " },
  { text: "160/90 mmHg", mark: "fix" },
  {
    text: ". Không đau ngực, không khó thở. Chẩn đoán: tăng huyết áp chưa kiểm soát. Kế hoạch: đo lại huyết áp tại phòng khám, theo dõi huyết áp mỗi sáng, tái khám sau một tuần.",
  },
];

export const soapDraft: Array<{ key: "s" | "o" | "a" | "p"; text: string }> = [
  { key: "s", text: "Đau đầu, chóng mặt từ sáng nay. Không đau ngực, không khó thở." },
  {
    key: "o",
    text: "Huyết áp tự đo tại nhà 160/90 mmHg. Tiền sử tăng huyết áp, đang dùng amlodipin 5 mg mỗi sáng.",
  },
  { key: "a", text: "Tăng huyết áp chưa kiểm soát." },
  {
    key: "p",
    text: "Đo lại huyết áp tại phòng khám. Theo dõi huyết áp tại nhà mỗi sáng; tái khám sau một tuần.",
  },
];

function SampleText({ segments }: { segments: Segment[] }) {
  return (
    <p className="scribe-doc__text" lang="vi">
      {segments.map((segment, index) =>
        segment.mark ? (
          <mark
            className={`scribe-mark scribe-mark--${segment.mark}`}
            key={`${segment.text}-${index}`}
          >
            {segment.text}
          </mark>
        ) : (
          segment.text
        ),
      )}
    </p>
  );
}

export default function ScribeShowcase({ language }: { language: Language }) {
  const copy = copyFor(language).scribe;
  const [step, setStep] = useState<Step>("raw");
  const steps: Step[] = ["raw", "corrected", "soap"];

  return (
    <div className="scribe-panel">
      <div className="scribe-panel__header">
        <p className="demo__brand">{copy.brand}</p>
        <p className="demo__disclosure">{copy.disclosure}</p>
      </div>
      <div className="scribe-tabs">
        {steps.map((value) => (
          <button
            aria-pressed={step === value}
            className="scribe-tab"
            key={value}
            onClick={() => setStep(value)}
            type="button"
          >
            {copy.steps[value].label}
          </button>
        ))}
      </div>
      <div className="scribe-doc">
        {step === "soap" ? (
          <>
            <p className="scribe-status">{copy.status}</p>
            <dl className="soap-note">
              {soapDraft.map((row) => (
                <div key={row.key}>
                  <dt>
                    <span aria-hidden="true">{row.key.toUpperCase()}</span>
                    {copy.soapLabels[row.key]}
                  </dt>
                  <dd lang="vi">{row.text}</dd>
                </div>
              ))}
            </dl>
          </>
        ) : (
          <SampleText segments={step === "raw" ? rawSegments : correctedSegments} />
        )}
        <p className="scribe-caption">{copy.steps[step].caption}</p>
      </div>
    </div>
  );
}
