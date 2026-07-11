import { useState } from "react";

import type { Language } from "../copy";

export type ConsentPayload = {
  ai_disclosure: boolean;
  interpreter_right: boolean;
  recorded_at: string;
  scope: "translation_aid";
};

type ConsentGateProps = {
  error: string | null;
  isSubmitting: boolean;
  language?: Language;
  onConsent: (payload: ConsentPayload) => void;
};

export function ConsentGate({ error, isSubmitting, language = "vi", onConsent }: ConsentGateProps) {
  const [aiDisclosure, setAiDisclosure] = useState(false);
  const [interpreterRight, setInterpreterRight] = useState(false);
  const canStart = aiDisclosure && interpreterRight && !isSubmitting;

  return (
    <main className="page" lang={language}>
      <section className="consent" aria-labelledby="consent-title">
        <div>
          <p className="eyebrow">Medical Interpreter</p>
          <h1 id="consent-title">Phiên dịch khám bệnh trực tiếp</h1>
          <p>
            Dịch hai chiều giữa bác sĩ tiếng Việt và bệnh nhân tiếng Anh trong lúc khám.
          </p>
        </div>
        <div>
          <p className="eyebrow">Các bước sử dụng</p>
          <ol className="consent-steps">
            <li>Bác sĩ nói tiếng Việt</li>
            <li>AI dịch sang tiếng Anh cho bệnh nhân</li>
            <li>Bệnh nhân trả lời bằng tiếng Anh</li>
            <li>AI dịch lại sang tiếng Việt cho bác sĩ</li>
          </ol>
          <p className="consent-reminder">
            CarePath chỉ hỗ trợ phiên dịch, không đưa ra chẩn đoán hoặc tư vấn điều trị.
            <br />
            <span lang="en">CarePath provides translation support only; it does not provide diagnoses or treatment advice.</span>
          </p>
        </div>
        <form
          className="consent-actions"
          onSubmit={(event) => {
            event.preventDefault();
            if (!canStart) {
              return;
            }
            onConsent({
              ai_disclosure: true,
              interpreter_right: true,
              recorded_at: new Date().toISOString(),
              scope: "translation_aid",
            });
          }}
        >
          <label>
            <input
              checked={aiDisclosure}
              type="checkbox"
              onChange={(event) => setAiDisclosure(event.target.checked)}
            />
            Bản dịch AI có thể có lỗi. <span lang="en">AI translation may contain errors.</span>
          </label>
          <label>
            <input
              checked={interpreterRight}
              type="checkbox"
              onChange={(event) => setInterpreterRight(event.target.checked)}
            />
            Có thể yêu cầu thông dịch viên bất cứ lúc nào. <span lang="en">A human interpreter can be requested at any time.</span>
          </label>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <button disabled={!canStart} type="submit">
            {isSubmitting ? "Đang bắt đầu…" : "Tiếp tục phiên dịch"}
          </button>
        </form>
      </section>
    </main>
  );
}
