// Landing copy for the care navigator.
//
// English is the default here and Vietnamese is behind the toggle, which is the
// reverse of what this file shipped with. The reader who has to understand this
// page in fifteen seconds is a foreign patient or someone judging whether the
// product helps one; the Vietnamese clinic owner who also reads it is the second
// audience, not the first. Neither language is dropped — see
// docs/decisions/0023-foreign-patient-care-navigator.md.
//
// Kept local to this surface rather than added to strings.ts: that file is a
// 1287-line PageCopy contract with a parity test, most of it unreferenced, and
// this page should not have to satisfy the old two-product shape to say what
// CarePath now is.
//
// Every figure below is sourced. The claim this page has to survive is that the
// problem is real, so nothing here is rounded up or written from intuition.
//
// The shape follows the page's composition, not a generic card list: the hero
// is a document, the problem is one comparison, the evidence is a results
// table with its limits attached. Structure that carries an argument does not
// survive being flattened back into `{title, body}[]`.

export type Lang = "vi" | "en";

export const LANDING = {
  vi: {
    navAria: "Điều hướng chính",
    nav: [
      { href: "#journey", label: "Hành trình" },
      { href: "#problem", label: "Vấn đề" },
      { href: "#how", label: "Cách hoạt động" },
      { href: "#evidence", label: "Bằng chứng" },
      { href: "#start", label: "Bắt đầu" },
    ],
    navCta: "Tôi cần khám bệnh",
    langToggle: "EN",
    langToggleAria: "Switch to English",

    heroLead: "Khám chữa bệnh ở Việt Nam, ",
    heroMark: "không phải tự xoay xở một mình.",
    heroBody:
      "CarePath đi cùng người bệnh nước ngoài từ lúc tìm phòng khám, chuẩn bị buổi khám, trao đổi với bác sĩ, tới lúc đọc hiểu giấy tờ và biết cần làm gì tiếp theo.",
    heroPrimary: "Tôi cần khám bệnh",
    heroSecondary: "Tôi đã có đơn thuốc",

    // The spine of the product, stated once, in order. Every capability
    // CarePath has appears as a step here and nowhere as a product of its own.
    journeyLabel: "Một hành trình",
    journeyTitle: "Sáu bước, một lần khám bệnh.",
    journeySteps: [
      { title: "Tìm nơi khám", body: "Chọn phòng khám phù hợp với vấn đề và ngôn ngữ của người bệnh." },
      { title: "Chuẩn bị", body: "Bản tóm tắt song ngữ để bác sĩ đọc trước khi người bệnh mở lời." },
      { title: "Khám", body: "Bác sĩ nói tiếng Việt, người bệnh nói tiếng Anh, dịch hai chiều." },
      { title: "Xác nhận", body: "Dòng có liều thuốc hoặc dị ứng bị giữ lại tới khi bác sĩ duyệt." },
      { title: "Giấy tờ", body: "Đơn thuốc, giấy ra viện, phiếu xét nghiệm — dịch từng dòng." },
      { title: "Theo dõi", body: "Thuốc đã xác nhận, lịch tái khám, câu hỏi cho lần sau." },
    ],
    journeyNote:
      "Đây là một sản phẩm, không phải bốn công cụ. Người bệnh không cần biết bên trong có gì.",

    timelineLabel: "Một ca có thật",
    timelineTitle: "Emma, khách du lịch ở Hà Nội.",
    timeline: [
      { when: "10:00", body: "Emma nổi mẩn đỏ ở hai cánh tay." },
      { when: "10:15", body: "Tìm được vài phòng khám, nhưng không biết nơi nào tiếp được tiếng Anh." },
      { when: "11:00", body: "Tới nơi, nhưng không giải thích được mình đang dùng thuốc gì." },
      { when: "11:30", body: "Buổi khám kết thúc." },
      { when: "11:35", body: "Cầm về một tờ đơn thuốc tiếng Việt." },
    ],
    timelineNote: "Đó là một vấn đề, không phải bốn bài toán dịch thuật riêng lẻ.",

    docLabel: "Ví dụ có thật",
    docOrg: "Phòng khám đa khoa",
    docTitle: "Đơn thuốc",
    docMeta: ["Người bệnh: M. Reynolds", "Ngày: 11/08/2026", "Số: 2026/0431"],
    // The two lines carrying a dose are held; the two that do not are resolved.
    // That is the product rule, not an illustration of it — a clinician reading
    // this sheet should recognise its own behaviour. A held row has no `en` at
    // all, so the English is absent from the DOM rather than hidden by CSS.
    docRows: [
      {
        vi: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
        held: true,
      },
      {
        vi: "Paracetamol 500 mg — Uống khi sốt trên 38,5 độ C",
        held: true,
      },
      {
        vi: "Không uống rượu trong thời gian dùng thuốc",
        en: "Do not drink alcohol while taking this medicine",
      },
      {
        vi: "Tái khám sau 5 ngày, hoặc sớm hơn nếu nặng lên",
        en: "Return for review after 5 days, or sooner if it gets worse",
      },
    ],
    docHeldMark: "Giữ lại",
    docHeldNote: "Dòng có liều thuốc",
    docFoot: "Bác sĩ xác nhận từng dòng trước khi người bệnh nhìn thấy.",
    // Was "Bác sĩ đã xác nhận". Past tense contradicted the line beneath it,
    // and now contradicts the two held rows on the same sheet.
    docSeal: "Chờ bác sĩ xác nhận",

    problemLabel: "Vấn đề",
    problemTitle: "Nguy hiểm không nằm ở lúc trò chuyện.",
    problemBody:
      "Phiên dịch viên rời đi khi buổi khám kết thúc. Tờ giấy thì theo người bệnh về nhà. Y văn quốc tế chỉ ra ba thời điểm dễ gây hại nhất cho người bệnh không thạo ngôn ngữ: đối chiếu thuốc, lúc ra viện, và khi ký cam kết — cả ba đều diễn ra trên giấy.",
    compareBase: {
      figure: "29,5%",
      caption: "Người bệnh nói cùng ngôn ngữ với bác sĩ: tỉ lệ sự cố y khoa gây tổn hại thể chất.",
    },
    compareRisk: {
      figure: "49,1%",
      caption: "Người bệnh không thạo ngôn ngữ: cùng loại sự cố, gần gấp rưỡi khả năng gây tổn hại.",
    },
    compareSource:
      "Divi C, Koss RG, Schmaltz SP, Loeb JM. Language proficiency and adverse events in US hospitals: a pilot study. Int J Qual Health Care 2007;19(2):60–67.",
    problemNotes: [
      {
        lead: "52,4% so với 35,9%",
        body: "— tỉ lệ sự cố bắt nguồn từ lỗi giao tiếp. Nguyên nhân được nêu tên là dùng người nhà, bạn bè hoặc nhân viên không có chuyên môn làm phiên dịch.",
      },
      {
        lead: "21,2 triệu lượt khách quốc tế năm 2025",
        body: "— mức cao nhất từ trước tới nay theo Cục Thống kê, cùng 161.992 lao động nước ngoài có việc làm hợp pháp tại Việt Nam tính đến cuối năm 2024.",
      },
    ],

    // The three moments the safety literature names. All three happen on paper,
    // which is the whole argument for why an interpreter alone does not cover
    // this. Stated as a sequence, because it is one: the interpreter is present
    // for the first column and gone for the other two.
    momentsLabel: "Thời điểm nguy hiểm",
    momentsTitle: "Ba lúc dễ gây hại nhất đều diễn ra trên giấy.",
    moments: [
      {
        when: "Đối chiếu thuốc",
        body: "Người bệnh cầm đơn thuốc về nhà và tự đọc liều. Không ai còn ở đó để hỏi lại.",
      },
      {
        when: "Lúc ra viện",
        body: "Giấy ra viện ghi dấu hiệu cần quay lại ngay. Nếu không đọc được, người bệnh không biết khi nào phải quay lại.",
      },
      {
        when: "Khi ký cam kết",
        body: "Chữ ký nằm dưới một đoạn văn bản tiếng Việt. Đồng ý mà không hiểu thì không phải là đồng ý.",
      },
    ],
    momentsNote:
      "Phiên dịch viên có mặt lúc trò chuyện. Cả ba thời điểm trên đều xảy ra sau đó.",

    tryLabel: "Thử ngay",
    tryTitle: "Đi hết hành trình, không cần tài khoản.",
    tryBody:
      "Chạy trọn ca của Emma ngay trên trình duyệt: tìm phòng khám, tóm tắt trước khám, buổi khám song ngữ, bước bác sĩ xác nhận, và đơn thuốc.",
    tryItems: [
      { title: "Tìm nơi khám", body: "Nhập vấn đề bằng lời của người bệnh." },
      { title: "Bước xác nhận", body: "Xem dòng có liều thuốc bị giữ lại thế nào." },
      { title: "Đơn thuốc", body: "Nhận bản tiếng Anh sau khi bác sĩ duyệt." },
    ],
    tryCta: "Đi thử hành trình",
    trySecondary: "Hoặc thử đọc một ảnh giấy tờ thật",

    howLabel: "Cách hoạt động",
    howTitle: "Đọc — đối chiếu — bác sĩ xác nhận.",
    howSteps: [
      { title: "Nghe và đọc", body: "Ghi lại lời nói hai chiều, và đọc chữ trên giấy tờ tiếng Việt." },
      {
        title: "Nhận diện",
        body: "Tách ra tên thuốc, liều dùng, tần suất, dị ứng — bằng bộ luật lâm sàng, không phải bằng phỏng đoán của mô hình.",
      },
      {
        title: "Giữ lại phần rủi ro",
        body: "Dòng có liều thuốc hoặc thuốc dễ nhầm tên bị chặn, người bệnh chưa nhìn thấy và chưa nghe thấy.",
      },
      {
        title: "Bàn giao",
        body: "Bác sĩ xác nhận hoặc sửa. Sau đó người bệnh nhận bản tiếng Anh, bác sĩ nhận bệnh án tiếng Việt.",
      },
    ],

    evidenceLabel: "Bằng chứng",
    evidenceTitle: "Đặt đúng giới hạn của bằng chứng.",
    evidenceBody:
      "Các con số về sự cố y khoa ở trên đến từ nghiên cứu an toàn người bệnh đã công bố, không phải kết quả của CarePath. Đây là lý do chúng tôi xây sản phẩm này, chưa phải bằng chứng rằng nó hiệu quả.",
    priceNote: {
      lead: "Người thật vẫn tốt hơn — khi kịp có mặt.",
      body: " Phiên dịch y tế ở Việt Nam khoảng 300.000–1.500.000 đồng mỗi giờ, chuyên khoa sâu 1,2–2,5 triệu, trọn ngày 2–5 triệu, và phải đặt trước. Dịch thuật công chứng khoảng 60.000–160.000 đồng mỗi trang, trả sau 24 giờ. Người bệnh thì rời phòng khám sau 20 phút. CarePath không thay thế phiên dịch viên; CarePath chỉ lấp những giờ không ai có mặt.",
    },
    tableCaption:
      "Bộ 50 câu kiểm thử chạy qua mô hình thật. Đây là kết quả kỹ thuật, không phải thử nghiệm lâm sàng.",
    tableHead: ["Điều đã đo", "Kết quả", "Nghĩa là gì"],
    tableRows: [
      { metric: "Tên thuốc", figure: "100%", note: "Không có tên thuốc nào bị đổi hoặc bị bỏ." },
      {
        metric: "Con số và đơn vị liều",
        figure: "100%",
        note: "500 mg vẫn là 500 mg, kể cả khi liều được đọc thành chữ.",
      },
      { metric: "Bên trái / bên phải", figure: "100%", note: "Không có ca nào bị đảo bên." },
      {
        metric: "Phủ định",
        figure: "98%",
        note: "Trường hợp còn lại đã bị giữ lại chờ bác sĩ xác nhận, không tới thẳng người bệnh.",
      },
    ],
    limitsTitle: "Điều CarePath chưa chứng minh",
    limits: [
      "Chưa có thử nghiệm lâm sàng.",
      "Chưa đo trên chữ viết tay.",
      "Chưa có dữ liệu về kết cục người bệnh.",
      "Bác sĩ vẫn chịu trách nhiệm chuyên môn cho mọi nội dung.",
    ],

    safetyLabel: "Giới hạn",
    safetyTitle: "Những việc CarePath không làm.",
    safetyItems: [
      "Không chẩn đoán, không kê đơn, không đưa lời khuyên y khoa.",
      "Không tự gửi nội dung rủi ro cho người bệnh khi bác sĩ chưa xác nhận.",
      "Không lưu âm thanh. Không lưu ảnh giấy tờ.",
      "Không thay thế phiên dịch viên khi người bệnh yêu cầu người thật.",
    ],

    startLabel: "Bắt đầu",
    startTitle: "Bắt đầu từ chỗ bạn đang đứng.",
    startBody:
      "Không cần cài đặt, không cần tài khoản. Người bệnh mở trên điện thoại của mình; phòng khám mở trên máy tính bảng, micro chỉ bật khi bác sĩ bấm giữ.",
    startCta: "Tôi cần khám bệnh",
    // The page argues that harm concentrates on paper, and until CP-UX-19 every
    // door it opened was a conversation. This is the paperwork door.
    startPaperwork: "Tôi đã có đơn thuốc",
    startVisit: "Dành cho phòng khám: bắt đầu ca khám song ngữ",
    startScribe: "Hoặc chỉ tạo bệnh án từ tệp âm thanh",
    // The B2B wedge: a clinic that treats foreign patients without running an
    // international-patient department. No pricing is stated anywhere on this
    // page, because none of it has been validated with a paying clinic.
    pilotSummary: "Thí điểm CarePath tại phòng khám của bạn",
  },

  en: {
    navAria: "Main navigation",
    nav: [
      { href: "#journey", label: "The journey" },
      { href: "#problem", label: "The problem" },
      { href: "#how", label: "How it works" },
      { href: "#evidence", label: "Evidence" },
      { href: "#start", label: "Start" },
    ],
    navCta: "I need medical care",
    langToggle: "VI",
    langToggleAria: "Chuyển sang tiếng Việt",

    heroLead: "Healthcare in Vietnam, ",
    heroMark: "without navigating it alone.",
    heroBody:
      "Find care, prepare your visit, communicate with clinicians, understand your paperwork, and keep track of what happens next.",
    heroPrimary: "I need medical care",
    heroSecondary: "I already have a prescription",

    journeyLabel: "One journey",
    journeyTitle: "Six steps, one illness.",
    journeySteps: [
      { title: "Find care", body: "A clinic that matches what you described and the language you speak." },
      { title: "Prepare", body: "A bilingual brief the clinician reads before you have to explain anything." },
      { title: "Visit", body: "You speak English, the clinician speaks Vietnamese, both directions interpreted." },
      { title: "Verify", body: "A dose, a drug name or an allergy is held until the clinician confirms it." },
      { title: "Paperwork", body: "Prescription, discharge sheet, lab result — read line by line." },
      { title: "Follow-up", body: "Confirmed medicines, when to come back, what to ask next time." },
    ],
    journeyNote:
      "One product, not four tools. Nobody using it should have to know what is underneath.",

    timelineLabel: "One real case",
    timelineTitle: "Emma, a tourist in Hanoi.",
    timeline: [
      { when: "10:00", body: "Emma develops an itchy red rash on both arms." },
      { when: "10:15", body: "She finds several clinics and cannot tell which one handles English." },
      { when: "11:00", body: "She gets there and cannot explain which medicines she takes." },
      { when: "11:30", body: "The consultation ends." },
      { when: "11:35", body: "She leaves holding a prescription written in Vietnamese." },
    ],
    timelineNote: "That is one problem, not four separate translation problems.",

    docLabel: "A real example",
    docOrg: "General clinic",
    docTitle: "Prescription",
    docMeta: ["Patient: M. Reynolds", "Date: 11/08/2026", "No: 2026/0431"],
    docRows: [
      {
        vi: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
        held: true,
      },
      {
        vi: "Paracetamol 500 mg — Uống khi sốt trên 38,5 độ C",
        held: true,
      },
      {
        vi: "Không uống rượu trong thời gian dùng thuốc",
        en: "Do not drink alcohol while taking this medicine",
      },
      {
        vi: "Tái khám sau 5 ngày, hoặc sớm hơn nếu nặng lên",
        en: "Return for review after 5 days, or sooner if it gets worse",
      },
    ],
    docHeldMark: "Withheld",
    docHeldNote: "Line carries a dose",
    docFoot: "The clinician confirms every line before the patient sees it.",
    docSeal: "Awaiting clinician confirmation",

    problemLabel: "The problem",
    problemTitle: "The danger is not in the conversation.",
    problemBody:
      "An interpreter leaves when the consultation ends. The paper goes home with the patient. The patient-safety literature names the three moments where limited-English-proficiency patients are most often harmed — medication reconciliation, discharge, and informed consent — and all three happen on paper.",
    compareBase: {
      figure: "29.5%",
      caption: "Patients who share the clinician's language: share of adverse events causing physical harm.",
    },
    compareRisk: {
      figure: "49.1%",
      caption: "Patients with limited proficiency: the same events, close to half again as likely to cause harm.",
    },
    compareSource:
      "Divi C, Koss RG, Schmaltz SP, Loeb JM. Language proficiency and adverse events in US hospitals: a pilot study. Int J Qual Health Care 2007;19(2):60–67.",
    problemNotes: [
      {
        lead: "52.4% against 35.9%",
        body: "— the share of adverse events rooted in communication error. The named root cause is using family, friends or untrained staff as interpreters.",
      },
      {
        lead: "21.2 million international arrivals in 2025",
        body: "— the highest on record per the General Statistics Office, alongside 161,992 foreign nationals in legal employment in Vietnam at the end of 2024.",
      },
    ],

    momentsLabel: "The dangerous moments",
    momentsTitle: "The three most harmful moments all happen on paper.",
    moments: [
      {
        when: "Medication reconciliation",
        body: "The patient takes the prescription home and reads the dose alone. Nobody is left to ask.",
      },
      {
        when: "Discharge",
        body: "The discharge sheet names the signs that mean come back now. Unreadable, it names nothing.",
      },
      {
        when: "Informed consent",
        body: "The signature sits under a paragraph of Vietnamese. Agreement without understanding is not consent.",
      },
    ],
    momentsNote:
      "An interpreter is there for the conversation. All three of these happen after it.",

    tryLabel: "Try it",
    tryTitle: "Walk the whole journey. No account needed.",
    tryBody:
      "Run Emma's case in the browser: find a clinic, build the visit brief, sit through the bilingual consultation, watch the clinician release a dose, and take the prescription home in English.",
    tryItems: [
      { title: "Find care", body: "Describe the problem in your own words." },
      { title: "The safety gate", body: "Watch a line carrying a dose get held back." },
      { title: "The prescription", body: "Get the English only once the clinician confirms it." },
    ],
    tryCta: "Walk the journey",
    trySecondary: "Or read a real document instead",

    howLabel: "How it works",
    howTitle: "Read it, check it, let the clinician confirm it.",
    howSteps: [
      {
        title: "Listen and read",
        body: "Capture speech in both directions, and read the Vietnamese printed on the paperwork.",
      },
      {
        title: "Identify",
        body: "Pull out drug names, doses, frequencies and allergies — with a clinical rule set, not the model's guess.",
      },
      {
        title: "Hold the risky parts",
        body: "A line carrying a dose or a look-alike drug name is blocked. The patient neither sees nor hears it.",
      },
      {
        title: "Hand over",
        body: "The clinician confirms or corrects. Only then does the patient get the English, and the clinician the Vietnamese record.",
      },
    ],

    evidenceLabel: "Evidence",
    evidenceTitle: "Evidence, kept inside its limits.",
    evidenceBody:
      "The adverse-event figures above come from published patient-safety research, not from CarePath. They are why we built this, not proof that it works.",
    priceNote: {
      lead: "A person is better — when a person gets there in time.",
      body: " A medical interpreter in Vietnam runs 300,000–1,500,000 VND per hour, 1.2–2.5 million for deep specialisation, 2–5 million for a full day, and has to be booked ahead. Certified translation runs 60,000–160,000 VND per page with a 24-hour turnaround. The patient leaves the clinic in 20 minutes. CarePath does not replace an interpreter; it covers the hours when nobody is there.",
    },
    tableCaption:
      "A 50-case set run through the real model. These are engineering results, not a clinical trial.",
    tableHead: ["What was measured", "Result", "What it means"],
    tableRows: [
      { metric: "Drug name", figure: "100%", note: "No drug name was altered or dropped." },
      {
        metric: "Numbers and dose units",
        figure: "100%",
        note: "500 mg stays 500 mg, including when the dose is spoken as words.",
      },
      { metric: "Laterality", figure: "100%", note: "No case swapped left for right." },
      {
        metric: "Negation",
        figure: "98%",
        note: "The remaining case was held for clinician confirmation; it never reached the patient.",
      },
    ],
    limitsTitle: "What CarePath has not shown",
    limits: [
      "No clinical trial.",
      "No measurement on handwriting.",
      "No patient-outcome data.",
      "The clinician remains responsible for every clinical statement.",
    ],

    safetyLabel: "Boundaries",
    safetyTitle: "What CarePath does not do.",
    safetyItems: [
      "No diagnosis, no prescribing, no medical advice.",
      "Nothing risky reaches the patient before the clinician confirms it.",
      "No audio is stored. No document images are stored.",
      "It does not replace a human interpreter when the patient asks for one.",
    ],

    startLabel: "Start",
    startTitle: "Start wherever you are.",
    startBody:
      "Nothing to install, no account. A patient opens it on their own phone; a clinic opens it on a tablet, where the microphone only runs while the clinician holds the button.",
    startCta: "I need medical care",
    startPaperwork: "I already have a prescription",
    startVisit: "For clinics: start a bilingual visit",
    startScribe: "Or just draft a clinical note from an audio file",
    // The B2B wedge: a clinic treating foreign patients without an
    // international-patient department. No price appears on this page — none
    // has been validated with a paying clinic, and a made-up one is a claim.
    pilotSummary: "Pilot CarePath at your clinic",
  },
} as const;
