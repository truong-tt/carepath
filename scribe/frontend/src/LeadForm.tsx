import { FormEvent, useEffect, useState } from "react";
import { copyFor } from "./content/strings";
import type { Language, Scenario } from "./demo/types";
import {
  buildLeadDraft,
  defaultLeadMessage,
  leadContact,
  submitLead,
  type LeadSubmissionConfig,
  type ProductInterest,
} from "./leads";

interface LeadFormProps {
  language: Language;
  clinic: string;
  specialty: string;
  scenario: Scenario;
  transcript: string;
  endpoint?: string;
  leadEmail?: string;
  fetcher?: typeof fetch;
  onMailto?: (url: string) => void;
  interest?: ProductInterest;
  onInterestChange?: (interest: ProductInterest) => void;
  hideInterestField?: boolean;
}

export default function LeadForm({
  language,
  clinic,
  specialty,
  scenario,
  transcript,
  endpoint = import.meta.env.VITE_LEAD_ENDPOINT,
  leadEmail = leadContact.email,
  fetcher,
  onMailto,
  interest: controlledInterest,
  onInterestChange,
  hideInterestField = false,
}: LeadFormProps) {
  const labels = copyFor(language).form;
  const [localInterest, setLocalInterest] = useState<ProductInterest>("both");
  const interest = controlledInterest ?? localInterest;
  const [name, setName] = useState("");
  const [clinicName, setClinicName] = useState(clinic);
  const [specialtyName, setSpecialtyName] = useState(specialty);
  const [role, setRole] = useState("");
  const [contact, setContact] = useState("");
  const [includeDemoContext, setIncludeDemoContext] = useState(false);
  const [message, setMessage] = useState(() =>
    defaultLeadMessage(clinic, specialty, scenario, language, interest),
  );
  const [messageDirty, setMessageDirty] = useState(false);
  const [status, setStatus] = useState<
    "idle" | "submitting" | "posted" | "mailto" | "error"
  >("idle");
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!messageDirty) {
      setMessage(
        defaultLeadMessage(
          clinicName,
          specialtyName,
          scenario,
          language,
          interest,
          includeDemoContext,
        ),
      );
    }
  }, [clinicName, includeDemoContext, interest, language, messageDirty, scenario, specialtyName]);

  async function sendRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    for (const [key, value] of Object.entries({
      name,
      clinic: clinicName,
      specialty: specialtyName,
      role,
      contact,
      message,
    })) {
      if (!value.trim()) nextErrors[key] = labels.required;
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const payload = buildLeadDraft({
      clinic: clinicName,
      specialty: specialtyName,
      scenario,
      transcript,
      language,
      interest,
      includeInterpreterContext: includeDemoContext,
      fields: { name, role, contact, message },
    });
    setStatus("submitting");
    try {
      const submissionConfig: LeadSubmissionConfig = {
        endpoint,
        email: leadEmail,
      };
      if (fetcher) submissionConfig.fetcher = fetcher;
      if (onMailto) submissionConfig.openMailto = onMailto;
      const result = await submitLead(payload, submissionConfig);
      setStatus(result);
    } catch {
      setStatus("error");
    }
  }

  return (
    <form
      className="lead-form"
      data-transcript-length={transcript.length}
      onSubmit={sendRequest}
      noValidate
    >
      <label>
        {labels.name}
        <input
          value={name}
          maxLength={120}
          aria-invalid={Boolean(errors.name)}
          aria-describedby={errors.name ? "lead-name-error" : undefined}
          onChange={(event) => setName(event.target.value)}
        />
        {errors.name && <span className="field-error" id="lead-name-error">{errors.name}</span>}
      </label>
      <label>
        {labels.clinic}
        <input
          value={clinicName}
          maxLength={160}
          aria-invalid={Boolean(errors.clinic)}
          aria-describedby={errors.clinic ? "lead-clinic-error" : undefined}
          onChange={(event) => setClinicName(event.target.value)}
        />
        {errors.clinic && <span className="field-error" id="lead-clinic-error">{errors.clinic}</span>}
      </label>
      <label>
        {labels.specialty}
        <input
          value={specialtyName}
          maxLength={100}
          aria-invalid={Boolean(errors.specialty)}
          aria-describedby={errors.specialty ? "lead-specialty-error" : undefined}
          onChange={(event) => setSpecialtyName(event.target.value)}
        />
        {errors.specialty && <span className="field-error" id="lead-specialty-error">{errors.specialty}</span>}
      </label>
      {interest !== "scribe" && (
        <label className="lead-form__context">
          <input
            checked={includeDemoContext}
            type="checkbox"
            onChange={(event) => setIncludeDemoContext(event.target.checked)}
          />
          {labels.includeDemoContext}
        </label>
      )}
      {!hideInterestField && (
        <label>
          {labels.interest}
          <select
            value={interest}
            onChange={(event) => {
              const nextInterest = event.target.value as ProductInterest;
              if (controlledInterest === undefined) {
                setLocalInterest(nextInterest);
              }
              onInterestChange?.(nextInterest);
            }}
          >
            <option value="interpreter">
              {labels.interestOptions.interpreter}
            </option>
            <option value="scribe">{labels.interestOptions.scribe}</option>
            <option value="both">{labels.interestOptions.both}</option>
          </select>
        </label>
      )}
      <label>
        {labels.role}
        <input
          value={role}
          maxLength={100}
          aria-invalid={Boolean(errors.role)}
          aria-describedby={errors.role ? "lead-role-error" : undefined}
          onChange={(event) => setRole(event.target.value)}
        />
        {errors.role && <span className="field-error" id="lead-role-error">{errors.role}</span>}
      </label>
      <label>
        {labels.contact}
        <input
          value={contact}
          maxLength={160}
          aria-invalid={Boolean(errors.contact)}
          aria-describedby={errors.contact ? "lead-contact-error" : undefined}
          onChange={(event) => setContact(event.target.value)}
        />
        {errors.contact && <span className="field-error" id="lead-contact-error">{errors.contact}</span>}
      </label>
      <label className="lead-form__message">
        {labels.message}
        <textarea
          value={message}
          maxLength={1200}
          aria-invalid={Boolean(errors.message)}
          aria-describedby={errors.message ? "lead-message-error" : undefined}
          onChange={(event) => {
            setMessage(event.target.value);
            setMessageDirty(true);
          }}
        />
        {errors.message && <span className="field-error" id="lead-message-error">{errors.message}</span>}
      </label>
      <button
        className="button button--primary"
        disabled={status === "submitting"}
        type="submit"
      >
        {status === "submitting"
          ? labels.submitting
          : endpoint
            ? labels.submit
            : labels.openMail}
      </button>
      <p className={status === "error" ? "form-status is-error" : "form-status"} aria-live="polite">
        {status === "posted"
          ? labels.posted
          : status === "mailto"
            ? labels.mailOpened
            : status === "error"
              ? labels.failed
              : ""}
      </p>
    </form>
  );
}
