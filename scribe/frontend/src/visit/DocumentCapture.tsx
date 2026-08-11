import { DragEvent, useRef, useState } from "react";
import { CameraIcon, DocumentIcon, SpinnerIcon } from "./icons";
import type { VisitTurn } from "./types";

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

type CaptureState = "idle" | "reading" | "error" | "empty";

/**
 * Bring the Vietnamese paper into the visit.
 *
 * A foreign patient's language problem does not end with the conversation —
 * they leave holding a prescription they cannot read, and medication and
 * discharge are where harm concentrates. Every line read here becomes an
 * ordinary turn, so the risk engine and the clinician gate apply to paperwork
 * exactly as they do to speech.
 */
export default function DocumentCapture({
  visitId,
  onTurns,
  disabled = false,
}: {
  visitId: string;
  onTurns: (turns: VisitTurn[]) => void;
  disabled?: boolean;
}) {
  const [state, setState] = useState<CaptureState>("idle");
  const [dragging, setDragging] = useState(false);
  const [lastCount, setLastCount] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  async function send(file: File | null | undefined) {
    if (!file || disabled) return;
    setState("reading");
    const body = new FormData();
    body.append("image", file);
    try {
      const response = await fetch(`${API_BASE}/api/v1/visits/${visitId}/documents`, {
        method: "POST",
        body,
      });
      if (!response.ok) throw new Error(String(response.status));
      const turns = (await response.json()) as VisitTurn[];
      if (turns.length === 0) {
        setState("empty");
        return;
      }
      setLastCount(turns.length);
      setState("idle");
      onTurns(turns);
    } catch {
      // Nothing is partially added: the request either produced turns or none.
      setState("error");
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    void send(event.dataTransfer.files?.[0]);
  }

  const busy = state === "reading";

  return (
    <div className="visit-capture">
      <label
        className={`visit-capture__zone${dragging ? " is-drag" : ""}${busy ? " is-busy" : ""}`}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragging(false);
        }}
        onDrop={onDrop}
      >
        <span className="visit-capture__mark" aria-hidden="true">
          {busy ? <SpinnerIcon /> : <CameraIcon />}
        </span>
        <strong>{busy ? "Đang đọc giấy tờ…" : "Chụp giấy tờ"}</strong>
        <span className="visit-capture__hint">
          {busy ? "Giữ máy yên trong giây lát" : "Đơn thuốc, phiếu xét nghiệm, giấy ra viện"}
        </span>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          disabled={disabled || busy}
          onChange={(e) => void send(e.target.files?.[0])}
        />
      </label>

      {state === "error" ? (
        <p className="visit-capture__note visit-capture__note--bad" role="alert">
          Không đọc được giấy tờ. Thử lại hoặc gõ nội dung.
        </p>
      ) : null}

      {state === "empty" ? (
        <p className="visit-capture__note visit-capture__note--bad" role="alert">
          Không đọc được chữ nào. Chụp lại rõ hơn hoặc gõ nội dung.
        </p>
      ) : null}

      {state === "idle" && lastCount > 0 ? (
        <p className="visit-capture__note" role="status">
          <DocumentIcon />
          Đã đọc {lastCount} dòng. Bác sĩ xác nhận trước khi đưa cho bệnh nhân.
        </p>
      ) : null}
    </div>
  );
}
