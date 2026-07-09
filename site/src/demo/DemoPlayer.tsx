import { FormEvent, useEffect, useMemo, useState } from "react";
import { getScenario, scenarios } from "./scenarios";
import { buildTranscript } from "./transcript";
import type { DemoTurn, PlaybackState } from "./types";

const TURN_DELAY_MS = 4000;

function downloadText(filename: string, content: string) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/plain;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function DemoPlayer() {
  const [scenarioId, setScenarioId] = useState(scenarios[0].id);
  const scenario = useMemo(() => getScenario(scenarioId), [scenarioId]);
  const [revealedCount, setRevealedCount] = useState(0);
  const [state, setState] = useState<PlaybackState>("idle");
  const [confirmedIds, setConfirmedIds] = useState<string[]>([]);
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [editValue, setEditValue] = useState("");
  const [customInput, setCustomInput] = useState("");
  const [customTurns, setCustomTurns] = useState<DemoTurn[]>([]);

  const revealedTurns = scenario.turns.slice(0, revealedCount);
  const pendingTurn =
    state === "awaiting-confirmation"
      ? scenario.turns[revealedCount - 1]
      : undefined;

  function reset(nextScenarioId = scenarioId) {
    setScenarioId(nextScenarioId);
    setRevealedCount(0);
    setState("idle");
    setConfirmedIds([]);
    setCorrections({});
    setEditValue("");
    setCustomTurns([]);
  }

  function advance() {
    if (
      state === "awaiting-confirmation" ||
      state === "escalated" ||
      state === "complete"
    ) {
      return;
    }
    const turn = scenario.turns[revealedCount];
    if (!turn) {
      setState("complete");
      return;
    }

    const nextCount = revealedCount + 1;
    setRevealedCount(nextCount);
    if (turn.escalation) {
      setState("escalated");
    } else if (turn.readback) {
      setEditValue(turn.en);
      setState("awaiting-confirmation");
    } else if (nextCount === scenario.turns.length) {
      setState("complete");
    }
  }

  useEffect(() => {
    if (state !== "playing") return;
    const timer = window.setTimeout(advance, TURN_DELAY_MS);
    return () => window.clearTimeout(timer);
  });

  function confirmPending() {
    if (!pendingTurn) return;
    setCorrections((current) => ({
      ...current,
      [pendingTurn.id]: editValue.trim() || pendingTurn.en,
    }));
    setConfirmedIds((current) => [...current, pendingTurn.id]);
    setState(
      revealedCount === scenario.turns.length ? "complete" : "playing",
    );
  }

  function submitCustom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = customInput.trim();
    if (!text) return;
    setCustomTurns((current) => [
      ...current,
      {
        id: `custom-${current.length + 1}`,
        speaker: "patient",
        sourceLanguage: "vi",
        vi: text,
        en: "Custom text received in the simulation. This is not a live translation.",
        riskTier: "low",
        riskSpans: [],
      },
    ]);
    setCustomInput("");
  }

  const allTranscriptTurns = [...revealedTurns, ...customTurns];
  const progress = [
    true,
    revealedCount > 0,
    confirmedIds.length > 0 || state === "escalated" || state === "complete",
    state === "complete",
  ];

  return (
    <section className="demo" aria-labelledby="demo-title">
      <header className="demo__header">
        <div>
          <p className="demo__brand">CarePath Translate</p>
          <h2 id="demo-title">Bản mô phỏng hội thoại</h2>
          <p className="demo__disclosure">
            Bản mô phỏng — không phải bản dịch trực tiếp
          </p>
        </div>
        <span className="demo__privacy">Không thu âm</span>
      </header>

      <div className="scenario-picker" aria-label="Chọn kịch bản">
        {scenarios.map((item) => (
          <button
            className={item.id === scenarioId ? "scenario is-selected" : "scenario"}
            key={item.id}
            onClick={() => reset(item.id)}
            type="button"
          >
            <strong>{item.title.vi}</strong>
            <span>{item.summary.vi}</span>
          </button>
        ))}
      </div>

      <ol className="progress-rail" aria-label="Tiến độ bản mô phỏng">
        {["Kịch bản đã chọn", "Nghe hội thoại", "Xác nhận read-back", "Nhận bản ghi"].map(
          (label, index) => (
            <li className={progress[index] ? "is-complete" : ""} key={label}>
              <span
                aria-hidden="true"
                className={progress[index] ? "progress-check" : ""}
              >
                {progress[index] ? "" : index + 1}
              </span>
              {label}
            </li>
          ),
        )}
      </ol>

      <div className="demo__controls">
        {state !== "playing" ? (
          <button
            className="button button--primary"
            onClick={() => setState("playing")}
            type="button"
            disabled={
              state === "awaiting-confirmation" ||
              state === "escalated" ||
              state === "complete"
            }
          >
            {state === "idle" ? "Bắt đầu" : "Tiếp tục"}
          </button>
        ) : (
          <button
            className="button button--secondary"
            onClick={() => setState("paused")}
            type="button"
          >
            Tạm dừng
          </button>
        )}
        <button
          className="button button--secondary"
          onClick={advance}
          type="button"
          disabled={
            state === "awaiting-confirmation" ||
            state === "escalated" ||
            state === "complete"
          }
        >
          Lượt tiếp theo
        </button>
        <button
          className="button button--text"
          onClick={() => reset()}
          type="button"
        >
          Phát lại
        </button>
      </div>

      <div className="transcript" aria-live="polite">
        {revealedTurns.length === 0 ? (
          <p className="transcript__empty">Hội thoại sẽ xuất hiện tại đây.</p>
        ) : (
          revealedTurns.map((turn) => {
            const blocked =
              (turn.id === pendingTurn?.id || turn.escalation) &&
              !confirmedIds.includes(turn.id);
            return (
              <article className={`turn turn--${turn.riskTier}`} key={turn.id}>
                <header>
                  <strong>
                    {turn.speaker === "doctor" ? "Bác sĩ" : "Bệnh nhân"}
                  </strong>
                  <span>{turn.riskTier}</span>
                </header>
                <div className="turn__columns">
                  <p lang="vi">{turn.vi}</p>
                  <p lang="en">
                    {blocked
                      ? "Bị chặn cho đến khi bác sĩ xác nhận."
                      : corrections[turn.id] ?? turn.en}
                  </p>
                </div>
                {turn.riskSpans.length > 0 && (
                  <ul className="risk-list" aria-label="Chi tiết rủi ro">
                    {turn.riskSpans.map((span, index) => (
                      <li key={`${span.kind}-${index}`}>{span.kind}: {span.vi}</li>
                    ))}
                  </ul>
                )}
              </article>
            );
          })
        )}
        {customTurns.map((turn) => (
          <article className="turn turn--custom" key={turn.id}>
            <header>
              <strong>Thử tự gõ</strong>
              <span>Mô phỏng</span>
            </header>
            <div className="turn__columns">
              <p>{turn.vi}</p>
              <p>{turn.en}</p>
            </div>
          </article>
        ))}
      </div>

      {pendingTurn?.readback && (
        <section className="readback" aria-labelledby="readback-title">
          <p className="readback__flag">Bản dịch đang bị chặn</p>
          <h3 id="readback-title">Xác nhận thông tin quan trọng</h3>
          <table>
            <thead>
              <tr>
                <th>Loại</th>
                <th>Nguồn</th>
                <th>Bản dịch</th>
              </tr>
            </thead>
            <tbody>
              {pendingTurn.readback.entities.map((entity) => (
                <tr key={`${entity.kind}-${entity.sourceText}`}>
                  <td>{entity.kind}</td>
                  <td>{entity.sourceText}</td>
                  <td>{entity.translatedText}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <label>
            Chỉnh bản dịch trước khi xác nhận
            <textarea
              value={editValue}
              onChange={(event) => setEditValue(event.target.value)}
            />
          </label>
          <div className="readback__actions">
            <button
              className="button button--primary"
              onClick={confirmPending}
              type="button"
            >
              Xác nhận và tiếp tục
            </button>
            <button
              className="button button--danger"
              onClick={() => setState("escalated")}
              type="button"
            >
              Yêu cầu phiên dịch viên
            </button>
          </div>
        </section>
      )}

      {state === "escalated" && (
        <section className="escalation" role="alert">
          <p>Đã dừng bản dịch tự động</p>
          <h3>Ưu tiên phiên dịch viên cho nội dung nguy cơ cao</h3>
          <p>
            Đây là luồng mô phỏng. Trong sản phẩm, nội dung này không được phát
            cho bệnh nhân trước khi có xác nhận phù hợp.
          </p>
          <button
            className="button button--primary"
            onClick={() => setState("complete")}
            type="button"
          >
            Xác nhận đã chuyển phiên dịch viên
          </button>
        </section>
      )}

      <form className="custom-input" onSubmit={submitCustom}>
        <label htmlFor="custom-line">Thử tự gõ một câu</label>
        <div>
          <input
            id="custom-line"
            value={customInput}
            onChange={(event) => setCustomInput(event.target.value)}
            placeholder="Nội dung chỉ được phản hồi bằng câu mẫu"
          />
          <button className="button button--secondary" type="submit">
            Thêm vào mô phỏng
          </button>
        </div>
        <small>Không phải dịch máy trực tiếp.</small>
      </form>

      {state === "complete" && (
        <button
          className="button button--download"
          onClick={() =>
            downloadText(
              `carepath-translate-${scenario.id}.txt`,
              buildTranscript(scenario, allTranscriptTurns, corrections),
            )
          }
          type="button"
        >
          Tải bản ghi demo
        </button>
      )}
    </section>
  );
}
