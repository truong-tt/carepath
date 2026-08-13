import { useState } from "react";
import { patchEpisode } from "../episode/episode";
import type { VisitNote } from "./types";
import "./visit.css";

function Section({ title, body }: { title: string; body: string }) {
  // Medication instructions arrive one per line, taken verbatim from the
  // confirmed prescription. A patient scans a list; they do not scan a
  // paragraph that has run three medicines together.
  const lines = (body ?? "").split("\n").map((line) => line.trim()).filter(Boolean);
  return (
    <div className="visit-doc__row">
      <dt>{title}</dt>
      <dd>
        {lines.length === 0 ? (
          "—"
        ) : lines.length === 1 ? (
          lines[0]
        ) : (
          <ul className="visit-doc__lines">
            {lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        )}
      </dd>
    </div>
  );
}

export default function VisitReview({
  note,
  onBack,
  onNewVisit,
  backHref = "/",
}: {
  note: VisitNote;
  onBack: () => void;
  onNewVisit?: () => void;
  backHref?: string;
}) {
  const [copied, setCopied] = useState<"clinical" | "patient" | null>(null);
  const [saved, setSaved] = useState(false);
  const { clinical_note: soap, patient_summary: summary } = note;

  /**
   * Carry the patient's half of this visit into their care episode.
   *
   * Only the patient summary, and only what the server already built from
   * confirmed turns: `_confirmed_medication_lines` in scribe/carepath/main.py
   * excludes anything the clinician did not release, so an unconfirmed line
   * cannot arrive here. The SOAP note is deliberately left behind — that is the
   * clinician's record, not the patient's copy.
   */
  const saveToEpisode = () => {
    patchEpisode({
      visitId: note.visit_id,
      status: "post_visit",
      source: "live",
      confirmedMedications: (summary.medications ?? "")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
      followUp: summary.follow_up || undefined,
    });
    setSaved(true);
  };

  const copy = async (which: "clinical" | "patient") => {
    const text =
      which === "clinical"
        ? `S: ${soap.subjective}\nO: ${soap.objective}\nA: ${soap.assessment}\nP: ${soap.plan}`
        : `What we discussed: ${summary.what_we_discussed}\n\nMedications: ${summary.medications}\n\nFollow-up: ${summary.follow_up}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(which);
    } catch {
      setCopied(null);
    }
  };

  return (
    <main className="visit visit--review">
      <header className="visit__bar">
        <h1>Hồ sơ sau khám</h1>
        <div className="visit__bar-actions">
          <button type="button" className="button button--secondary" onClick={onBack}>
            ← Quay lại ca khám
          </button>
          {onNewVisit ? (
            <button type="button" className="button button--secondary" onClick={onNewVisit}>
              Ca khám mới
            </button>
          ) : null}
          <a className="button button--secondary" href={backHref}>
            Trang chủ
          </a>
        </div>
      </header>

      <p className="visit-review__banner" role="note">
        Bản nháp do AI tạo từ nội dung đã trao đổi. Bác sĩ phải kiểm tra và xác nhận trước khi sử
        dụng hoặc đưa cho bệnh nhân.
      </p>

      {note.unconfirmed_turn_count > 0 ? (
        <p className="visit-review__withheld" role="alert">
          {note.unconfirmed_turn_count} lượt dịch chưa được bác sĩ xác nhận nên không được đưa vào
          hồ sơ. Quay lại ca khám để xác nhận nếu cần.
        </p>
      ) : null}

      <div className="visit-docs">
        <section className="visit-doc" aria-label="Bệnh án cho bác sĩ">
          <h2>
            Bệnh án <span className="visit-doc__lang">Tiếng Việt · cho bác sĩ</span>
          </h2>
          <dl className="visit-doc__body">
            <Section title="Chủ quan (S)" body={soap.subjective} />
            <Section title="Khách quan (O)" body={soap.objective} />
            <Section title="Đánh giá (A)" body={soap.assessment} />
            <Section title="Kế hoạch (P)" body={soap.plan} />
          </dl>
          {soap.missing_information.length > 0 ? (
            <div className="visit-doc__missing">
              <h3>Thiếu thông tin</h3>
              <ul>
                {soap.missing_information.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <button type="button" className="button button--secondary" onClick={() => copy("clinical")}>
            {copied === "clinical" ? "Đã sao chép" : "Sao chép bệnh án"}
          </button>
        </section>

        <section className="visit-doc" aria-label="After-visit summary for the patient">
          <h2>
            After-visit summary <span className="visit-doc__lang">English · for the patient</span>
          </h2>
          <dl className="visit-doc__body">
            <Section title="What we discussed" body={summary.what_we_discussed} />
            <Section title="Your medication" body={summary.medications} />
            <Section title="Follow-up" body={summary.follow_up} />
          </dl>
          {summary.allergies_noted.length > 0 ? (
            <div className="visit-doc__allergies">
              <h3>⚠️ Allergy noted</h3>
              <ul>
                {summary.allergies_noted.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="visit-doc__actions">
            <button
              type="button"
              className="button button--secondary"
              onClick={() => copy("patient")}
            >
              {copied === "patient" ? "Copied" : "Copy summary"}
            </button>
            {/* The patient's own device keeps the episode; this is the visit
                joining it. Nothing leaves the browser. */}
            <button type="button" className="button button--secondary" onClick={saveToEpisode}>
              {saved ? "Saved to My CarePath" : "Save to My CarePath"}
            </button>
            {saved ? (
              <a className="button button--secondary" href="/my-carepath/">
                Open My CarePath
              </a>
            ) : null}
          </div>
        </section>
      </div>

      <p className="visit-review__meta">
        {note.turn_count} lượt trao đổi · nguồn: nội dung đã được bác sĩ xác nhận trong ca khám
      </p>
    </main>
  );
}
