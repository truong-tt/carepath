import { useState } from "react";
import { DocumentIcon } from "./icons";
import { riskLabel, SEVERITY_LABELS, type RiskSeverity } from "./riskLabels";
import { spokenText, type VisitTurn } from "./types";

/**
 * Review the lines read off one document.
 *
 * A conversation delivers one turn at a time, so one gate card per turn works.
 * A prescription delivers six at once, and six stacked full-size cards bury the
 * consultation. These share one frame and one warning, and each row carries only
 * what the clinician needs to decide: the Vietnamese as printed, the English the
 * patient would receive, and the entities the risk engine found.
 */
export default function DocumentReview({
  turns,
  onConfirm,
  busy,
  renderChips,
}: {
  turns: VisitTurn[];
  onConfirm: (turn: VisitTurn, edited?: string) => void;
  busy: boolean;
  renderChips: (turn: VisitTurn) => React.ReactNode;
}) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  if (turns.length === 0) return null;

  return (
    <section className="visit-docreview" aria-label="Giấy tờ cần bác sĩ xác nhận">
      <header className="visit-docreview__head">
        <h3>
          <DocumentIcon className="visit-glyph" />
          Giấy tờ vừa đọc
          <span className="visit-docreview__count">{turns.length} dòng cần xác nhận</span>
        </h3>
        <p>Bệnh nhân chưa nhìn thấy nội dung này.</p>
      </header>

      <ol className="visit-docreview__list">
        {turns.map((turn) => {
          const tier = SEVERITY_LABELS[turn.risk_tier as RiskSeverity]?.vi ?? turn.risk_tier;
          const isEditing = editing === turn.id;
          const checks = turn.risk_spans.filter((s) => riskLabel(s.kind).group === "check");
          return (
            <li key={turn.id} className={`visit-docrow visit-docrow--${turn.risk_tier}`}>
              <p className="visit-docrow__source">
                <span className={`visit-docrow__tier visit-docrow__tier--${turn.risk_tier}`}>
                  {tier}
                </span>
                {turn.source_text}
              </p>

              {isEditing ? (
                <textarea
                  className="visit-docrow__edit"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={2}
                  aria-label={`Sửa bản dịch: ${turn.source_text}`}
                />
              ) : (
                <p className="visit-docrow__target">{spokenText(turn)}</p>
              )}

              {renderChips(turn)}

              {checks.length > 0 ? (
                <p className="visit-docrow__checks">
                  {checks.map((s) => riskLabel(s.kind).vi).join(" · ")}
                </p>
              ) : null}

              <div className="visit-docrow__actions">
                <button
                  type="button"
                  className="button button--primary"
                  disabled={busy}
                  onClick={() => {
                    onConfirm(turn, isEditing ? draft : undefined);
                    setEditing(null);
                  }}
                >
                  {isEditing ? "Lưu và xác nhận" : "Xác nhận"}
                </button>
                {!isEditing ? (
                  <button
                    type="button"
                    className="button button--secondary"
                    onClick={() => {
                      setDraft(spokenText(turn));
                      setEditing(turn.id);
                    }}
                  >
                    Sửa
                  </button>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
