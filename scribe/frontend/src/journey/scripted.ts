/**
 * The Emma scenario, as turn payloads.
 *
 * These are shaped exactly like what the websocket and the document endpoint
 * return, because the journey renders them through the *real* components —
 * `GateCard`, `TurnCard`, `DocumentReview`, `PatientSheet` — and the real
 * predicates in `visit/types.ts`. Nothing here re-implements the gate. A line is
 * withheld because `isGated` says so, on the same fields the server sets.
 *
 * Why canned at all: the pitch has to complete on venue Wi-Fi that may not
 * exist. Everything on `/get-care/` is therefore client-side. The live paths at
 * `/kham-song-ngu/` and `/dich-giay-to/` are unchanged and still one click away
 * from the stages that mirror them.
 *
 * Clinical coherence matters even in a script: Emma reports a sulfa allergy, and
 * the clinician then prescribes amoxicillin — safe with that allergy. A script
 * that prescribed a penicillin to a penicillin-allergic patient would be a
 * safety error printed on the pitch slide.
 */

import type { VisitTurn } from "../visit/types";

interface Seed {
  id: string;
  seq: number;
  speaker: "doctor" | "patient" | "document";
  src: "vi" | "en";
  source: string;
  translation: string;
  tier: "low" | "medium" | "high" | "critical";
  spans?: { kind: string; severity: string; term: string }[];
  backTranslation?: string;
}

function turn(seed: Seed): VisitTurn {
  const gated = seed.tier === "high" || seed.tier === "critical";
  return {
    id: seed.id,
    session_id: "scripted",
    seq: seed.seq,
    speaker: seed.speaker,
    src_lang: seed.src,
    tgt_lang: seed.src === "vi" ? "en" : "vi",
    source_text: seed.source,
    normalized_text: seed.source,
    translation: seed.translation,
    asr_confidence: 0.96,
    mt_confidence: 0.94,
    risk_tier: seed.tier,
    risk_spans: seed.spans ?? [],
    readback: seed.backTranslation
      ? { back_translation: seed.backTranslation, entities: [], flags: [] }
      : null,
    // The server sets these two together; so does this. `turn_status` in
    // interpreter/app/session.py is the rule being mirrored: high and critical
    // wait for the clinician, everything else is delivered.
    status: gated ? "awaiting_confirm" : "delivered",
    corrected_text: null,
    created_at: new Date().toISOString(),
    requires_confirmation: gated,
    low_confidence: false,
  };
}

export const SCRIPTED_VISIT: VisitTurn[] = [
  turn({
    id: "sv1",
    seq: 1,
    speaker: "doctor",
    src: "vi",
    source: "Chào chị. Hôm nay chị thấy trong người thế nào?",
    translation: "Hello. What has been bothering you today?",
    tier: "low",
  }),
  turn({
    id: "sv2",
    seq: 2,
    speaker: "patient",
    src: "en",
    source: "I have an itchy red rash on both arms. It started yesterday morning.",
    translation: "Tôi bị nổi mẩn đỏ và ngứa ở cả hai cánh tay, bắt đầu từ sáng hôm qua.",
    tier: "low",
    spans: [{ kind: "body_location", severity: "low", term: "both arms" }],
  }),
  turn({
    id: "sv3",
    seq: 3,
    speaker: "doctor",
    src: "vi",
    source: "Chị có dị ứng với loại thuốc nào không?",
    translation: "Are you allergic to any medicines?",
    tier: "low",
  }),
  // Withheld in the other direction: the clinician does not see this in their
  // column until they have reviewed it against the back-translation. An allergy
  // misheard is the kind of error that ends in the wrong prescription.
  turn({
    id: "sv4",
    seq: 4,
    speaker: "patient",
    src: "en",
    source: "Yes — I am allergic to sulfa drugs.",
    translation: "Vâng — tôi bị dị ứng với thuốc nhóm sulfa.",
    tier: "critical",
    spans: [{ kind: "allergy", severity: "critical", term: "sulfa drugs" }],
    backTranslation: "Yes, I am allergic to sulfa medicines.",
  }),
  // The moment the product exists for.
  turn({
    id: "sv5",
    seq: 5,
    speaker: "doctor",
    src: "vi",
    source: "Tôi kê Amoxicillin 500 mg, uống 1 viên, ngày 2 lần, sau khi ăn.",
    translation: "Amoxicillin 500 mg — take 1 tablet twice daily after meals.",
    tier: "high",
    spans: [
      { kind: "drug_name", severity: "high", term: "Amoxicillin" },
      { kind: "dose_number", severity: "high", term: "500 mg" },
      { kind: "frequency_duration", severity: "medium", term: "ngày 2 lần" },
    ],
    backTranslation: "Amoxicillin 500 mg, one tablet, two times per day, after eating.",
  }),
];

/**
 * The prescription Emma is handed on the way out.
 *
 * Deliberately the same four lines as the document on the homepage: the two
 * carrying a dose are held, the two that do not are delivered. A visitor who
 * read the front page should recognise this sheet as the thing they were shown.
 */
export const SCRIPTED_DOCUMENT: VisitTurn[] = [
  turn({
    id: "sd1",
    seq: 1,
    speaker: "document",
    src: "vi",
    source: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
    translation: "Amoxicillin 500 mg — take 1 tablet twice daily, after meals",
    tier: "high",
    spans: [
      { kind: "drug_name", severity: "high", term: "Amoxicillin" },
      { kind: "dose_number", severity: "high", term: "500 mg" },
    ],
  }),
  turn({
    id: "sd2",
    seq: 2,
    speaker: "document",
    src: "vi",
    source: "Paracetamol 500 mg — Uống khi sốt trên 38,5 độ C",
    translation: "Paracetamol 500 mg — take when your temperature is above 38.5 °C",
    tier: "high",
    spans: [
      { kind: "drug_name", severity: "high", term: "Paracetamol" },
      { kind: "dose_number", severity: "high", term: "500 mg" },
    ],
  }),
  turn({
    id: "sd3",
    seq: 3,
    speaker: "document",
    src: "vi",
    source: "Không uống rượu trong thời gian dùng thuốc",
    translation: "Do not drink alcohol while taking this medicine",
    tier: "low",
    spans: [{ kind: "negation", severity: "low", term: "Không" }],
  }),
  turn({
    id: "sd4",
    seq: 4,
    speaker: "document",
    src: "vi",
    source: "Tái khám sau 5 ngày, hoặc sớm hơn nếu nặng lên",
    translation: "Return for review after 5 days, or sooner if it gets worse",
    tier: "low",
  }),
];

export const SCRIPTED_FOLLOW_UP =
  "Return for review after 5 days, or sooner if the rash spreads or you develop a fever.";

/**
 * Release one turn, the way the server does on `POST /api/turns/{id}/confirm`.
 *
 * `requires_confirmation` is cleared alongside the status because the two are
 * what `isGated` reads; clearing only one would leave a turn that is confirmed
 * and still masked, which is precisely the bug the predicate exists to prevent.
 */
export function confirmScripted(turns: VisitTurn[], id: string, edited?: string): VisitTurn[] {
  return turns.map((item) =>
    item.id === id
      ? {
          ...item,
          status: edited ? "corrected" : "confirmed",
          corrected_text: edited ?? item.corrected_text,
          requires_confirmation: false,
          low_confidence: false,
        }
      : item,
  );
}
