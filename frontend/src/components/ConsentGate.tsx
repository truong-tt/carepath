import { useState } from "react";

export type ConsentPayload = {
  ai_disclosure: boolean;
  interpreter_right: boolean;
  recorded_at: string;
  scope: "translation_aid";
};

type ConsentGateProps = {
  error: string | null;
  isSubmitting: boolean;
  onConsent: (payload: ConsentPayload) => void;
};

export function ConsentGate({ error, isSubmitting, onConsent }: ConsentGateProps) {
  const [aiDisclosure, setAiDisclosure] = useState(false);
  const [interpreterRight, setInterpreterRight] = useState(false);
  const canStart = aiDisclosure && interpreterRight && !isSubmitting;

  return (
    <main className="page">
      <section className="consent" aria-labelledby="consent-title">
        <div>
          <p className="eyebrow">AI translation disclosure</p>
          <h1 id="consent-title">CarePath Interpreter</h1>
          <p>
            This tool translates what each person says. It can make mistakes and does not
            provide medical advice, diagnoses, or drug recommendations.
          </p>
        </div>
        <div lang="vi">
          <p className="eyebrow">Thông báo sử dụng AI</p>
          <h2>Công cụ phiên dịch</h2>
          <p>
            Công cụ này chỉ phiên dịch lời nói. Kết quả có thể sai và không thay thế lời khuyên
            y tế, chẩn đoán, hoặc khuyến nghị dùng thuốc.
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
            AI translation may contain errors. / Bản dịch AI có thể có lỗi.
          </label>
          <label>
            <input
              checked={interpreterRight}
              type="checkbox"
              onChange={(event) => setInterpreterRight(event.target.checked)}
            />
            A human interpreter can be requested at any time. / Có thể yêu cầu thông dịch viên bất
            cứ lúc nào.
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button disabled={!canStart} type="submit">
            {isSubmitting ? "Starting..." : "Start session"}
          </button>
        </form>
      </section>
    </main>
  );
}
