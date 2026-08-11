// Every span kind the risk engine emits (interpreter/app/risk/engine.py).
// Anything missing here renders as a generic "item to check", which tells a
// clinician nothing -- so tests/test_risk_labels.py fails the build if the
// engine gains a kind that is not listed below.

export type RiskKind =
  | "red_flag"
  | "allergy"
  | "pregnancy"
  | "symptom_severity"
  | "drug_name"
  | "dose_number"
  | "frequency_duration"
  | "route"
  | "laterality"
  | "body_location"
  | "medical_history"
  | "negation"
  | "negation_mismatch"
  | "number_mismatch"
  | "abbreviation"
  | "subject_omission"
  | "pronoun"
  | "low_confidence";

export type RiskSeverity = "low" | "medium" | "high" | "critical";

/** Named marks from the authored icon family; never emoji. */
export type RiskIcon =
  | "alert"
  | "pill"
  | "dose"
  | "repeat"
  | "route"
  | "sides"
  | "pin"
  | "clipboard"
  | "no"
  | "speech"
  | "gauge";

export interface RiskLabel {
  /** Vietnamese label, the primary one a clinician reads. */
  vi: string;
  /** English helper text, secondary. */
  en: string;
  icon: RiskIcon;
  /**
   * "entity" is clinical content extracted from the turn and worth showing as a
   * chip. "check" is a reason the turn needs review, shown in the gate card.
   */
  group: "entity" | "check";
}

export const RISK_LABELS: Record<RiskKind, RiskLabel> = {
  red_flag: { vi: "Dấu hiệu nguy hiểm", en: "Red flag", icon: "alert", group: "entity" },
  allergy: { vi: "Dị ứng thuốc", en: "Allergy", icon: "alert", group: "entity" },
  pregnancy: { vi: "Thai kỳ", en: "Pregnancy", icon: "clipboard", group: "entity" },
  symptom_severity: {
    vi: "Mức độ triệu chứng",
    en: "Symptom severity",
    icon: "alert",
    group: "entity",
  },
  drug_name: { vi: "Tên thuốc", en: "Medication", icon: "pill", group: "entity" },
  dose_number: { vi: "Liều dùng", en: "Dose", icon: "dose", group: "entity" },
  frequency_duration: {
    vi: "Tần suất / thời gian",
    en: "Frequency",
    icon: "repeat",
    group: "entity",
  },
  route: { vi: "Đường dùng thuốc", en: "Route", icon: "route", group: "entity" },
  laterality: { vi: "Bên trái / phải", en: "Laterality", icon: "sides", group: "entity" },
  body_location: { vi: "Vị trí trên cơ thể", en: "Body location", icon: "pin", group: "entity" },
  medical_history: { vi: "Tiền sử bệnh", en: "Medical history", icon: "clipboard", group: "entity" },
  negation: { vi: "Phủ định", en: "Negation", icon: "no", group: "entity" },

  negation_mismatch: {
    vi: "Sai lệch phủ định giữa hai câu",
    en: "Negation mismatch",
    icon: "alert",
    group: "check",
  },
  number_mismatch: {
    vi: "Sai lệch con số giữa hai câu",
    en: "Number mismatch",
    icon: "alert",
    group: "check",
  },
  abbreviation: { vi: "Từ viết tắt", en: "Abbreviation", icon: "clipboard", group: "check" },
  subject_omission: { vi: "Thiếu chủ ngữ", en: "Missing subject", icon: "speech", group: "check" },
  pronoun: { vi: "Đại từ xưng hô", en: "Pronoun", icon: "speech", group: "check" },
  low_confidence: { vi: "Độ tin cậy thấp", en: "Low confidence", icon: "gauge", group: "check" },
};

export const SEVERITY_LABELS: Record<RiskSeverity, { vi: string; en: string }> = {
  low: { vi: "Thấp", en: "Low" },
  medium: { vi: "Trung bình", en: "Medium" },
  high: { vi: "Cao", en: "High" },
  critical: { vi: "Nghiêm trọng", en: "Critical" },
};

export function riskLabel(kind: string): RiskLabel {
  return (
    RISK_LABELS[kind as RiskKind] ?? {
      vi: "Thông tin cần kiểm tra",
      en: "Item to check",
      icon: "clipboard",
      group: "check",
    }
  );
}
