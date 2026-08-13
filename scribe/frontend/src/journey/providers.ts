/**
 * Curated provider data for the care journey.
 *
 * Every clinic here is invented. Naming real Hanoi clinics would imply a
 * relationship that does not exist, and the preplan is explicit that no fake
 * partnerships get added — so these are plausible sample records, labelled as
 * sample records everywhere they render.
 *
 * Two things this file must never do:
 *
 * 1. State appointment availability. `hours` is opening hours, which are a
 *    property of a clinic. "Two slots left today" is a property of a booking
 *    system nobody has connected, and inventing one is the exact failure mode
 *    that makes a demo dishonest.
 * 2. Diagnose. Matching is on the *category of service a patient asked for*,
 *    never on what might be wrong with them. "rash" routes to dermatology
 *    because the patient said skin, not because CarePath decided it is eczema.
 */

import type { Provider } from "../episode/episode";

export interface CuratedProvider extends Provider {
  /** Service categories, matched against the words the patient used. */
  tags: string[];
}

/** Drop the matching tags before storing: the episode records the choice, not
 *  the routing machinery that produced it. */
export function storable({ tags, ...provider }: CuratedProvider): Provider {
  void tags;
  return provider;
}

export const PROVIDERS: CuratedProvider[] = [
  {
    id: "cp-derm",
    name: "Ba Dinh Skin & Allergy Clinic",
    district: "Ba Dinh, Hanoi",
    focus: "Dermatology and allergy",
    languages: ["English", "Vietnamese"],
    hours: "Mon–Sat, 08:00–17:30",
    note: "Walk-in dermatology. Two doctors consult in English.",
    tags: ["skin", "rash", "itch", "allergy", "derm", "acne", "bite", "hives", "eczema"],
  },
  {
    id: "cp-gp",
    name: "Hoan Kiem International Family Practice",
    district: "Hoan Kiem, Hanoi",
    focus: "General practice",
    languages: ["English", "Vietnamese", "French"],
    hours: "Daily, 08:00–20:00",
    note: "General outpatient care. Refers on for specialist opinion.",
    tags: ["general", "fever", "cold", "flu", "stomach", "pain", "tired", "sick", "infection"],
  },
  {
    id: "cp-dental",
    name: "Tay Ho Dental Centre",
    district: "Tay Ho, Hanoi",
    focus: "Dental",
    languages: ["English", "Vietnamese", "Korean"],
    hours: "Mon–Sat, 09:00–18:00",
    note: "Routine and emergency dental treatment.",
    tags: ["tooth", "teeth", "dental", "dentist", "gum", "filling", "molar"],
  },
  {
    id: "cp-diag",
    name: "Cau Giay Diagnostic Centre",
    district: "Cau Giay, Hanoi",
    focus: "Imaging and laboratory",
    languages: ["English", "Vietnamese"],
    hours: "Mon–Fri, 07:00–16:00",
    note: "Tests and imaging by referral. No walk-in consultations.",
    tags: ["test", "blood", "scan", "x-ray", "ultrasound", "lab", "result", "referral"],
  },
];

/**
 * Rank curated providers against the words the patient used.
 *
 * Deterministic and offline by design: the pitch path must produce the same
 * three clinics every time, on venue Wi-Fi or none. A tie falls back to file
 * order, so the ranking never depends on `sort` stability across engines.
 */
export function matchProviders(careNeed: string, limit = 3): CuratedProvider[] {
  const words = careNeed.toLowerCase();
  const matched = PROVIDERS.map((provider, index) => ({
    provider,
    index,
    score: provider.tags.filter((tag) => words.includes(tag)).length,
  }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map((entry) => entry.provider);

  // General practice always makes the list. It is the honest answer to "I do
  // not know what this is", and it is also the safe one: a patient who picks
  // GP because nothing else looked right ends up in front of a doctor who can
  // refer, rather than guessing at a specialty from a list.
  const gp = PROVIDERS.find((provider) => provider.id === "cp-gp")!;
  const withGp = matched.includes(gp) ? matched : [...matched, gp];

  // Listing a dental clinic for a rash is noise, not choice. Unmatched
  // specialties are dropped rather than padded in to fill three rows.
  return withGp.slice(0, limit);
}

/**
 * Why this clinic appeared, in the patient's terms.
 *
 * Quotes the patient's own word back and names the clinic's *service*. It never
 * says what the patient has — "you described a rash, this is a dermatology
 * clinic" is routing; "this looks like dermatitis" would be diagnosis.
 *
 * Null when nothing matched, so the row shows no reason rather than a
 * manufactured one.
 */
export function matchReason(provider: CuratedProvider, careNeed: string): string | null {
  const hit = provider.tags.find((tag) => careNeed.toLowerCase().includes(tag));
  if (hit) {
    return `You said "${hit}". This clinic's service is ${provider.focus.toLowerCase()}.`;
  }
  return provider.id === "cp-gp"
    ? "Always listed: general practice can see you and refer you on if it turns out to need a specialist."
    : null;
}
