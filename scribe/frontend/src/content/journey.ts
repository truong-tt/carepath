/**
 * Copy for the care journey at /get-care/ and the episode at /my-carepath/.
 *
 * English, because the reader is the patient and the patient is foreign. The
 * clinician-facing pieces embedded in these screens — the gate card, the risk
 * chips, the document review — render their own Vietnamese from
 * `visit/riskLabels.ts` and are not translated here. That split is the point:
 * on one screen, each person reads their own language, and the thing being
 * decided sits between them.
 *
 * Three rules this file holds:
 *
 * 1. Nothing here diagnoses or recommends treatment. The intake asks what the
 *    patient wants help with; it never interprets it.
 * 2. Curated data says it is curated, every time it appears. No availability is
 *    ever stated, because no booking system is connected.
 * 3. A prototype says it is a prototype. The escalation panel does not imply a
 *    coordinator is sitting by a phone.
 */

export const JOURNEY = {
  navBack: "← Home",
  brand: "CarePath",

  steps: ["Your need", "Where to go", "Visit brief", "The visit", "Paperwork"],

  intake: {
    label: "Step 1 of 5",
    title: "What do you need help with?",
    lede: "Five questions. Nothing here identifies you — no name, no passport, no date of birth.",
    disclaimer:
      "CarePath does not diagnose and does not recommend treatment. It helps you reach a clinician and understand what they tell you.",
    city: "Which city are you in?",
    cityHint: "Hanoi is the only city with curated clinic data right now.",
    language: "Which language do you want care in?",
    need: "What is going on? Use your own words.",
    needPlaceholder: "e.g. itchy red rash on both arms since yesterday",
    timing: "When do you need to be seen?",
    timingOptions: ["Today", "In the next few days", "I am flexible"],
    insurance: "I have travel or health insurance",
    insuranceHint: "Used only to tell the clinic whether to prepare paperwork for a claim.",
    submit: "Find care",
    example: "Use the example patient",
    exampleNote:
      "Fills this form with the demo scenario: Emma, an English-speaking tourist in Hanoi with a rash.",
    needRequired: "Tell us briefly what is going on, so we can point you somewhere useful.",
  },

  providers: {
    label: "Step 2 of 5",
    title: "Where you could go",
    lede: "Ranked against the words you used, not against a diagnosis.",
    curated:
      "Curated sample data. CarePath does not have live appointment availability and will not invent it — call the clinic to confirm before travelling.",
    hours: "Opening hours",
    languages: "Languages",
    choose: "Choose this clinic",
    chosen: "Chosen",
    back: "← Change what you told us",
  },

  brief: {
    label: "Step 3 of 5",
    title: "Your visit brief",
    lede:
      "This is what the clinician sees before you speak. Check it and change anything that is wrong — it is your account, not ours.",
    patientColumn: "Your words",
    clinicianColumn: "For the clinician · Tiếng Việt",
    untranslated: "Translated live at the start of the visit",
    fields: {
      concern: { en: "What is wrong", vi: "Lý do khám" },
      since: { en: "Since when", vi: "Thời gian khởi phát" },
      history: { en: "Relevant history", vi: "Tiền sử liên quan" },
      medications: { en: "Medicines you take", vi: "Thuốc đang dùng" },
      allergies: { en: "Allergies", vi: "Dị ứng" },
      questions: { en: "What you want to ask", vi: "Câu hỏi của người bệnh" },
      insurance: { en: "Insurance", vi: "Bảo hiểm" },
    },
    empty: "Not given",
    save: "Looks right — continue",
    edit: "Edit",
    done: "Done editing",
  },

  visit: {
    label: "Step 4 of 5",
    title: "During the visit",
    lede:
      "Both sides speak their own language. Anything carrying a dose, a drug name or an allergy stops here until the clinician confirms it.",
    scripted: "Scripted walkthrough. It runs offline so a demo never depends on the venue network.",
    live: "Run this on a real consultation →",
    patientColumn: "You · English",
    clinicianColumn: "Clinician · Tiếng Việt",
    // What the patient sees where a withheld line would be. It has to read as a
    // deliberate act, not a loading state and not a failure.
    masked: "Held back — the clinician is checking this",
    principle: "Translation is not the safety mechanism. Verification is.",
    principleBody:
      "A machine translation of a dose is still a machine translation of a dose. What makes it safe to hand you is that the clinician read it back and confirmed it.",
    waiting: (n: number) =>
      n === 1 ? "1 line is waiting for the clinician." : `${n} lines are waiting for the clinician.`,
    cleared: "Nothing is being withheld. Every line has been confirmed.",
    next: "Continue to paperwork",
  },

  paperwork: {
    label: "Step 5 of 5",
    title: "The paper you take home",
    lede:
      "The prescription is in Vietnamese. Each line is read, checked, and held until the clinician confirms it — then it is yours in English.",
    scripted: "Scripted walkthrough, offline.",
    live: "Translate a real document →",
    sheetTitle: "Your copy",
    sheetReady: (n: number) =>
      n === 1 ? "1 line confirmed and ready for you." : `${n} lines confirmed and ready for you.`,
    sheetEmpty: "Nothing confirmed yet. Confirmed lines appear here.",
    sheetNote:
      "Only lines the clinician confirmed appear here. The clinician remains responsible for every clinical statement.",
    finish: "Save to My CarePath",
  },

  done: {
    label: "Done",
    title: "Your care episode is saved",
    lede: "It lives in this browser tab only, and you can delete it at any time.",
    cta: "Open My CarePath",
  },

  episode: {
    navBack: "← Home",
    label: "My CarePath",
    title: "Your care episode",
    lede: "One health problem, from finding a clinic to knowing what happens next.",
    emptyTitle: "No care episode yet",
    emptyBody:
      "When you start a care journey, what you tell us and what the clinician confirms is collected here.",
    emptyCta: "Start a care journey",

    status: {
      planning: "Working out where to go",
      prepared: "Ready for the visit",
      in_visit: "In the visit",
      post_visit: "After the visit",
      escalated: "Waiting for a person",
    },

    sections: {
      overview: "Overview",
      brief: "Visit brief",
      provider: "Clinic",
      consultation: "What was said",
      medications: "Medicines",
      documents: "Documents",
      followUp: "Follow-up",
    },

    medicationsNote:
      "Taken word for word from what the clinician confirmed. Nothing here was rewritten or summarised.",
    documentsNote: "Vietnamese as printed, English as confirmed.",
    noMedications: "No confirmed medicines yet.",
    noDocuments: "No confirmed documents yet.",
    noFollowUp: "No follow-up recorded yet.",

    escalate: {
      title: "This step needs a person",
      body: "Some things software should not do alone. Tell us which one and CarePath stops trying.",
      prototype:
        "Prototype. No coordinator is on call — this records what you need and shows you what would happen next.",
      reasons: [
        "I want a human interpreter",
        "I need someone to come to the hospital with me",
        "My insurance is refusing or asking for more",
        "This is more complicated than an outpatient visit",
        "My language is not supported",
      ],
      submit: "Request a person",
      requested: "Recorded. In a live service this reaches a coordinator; here it stops.",
      emergency: "If this is an emergency, call 115 — do not wait for CarePath.",
    },

    privacy: {
      title: "Your data",
      body: "Everything above is held in this browser tab and nowhere else. Closing the tab clears it.",
      clear: "Delete this episode",
      cleared: "Deleted. Nothing from this episode is left in the browser.",
    },
  },
} as const;
