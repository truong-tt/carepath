import { FormEvent, useEffect, useState } from "react";
import type { Language, Scenario } from "./demo/types";
import { buildLeadDraft, defaultLeadMessage } from "./leads";

interface LeadFormProps {
  language: Language;
  clinic: string;
  specialty: string;
  scenario: Scenario;
  transcript: string;
}

export default function LeadForm({
  language,
  clinic,
  specialty,
  scenario,
  transcript,
}: LeadFormProps) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [contact, setContact] = useState("");
  const [message, setMessage] = useState(() =>
    defaultLeadMessage(clinic, specialty, scenario, language),
  );
  const [messageDirty, setMessageDirty] = useState(false);
  const [draftReady, setDraftReady] = useState(false);

  useEffect(() => {
    if (!messageDirty) {
      setMessage(defaultLeadMessage(clinic, specialty, scenario, language));
    }
  }, [clinic, language, messageDirty, scenario, specialty]);

  function prepareDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    buildLeadDraft({
      clinic,
      specialty,
      scenario,
      transcript,
      language,
      fields: { name, role, contact, message },
    });
    setDraftReady(true);
  }

  const labels =
    language === "vi"
      ? {
          name: "Họ và tên",
          clinic: "Cơ sở y tế",
          role: "Vai trò",
          contact: "Email hoặc Zalo",
          message: "Lời nhắn",
          button: "Chuẩn bị yêu cầu thí điểm",
          ready: "Bản nháp đã sẵn sàng. Kết nối gửi sẽ được thêm ở bước tiếp theo.",
        }
      : {
          name: "Full name",
          clinic: "Clinic or hospital",
          role: "Role",
          contact: "Email or Zalo",
          message: "Message",
          button: "Prepare pilot request",
          ready: "The draft is ready. Submission will be connected in the next step.",
        };

  return (
    <form
      className="lead-form"
      data-transcript-length={transcript.length}
      onSubmit={prepareDraft}
    >
      <label>
        {labels.name}
        <input
          value={name}
          maxLength={120}
          onChange={(event) => setName(event.target.value)}
        />
      </label>
      <label>
        {labels.clinic}
        <input value={clinic} readOnly />
      </label>
      <label>
        {labels.role}
        <input
          value={role}
          maxLength={100}
          onChange={(event) => setRole(event.target.value)}
        />
      </label>
      <label>
        {labels.contact}
        <input
          value={contact}
          maxLength={160}
          onChange={(event) => setContact(event.target.value)}
        />
      </label>
      <label className="lead-form__message">
        {labels.message}
        <textarea
          value={message}
          maxLength={1200}
          onChange={(event) => {
            setMessage(event.target.value);
            setMessageDirty(true);
          }}
        />
      </label>
      <button className="button button--primary" type="submit">
        {labels.button}
      </button>
      <p aria-live="polite">{draftReady ? labels.ready : ""}</p>
    </form>
  );
}
