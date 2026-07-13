import { useState } from "react";

import { copy, type Language } from "../copy";

type SessionChecklistProps = {
  language?: Language;
  delivered: boolean;
  confirmed: boolean;
  escalationLocated: boolean;
};

export function SessionChecklist({ language = "vi", delivered, confirmed, escalationLocated }: SessionChecklistProps) {
  const text = copy[language].checklist;
  const [dismissed, setDismissed] = useState(() => localStorage.getItem("carepath-session-checklist-dismissed") === "1");
  if (dismissed) return null;
  const dismiss = () => {
    localStorage.setItem("carepath-session-checklist-dismissed", "1");
    setDismissed(true);
  };
  return (
    <aside className="session-checklist" aria-label={text.title} aria-live="polite">
      <strong>{text.title}</strong>
      <ul>
        <li>{delivered ? "✓ " : "○ "}{text.delivered}</li>
        <li>{confirmed ? "✓ " : "○ "}{text.confirmed}</li>
        <li>{escalationLocated ? "✓ " : "○ "}{text.escalation}</li>
      </ul>
      <button type="button" onClick={dismiss}>{text.dismiss}</button>
    </aside>
  );
}
