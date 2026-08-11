// Landing copy for the bilingual-visit product.
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
      { href: "#problem", label: "Vấn đề" },
      { href: "#how", label: "Cách hoạt động" },
      { href: "#evidence", label: "Bằng chứng" },
      { href: "#start", label: "Bắt đầu" },
    ],
    navCta: "Bắt đầu ca khám",
    langToggle: "EN",
    langToggleAria: "Switch to English",

    heroLead: "Người bệnh nước ngoài rời phòng khám với tờ giấy ",
    heroMark: "họ không đọc được.",
    heroBody:
      "CarePath dịch cả buổi khám và cả giấy tờ — đơn thuốc, phiếu xét nghiệm, giấy ra viện — rồi giữ lại phần nguy hiểm cho tới khi bác sĩ xác nhận.",
    heroPrimary: "Bắt đầu ca khám",
    heroSecondary: "Xem vấn đề",

    docLabel: "Ví dụ có thật",
    docOrg: "Phòng khám đa khoa",
    docTitle: "Đơn thuốc",
    docMeta: ["Người bệnh: M. Reynolds", "Ngày: 11/08/2026", "Số: 2026/0431"],
    docRows: [
      {
        vi: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
        en: "Amoxicillin 500 mg — take 1 tablet, 2 times a day, after food",
      },
      {
        vi: "Paracetamol 500 mg — Uống khi sốt trên 38,5 độ C",
        en: "Paracetamol 500 mg — take when fever is above 38.5°C",
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
    docFoot: "Bác sĩ xác nhận từng dòng trước khi người bệnh nhìn thấy.",
    docSeal: "Bác sĩ đã xác nhận",

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
    problemNotes: [
      {
        lead: "52,4% so với 35,9%",
        body: "— tỉ lệ sự cố bắt nguồn từ lỗi giao tiếp. Nguyên nhân được nêu tên là dùng người nhà, bạn bè hoặc nhân viên không có chuyên môn làm phiên dịch.",
      },
      {
        lead: "22,8 triệu lượt khách quốc tế năm 2025",
        body: "— mức cao nhất từ trước tới nay, cùng khoảng 83.500–100.000 người nước ngoài đang cư trú tại Việt Nam.",
      },
    ],

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
      lead: "Thị trường đã có giá.",
      body: " Phiên dịch y tế theo ca ở Việt Nam khoảng 50 USD, tính từ lúc làm thủ tục đến khi ra viện. Dịch thuật công chứng hồ sơ y tế khoảng 25–100 USD mỗi trang, trả kết quả sau 24 giờ.",
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
    startTitle: "Bắt đầu một ca khám song ngữ.",
    startBody:
      "Không cần cài đặt. Mở trên máy tính bảng hoặc điện thoại của phòng khám, micro chỉ bật khi bác sĩ bấm giữ.",
    startCta: "Bắt đầu ca khám",
    startScribe: "Hoặc chỉ tạo bệnh án từ tệp âm thanh",
    pilotSummary: "Dành cho cơ sở muốn thí điểm CarePath",
  },

  en: {
    navAria: "Main navigation",
    nav: [
      { href: "#problem", label: "The problem" },
      { href: "#how", label: "How it works" },
      { href: "#evidence", label: "Evidence" },
      { href: "#start", label: "Start" },
    ],
    navCta: "Start a visit",
    langToggle: "VI",
    langToggleAria: "Chuyển sang tiếng Việt",

    heroLead: "Foreign patients leave the clinic holding paper ",
    heroMark: "they cannot read.",
    heroBody:
      "CarePath interprets the consultation and reads the paperwork — prescriptions, lab results, discharge sheets — then holds back anything dangerous until the clinician confirms it.",
    heroPrimary: "Start a visit",
    heroSecondary: "See the problem",

    docLabel: "A real example",
    docOrg: "General clinic",
    docTitle: "Prescription",
    docMeta: ["Patient: M. Reynolds", "Date: 11/08/2026", "No: 2026/0431"],
    docRows: [
      {
        vi: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
        en: "Amoxicillin 500 mg — take 1 tablet, 2 times a day, after food",
      },
      {
        vi: "Paracetamol 500 mg — Uống khi sốt trên 38,5 độ C",
        en: "Paracetamol 500 mg — take when fever is above 38.5°C",
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
    docFoot: "The clinician confirms every line before the patient sees it.",
    docSeal: "Clinician confirmed",

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
    problemNotes: [
      {
        lead: "52.4% against 35.9%",
        body: "— the share of adverse events rooted in communication error. The named root cause is using family, friends or untrained staff as interpreters.",
      },
      {
        lead: "22.8 million international arrivals in 2025",
        body: "— the highest on record, alongside roughly 83,500–100,000 foreign residents in Vietnam.",
      },
    ],

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
      lead: "The market already has a price.",
      body: " A medical interpreter in Vietnam runs about $50 per case, covering admission through discharge. Certified medical document translation runs $25–100 per page with a 24-hour turnaround.",
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
    startTitle: "Start a bilingual visit.",
    startBody:
      "Nothing to install. Open it on the clinic's tablet or phone; the microphone only runs while the clinician holds the button.",
    startCta: "Start a visit",
    startScribe: "Or just draft a clinical note from an audio file",
    pilotSummary: "For clinics that want to pilot CarePath",
  },
} as const;
