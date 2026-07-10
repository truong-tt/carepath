import type { Language, LocalizedText } from "../demo/types";

export const sources = {
  research: {
    label: "CarePath research report",
    href: "https://github.com/truong-tt/carepath/blob/carepath-interpreter-demo/docs/research.md",
  },
  phuYenRates: {
    label: "Quyết định 32/2021/QĐ-UBND, tỉnh Phú Yên",
    href: "https://vbpl.vn/TW/Pages/vbpq-print.aspx?ItemID=149549",
  },
  healthPricing: {
    label: "Thông tư 21/2024/TT-BYT",
    href: "https://vbpl.moj.gov.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=170583&Keyword=",
  },
  ahrqCost: {
    label: "AHRQ National Scorecard, 2019",
    href: "https://www.ahrq.gov/sites/default/files/wysiwyg/professionals/quality-patient-safety/pfp/hacreport-2019.pdf",
  },
} as const;

interface SafetyItem {
  title: LocalizedText;
  body: LocalizedText;
}

interface PageCopy {
  language: {
    label: string;
    vi: string;
    en: string;
  };
  nav: {
    demo: string;
    scribe: string;
    safety: string;
    process: string;
    cost: string;
  };
  demo: {
    brand: string;
    consoleCta: string;
    disclosure: string;
    privacy: string;
    clinic: string;
    specialty: string;
    chooseScenario: string;
    progress: string[];
    start: string;
    continue: string;
    pause: string;
    next: string;
    replay: string;
    empty: string;
    doctor: string;
    patient: string;
    blocked: string;
    riskDetails: string;
    customTitle: string;
    simulation: string;
    blockedFlag: string;
    readbackTitle: string;
    entityType: string;
    source: string;
    translation: string;
    editTranslation: string;
    confirm: string;
    interpreter: string;
    escalationStopped: string;
    escalationTitle: string;
    escalationBody: string;
    escalationConfirm: string;
    customLabel: string;
    customPlaceholder: string;
    customAdd: string;
    customNote: string;
    customResponse: string;
    download: string;
    tiers: Record<"low" | "medium" | "high" | "critical", string>;
    entityKinds: Record<string, string>;
  };
  form: {
    name: string;
    clinic: string;
    role: string;
    contact: string;
    message: string;
    prepare: string;
    submitting: string;
    posted: string;
    mailOpened: string;
    failed: string;
    required: string;
  };
  hero: {
    titleBefore: string;
    titleAfter: string;
    body: string;
    primaryCta: string;
    secondaryCta: string;
    note: string;
  };
  modules: {
    heading: string;
    interpreter: { name: string; body: string };
    scribe: { name: string; body: string };
  };
  scribe: {
    brand: string;
    kicker: string;
    title: string;
    body: string;
    disclosure: string;
    steps: Record<"raw" | "corrected" | "soap", { label: string; caption: string }>;
    status: string;
    soapLabels: Record<"s" | "o" | "a" | "p", string>;
    note: string;
    cta: string;
  };
  scribeTool: {
    title: string;
    intro: string;
    back: string;
    health: Record<"checking" | "ready" | "demo" | "degraded" | "down", string>;
    dropzone: string;
    dropzoneHint: string;
    contextLabel: string;
    removeFile: string;
    submit: string;
    steps: [string, string, string];
    progressLabel: string;
    errorTitle: string;
    retry: string;
    resultTitle: string;
    reviewBanner: string;
    missingTitle: string;
    processedIn: string;
    copy: string;
    copied: string;
    copyFailed: string;
    newNote: string;
    copyHeading: string;
    disclaimer: string;
  };
  marquee: string[];
  problem: {
    kicker: string;
    title: string;
    body: string;
    memoryStat: string;
    memoryDetail: string;
    translationStat: string;
    translationDetail: string;
    framing: string;
  };
  safety: {
    kicker: string;
    title: string;
    body: string;
    items: SafetyItem[];
  };
  process: {
    kicker: string;
    title: string;
    steps: Array<{ title: string; body: string }>;
  };
  cost: {
    kicker: string;
    title: string;
    body: string;
    interpreterTitle: string;
    interpreterValue: string;
    interpreterNote: string;
    incidentTitle: string;
    incidentValue: string;
    incidentNote: string;
    pilotTitle: string;
    pilotValue: string;
    pilotNote: string;
  };
  pilot: {
    kicker: string;
    title: string;
    body: string;
    transcriptNote: string;
  };
  footer: {
    promise: string;
    posture: string;
    honesty: string;
    contact: string;
  };
}

export const strings: Record<Language, PageCopy> = {
  vi: {
    language: {
      label: "Ngôn ngữ",
      vi: "VI",
      en: "EN",
    },
    nav: {
      demo: "Bản mô phỏng",
      scribe: "Scribe",
      safety: "Cơ chế an toàn",
      process: "Cách hoạt động",
      cost: "Chi phí tham chiếu",
    },
    demo: {
      brand: "CarePath Phiên dịch",
      consoleCta: "Mở công cụ Phiên dịch",
      disclosure: "Bản mô phỏng — không phải bản dịch trực tiếp",
      privacy: "Không thu âm",
      clinic: "Tên cơ sở",
      specialty: "Chuyên khoa",
      chooseScenario: "Chọn kịch bản",
      progress: ["Kịch bản đã chọn", "Nghe hội thoại", "Xác nhận read-back", "Nhận bản ghi"],
      start: "Bắt đầu",
      continue: "Tiếp tục",
      pause: "Tạm dừng",
      next: "Lượt tiếp theo",
      replay: "Phát lại",
      empty: "Hội thoại sẽ xuất hiện tại đây.",
      doctor: "Bác sĩ",
      patient: "Bệnh nhân",
      blocked: "Bị chặn cho đến khi bác sĩ xác nhận.",
      riskDetails: "Chi tiết rủi ro",
      customTitle: "Thử tự gõ",
      simulation: "Mô phỏng",
      blockedFlag: "Bản dịch đang bị chặn",
      readbackTitle: "Xác nhận thông tin quan trọng",
      entityType: "Loại",
      source: "Nguồn",
      translation: "Bản dịch",
      editTranslation: "Chỉnh bản dịch trước khi xác nhận",
      confirm: "Xác nhận và tiếp tục",
      interpreter: "Yêu cầu phiên dịch viên",
      escalationStopped: "Đã dừng bản dịch tự động",
      escalationTitle: "Ưu tiên phiên dịch viên cho nội dung nguy cơ cao",
      escalationBody: "Đây là luồng mô phỏng. Trong sản phẩm, nội dung này không được phát cho bệnh nhân trước khi có xác nhận phù hợp.",
      escalationConfirm: "Xác nhận đã chuyển phiên dịch viên",
      customLabel: "Thử tự gõ một câu",
      customPlaceholder: "Nội dung chỉ được phản hồi bằng câu mẫu",
      customAdd: "Thêm vào mô phỏng",
      customNote: "Không phải dịch máy trực tiếp.",
      customResponse: "Đã nhận văn bản trong bản mô phỏng. Đây không phải bản dịch trực tiếp.",
      download: "Tải bản ghi demo",
      tiers: {
        low: "thấp",
        medium: "trung bình",
        high: "cao",
        critical: "nghiêm trọng",
      },
      entityKinds: {
        Thuốc: "Thuốc",
        Liều: "Liều",
        "Tần suất": "Tần suất",
        "Thời gian": "Thời gian",
        "Phủ định": "Phủ định",
      },
    },
    form: {
      name: "Họ và tên",
      clinic: "Cơ sở y tế",
      role: "Vai trò",
      contact: "Email hoặc Zalo",
      message: "Lời nhắn",
      prepare: "Chuẩn bị yêu cầu thí điểm",
      submitting: "Đang gửi yêu cầu…",
      posted: "Đã gửi yêu cầu thí điểm.",
      mailOpened: "Đã mở bản nháp email. Hãy kiểm tra và gửi thư để hoàn tất.",
      failed: "Không thể gửi yêu cầu. Vui lòng kiểm tra kết nối và thử lại.",
      required: "Vui lòng điền trường này.",
    },
    hero: {
      titleBefore: "Phiên dịch và ghi chép y khoa,",
      titleAfter: "xác nhận trước khi sử dụng.",
      body: "Phiên dịch Việt-Anh có bước xác nhận, cùng Scribe tạo bản nháp SOAP từ chính lời trong buổi khám. Không chẩn đoán, không tư vấn điều trị.",
      primaryCta: "Xem demo 90 giây",
      secondaryCta: "Xem cơ chế an toàn",
      note: "Không cần đăng ký. Không thu âm. Không gửi dữ liệu.",
    },
    modules: {
      heading: "Hai phân hệ",
      interpreter: {
        name: "Phiên dịch",
        body: "Hội thoại Việt-Anh trực tiếp; nội dung rủi ro chỉ được phát khi bác sĩ đã xác nhận.",
      },
      scribe: {
        name: "Scribe",
        body: "Bản nháp SOAP tiếng Việt từ hội thoại khám, luôn chờ bác sĩ duyệt.",
      },
    },
    scribe: {
      brand: "CarePath Scribe",
      kicker: "Phân hệ Scribe",
      title: "Từ lời nói trong buổi khám thành bản nháp SOAP.",
      body: "Scribe nghe hội thoại khám bằng tiếng Việt, hiệu chỉnh thuật ngữ bị nhận dạng sai và xếp thành bản nháp SOAP. Bản nháp chỉ vào hồ sơ sau khi bác sĩ duyệt.",
      disclosure: "Bản mô phỏng với dữ liệu mẫu, không phải hồ sơ thật",
      steps: {
        raw: {
          label: "1. Bản gõ thô từ ASR",
          caption: "Gạch chân: đoạn máy nghe sai trong bản gõ thô.",
        },
        corrected: {
          label: "2. Sau hiệu chỉnh thuật ngữ",
          caption: "Tô nền: thuật ngữ và con số đã được hiệu chỉnh.",
        },
        soap: {
          label: "3. Bản nháp SOAP",
          caption: "Bản nháp xếp theo bốn mục, chờ bác sĩ duyệt từng dòng.",
        },
      },
      status: "Chờ bác sĩ duyệt",
      soapLabels: {
        s: "Chủ quan",
        o: "Khách quan",
        a: "Đánh giá",
        p: "Kế hoạch",
      },
      note: "Nội dung trên là dữ liệu mẫu cho bản mô phỏng. Scribe không tự đưa ra chẩn đoán; mọi mục đều lấy từ lời đã nói trong buổi khám.",
      cta: "Mở công cụ Scribe",
    },
    scribeTool: {
      title: "Từ bản ghi âm buổi khám đến bệnh án SOAP",
      intro: "Tải lên tệp ghi âm buổi khám bằng tiếng Việt. Hệ thống phiên âm, hiệu chỉnh thuật ngữ và soạn bản nháp SOAP để bác sĩ kiểm tra.",
      back: "Về trang chính",
      health: {
        checking: "Đang kết nối…",
        ready: "Hệ thống sẵn sàng",
        demo: "Chế độ demo",
        degraded: "Một phần dịch vụ chưa sẵn sàng",
        down: "Mất kết nối máy chủ",
      },
      dropzone: "Kéo thả tệp âm thanh vào đây, hoặc bấm để chọn",
      dropzoneHint: "Hỗ trợ WAV, MP3, M4A, OGG, FLAC. Tối đa 25 MB.",
      contextLabel: "Bối cảnh buổi khám (tùy chọn)",
      removeFile: "Bỏ tệp",
      submit: "Tạo bệnh án SOAP",
      steps: ["Phiên âm", "Hiệu chỉnh thuật ngữ", "Soạn bệnh án SOAP"],
      progressLabel: "Tiến độ xử lý",
      errorTitle: "Đã xảy ra lỗi.",
      retry: "Thử lại",
      resultTitle: "Bệnh án SOAP (bản nháp)",
      reviewBanner: "Bản nháp do AI tạo, cần bác sĩ kiểm tra trước khi đưa vào hồ sơ bệnh án.",
      missingTitle: "Thông tin còn thiếu",
      processedIn: "Xử lý trong {seconds} giây",
      copy: "Sao chép",
      copied: "Đã sao chép",
      copyFailed: "Không sao chép được",
      newNote: "Tạo bệnh án mới",
      copyHeading: "BỆNH ÁN SOAP (bản nháp, cần bác sĩ kiểm tra)",
      disclaimer: "Bản demo cho nhân viên y tế. Không dùng cho chẩn đoán lâm sàng chính thức.",
    },
    marquee: [
      "Xác nhận read-back",
      "Đánh dấu nội dung rủi ro",
      "Cảnh báo độ tin cậy thấp",
      "Không lưu âm thanh",
      "Chuyển phiên dịch viên",
      "Bản nháp SOAP chờ duyệt",
    ],
    problem: {
      kicker: "Rủi ro đang có",
      title: "Một câu bị hiểu sai có thể đi xa hơn một cuộc hội thoại.",
      body: "CarePath không hứa thay thế phán đoán lâm sàng hay phiên dịch viên. Sản phẩm tập trung vào một việc hẹp hơn: làm cho điểm cần xác nhận trở nên nhìn thấy được.",
      memoryStat: "40–80%",
      memoryDetail: "thông tin y khoa bằng lời nói có thể bị quên ngay; gần một nửa phần được nhớ lại có thể không chính xác.",
      translationStat: "Tới 66%",
      translationDetail: "bộ hướng dẫn xuất viện được Google dịch sang tiếng Nga trong một nghiên cứu năm 2025 có ít nhất một điểm không chính xác.",
      framing: "Mỗi lượt khám không được phiên dịch đúng là một rủi ro mà cơ sở y tế đang gánh cho người bệnh, uy tín và quy trình chăm sóc.",
    },
    safety: {
      kicker: "An toàn theo thiết kế",
      title: "Nội dung quan trọng không tự động đi thẳng tới người bệnh hay hồ sơ.",
      body: "Năm cơ chế dưới đây áp dụng cho cả phiên dịch lẫn bản nháp Scribe. Đây là nguyên tắc sản phẩm, không phải lời hứa về kết quả điều trị.",
      items: [
        {
          title: { vi: "Xác nhận read-back", en: "Read-back confirmation" },
          body: {
            vi: "Liều, thuốc, tần suất và phủ định được tách riêng để bác sĩ kiểm tra trước khi phát.",
            en: "Dose, drug, frequency, and negation are separated for clinician review before delivery.",
          },
        },
        {
          title: { vi: "Đánh dấu rủi ro", en: "Risk highlighting" },
          body: {
            vi: "Màu sắc đi cùng nhãn chữ để thuốc, dị ứng, con số và dấu hiệu nguy cơ không bị chìm trong hội thoại.",
            en: "Color and text labels keep drugs, allergies, numbers, and red flags visible.",
          },
        },
        {
          title: { vi: "Độ tin cậy thấp", en: "Low confidence" },
          body: {
            vi: "Kết quả không chắc chắn luôn hiện cảnh báo và yêu cầu nói lại hoặc nhập văn bản.",
            en: "Uncertain output is visibly flagged and asks for repetition or typed input.",
          },
        },
        {
          title: { vi: "Phiên dịch viên", en: "Human interpreter" },
          body: {
            vi: "Nội dung nguy cơ rất cao dừng tự động và giữ thao tác chuyển phiên dịch viên trong tầm tay.",
            en: "Very high-risk content stops automation and keeps interpreter escalation within reach.",
          },
        },
        {
          title: { vi: "Thông báo sử dụng AI", en: "AI-use disclosure" },
          body: {
            vi: "Công cụ phiên dịch không lưu âm thanh; người dùng luôn được biết đây là AI và có thể yêu cầu con người hỗ trợ.",
            en: "The translation tool stores no audio; users are told AI is involved and may request human support.",
          },
        },
      ],
    },
    process: {
      kicker: "Một vòng xác nhận rõ ràng",
      title: "Nói. Kiểm tra. Chỉ phát sau khi xác nhận.",
      steps: [
        {
          title: "Nói theo lượt",
          body: "Bác sĩ và bệnh nhân nói theo từng lượt ngắn; bản mô phỏng không sử dụng micro.",
        },
        {
          title: "Nhìn thấy rủi ro",
          body: "Nội dung song ngữ xuất hiện cùng nhãn thuốc, liều, phủ định và độ tin cậy.",
        },
        {
          title: "Xác nhận hoặc chuyển người",
          body: "Bác sĩ xác nhận read-back, chỉnh bản dịch, hoặc yêu cầu phiên dịch viên.",
        },
      ],
    },
    cost: {
      kicker: "Đối chiếu minh bạch",
      title: "Chi phí hiện trạng cần được nhìn đúng ngữ cảnh.",
      body: "Các con số dưới đây là điểm tham chiếu công khai, không phải báo giá dịch vụ y tế và không phải cam kết tiết kiệm của CarePath.",
      interpreterTitle: "Khung tham chiếu phiên dịch",
      interpreterValue: "150.000–250.000 đồng/giờ",
      interpreterNote: "Mức trần tham chiếu tại Phú Yên năm 2021: 150.000 đồng/giờ cho thời lượng từ bốn giờ, 250.000 đồng/giờ cho thời lượng ngắn hơn. Ngoài phạm vi quyết định, các bên tự thỏa thuận. Đây không phải giá phiên dịch y khoa toàn quốc.",
      incidentTitle: "Chi phí tăng thêm do biến cố thuốc",
      incidentValue: "5.746 USD / biến cố",
      incidentNote: "Ước tính AHRQ tại bệnh viện Hoa Kỳ, công bố năm 2019. Không phải số liệu Việt Nam, không riêng lỗi phiên dịch và có khoảng bất định rộng.",
      pilotTitle: "Chương trình thí điểm",
      pilotValue: "TODO-pricing",
      pilotNote: "Giá sẽ được công khai sau khi phạm vi hỗ trợ, thời lượng và trách nhiệm của các bên được xác định. Không có giá gạch bỏ hoặc khan hiếm giả.",
    },
    pilot: {
      kicker: "Bản demo của cơ sở bạn",
      title: "Giữ lại bản demo bạn vừa tạo",
      body: "Thông tin cơ sở, chuyên khoa, kịch bản và phần hội thoại đã xem sẽ đi cùng yêu cầu thí điểm. Không có hộp đồng ý tiếp thị được chọn sẵn.",
      transcriptNote: "Bản ghi song ngữ hiện tại được đính kèm trong dữ liệu yêu cầu.",
    },
    footer: {
      promise: "Hỗ trợ AI, bác sĩ xác nhận.",
      posture: "Thiết kế theo hướng giảm thiểu dữ liệu, nhận biết yêu cầu của Nghị định 13/PDP và định vị phù hợp với nguyên tắc tiếp cận ngôn ngữ của §1557. Đây không phải tuyên bố chứng nhận pháp lý.",
      honesty: "Bản mô phỏng không dịch trực tiếp, không thu âm và không đưa ra lời khuyên y tế.",
      contact: "Liên hệ chương trình thí điểm",
    },
  },
  en: {
    language: {
      label: "Language",
      vi: "VI",
      en: "EN",
    },
    nav: {
      demo: "Simulation",
      scribe: "Scribe",
      safety: "Safety mechanics",
      process: "How it works",
      cost: "Cost references",
    },
    demo: {
      brand: "CarePath Interpreter",
      consoleCta: "Open the Interpreter tool",
      disclosure: "Simulation — not a live translation",
      privacy: "No recording",
      clinic: "Clinic name",
      specialty: "Specialty",
      chooseScenario: "Choose a scenario",
      progress: ["Scenario selected", "Hear the conversation", "Confirm read-back", "Keep transcript"],
      start: "Start",
      continue: "Continue",
      pause: "Pause",
      next: "Next turn",
      replay: "Replay",
      empty: "The conversation will appear here.",
      doctor: "Doctor",
      patient: "Patient",
      blocked: "Blocked until the clinician confirms.",
      riskDetails: "Risk details",
      customTitle: "Try typing",
      simulation: "Simulation",
      blockedFlag: "Translation blocked",
      readbackTitle: "Confirm critical information",
      entityType: "Type",
      source: "Source",
      translation: "Translation",
      editTranslation: "Edit the translation before confirmation",
      confirm: "Confirm and continue",
      interpreter: "Request an interpreter",
      escalationStopped: "Automated translation stopped",
      escalationTitle: "Prioritize an interpreter for high-risk content",
      escalationBody: "This is a simulation. In the product, this content is not delivered to the patient before appropriate confirmation.",
      escalationConfirm: "Confirm interpreter escalation",
      customLabel: "Try typing one line",
      customPlaceholder: "The simulation responds with a fixed message only",
      customAdd: "Add to simulation",
      customNote: "This is not live machine translation.",
      customResponse: "Custom text received in the simulation. This is not a live translation.",
      download: "Download demo transcript",
      tiers: {
        low: "low",
        medium: "medium",
        high: "high",
        critical: "critical",
      },
      entityKinds: {
        Thuốc: "Drug",
        Liều: "Dose",
        "Tần suất": "Frequency",
        "Thời gian": "Duration",
        "Phủ định": "Negation",
      },
    },
    form: {
      name: "Full name",
      clinic: "Clinic or hospital",
      role: "Role",
      contact: "Email or Zalo",
      message: "Message",
      prepare: "Prepare pilot request",
      submitting: "Sending request…",
      posted: "Pilot request sent.",
      mailOpened: "An email draft was opened. Review and send it to finish.",
      failed: "The request could not be sent. Check the connection and try again.",
      required: "Please complete this field.",
    },
    hero: {
      titleBefore: "Medical interpreting and notes,",
      titleAfter: "confirmed before use.",
      body: "Live Vietnamese-English interpreting with a confirmation step, plus Scribe drafts of the visit's SOAP note. No diagnosis, no treatment advice.",
      primaryCta: "Watch the 90-second demo",
      secondaryCta: "See the safety mechanics",
      note: "No signup. No recording. No data sent.",
    },
    modules: {
      heading: "Two modules",
      interpreter: {
        name: "Interpreter",
        body: "Live Vietnamese-English conversation; risky content is delivered only after the clinician confirms.",
      },
      scribe: {
        name: "Scribe",
        body: "Vietnamese SOAP-note drafts from the visit conversation, always awaiting clinician review.",
      },
    },
    scribe: {
      brand: "CarePath Scribe",
      kicker: "The Scribe module",
      title: "From spoken visit to a SOAP draft.",
      body: "Scribe listens to the Vietnamese consultation, fixes misrecognized medical terms, and arranges a SOAP draft. Nothing enters the record until the clinician approves.",
      disclosure: "Simulation with sample data, not a real record",
      steps: {
        raw: {
          label: "1. Raw ASR transcript",
          caption: "Underlined: what the machine misheard in the raw transcript.",
        },
        corrected: {
          label: "2. After term correction",
          caption: "Highlighted: corrected terms and numbers.",
        },
        soap: {
          label: "3. SOAP draft",
          caption: "Draft arranged in four sections, each line awaiting clinician review.",
        },
      },
      status: "Awaiting clinician review",
      soapLabels: {
        s: "Subjective",
        o: "Objective",
        a: "Assessment",
        p: "Plan",
      },
      note: "The content above is sample data for this simulation. Scribe does not produce its own diagnosis; every line comes from what was said during the visit.",
      cta: "Open the Scribe tool",
    },
    scribeTool: {
      title: "From visit recording to a SOAP note",
      intro: "Upload a Vietnamese consultation recording. The system transcribes it, corrects medical terms, and drafts a SOAP note for clinician review.",
      back: "Back to overview",
      health: {
        checking: "Connecting…",
        ready: "System ready",
        demo: "Demo mode",
        degraded: "Some services are not ready",
        down: "Server unreachable",
      },
      dropzone: "Drop an audio file here, or click to choose",
      dropzoneHint: "WAV, MP3, M4A, OGG, FLAC. Up to 25 MB.",
      contextLabel: "Encounter context (optional)",
      removeFile: "Remove file",
      submit: "Draft the SOAP note",
      steps: ["Transcribing", "Correcting terms", "Drafting the SOAP note"],
      progressLabel: "Processing progress",
      errorTitle: "Something went wrong.",
      retry: "Try again",
      resultTitle: "SOAP note (draft)",
      reviewBanner: "AI-generated draft. A clinician must review it before it enters the medical record.",
      missingTitle: "Missing information",
      processedIn: "Processed in {seconds} s",
      copy: "Copy",
      copied: "Copied",
      copyFailed: "Copy failed",
      newNote: "Start a new note",
      copyHeading: "SOAP NOTE (draft, requires clinician review)",
      disclaimer: "Demo for healthcare staff. Not for formal clinical diagnosis.",
    },
    marquee: [
      "Read-back confirmation",
      "Risk highlighting",
      "Low-confidence warning",
      "No audio storage",
      "Interpreter escalation",
      "SOAP drafts held for review",
    ],
    problem: {
      kicker: "The current risk",
      title: "A misunderstood sentence can travel beyond one conversation.",
      body: "CarePath does not promise to replace clinical judgment or human interpreters. It focuses on a narrower job: making confirmation points visible.",
      memoryStat: "40–80%",
      memoryDetail: "of verbal medical information may be forgotten immediately; almost half of what is retained may be incorrect.",
      translationStat: "Up to 66%",
      translationDetail: "of Russian Google-translated discharge-instruction sets in a 2025 study contained at least one inaccuracy.",
      framing: "Every visit without accurate interpretation creates risk for the patient, the clinic's reputation, and its care process.",
    },
    safety: {
      kicker: "Safety by design",
      title: "Important content does not pass straight to the patient or the record.",
      body: "These five mechanics apply to both interpreting and Scribe drafts. They are product principles, not treatment-outcome claims.",
      items: [],
    },
    process: {
      kicker: "A clear confirmation loop",
      title: "Speak. Review. Deliver only after confirmation.",
      steps: [
        {
          title: "Speak in turns",
          body: "Clinician and patient use short turns; this simulation never uses the microphone.",
        },
        {
          title: "See the risk",
          body: "Bilingual text appears with drug, dose, negation, and confidence labels.",
        },
        {
          title: "Confirm or escalate",
          body: "The clinician confirms the read-back, edits the translation, or requests an interpreter.",
        },
      ],
    },
    cost: {
      kicker: "Transparent comparison",
      title: "Status-quo costs need honest context.",
      body: "These figures are public reference points, not medical-service quotes or CarePath savings claims.",
      interpreterTitle: "Interpreter reference framework",
      interpreterValue: "VND 150,000–250,000/hour",
      interpreterNote: "A 2021 Phú Yên reference ceiling is VND 150,000/hour for work lasting at least four hours and VND 250,000/hour for shorter work. Other work is negotiated. This is not a nationwide medical-interpreting price.",
      incidentTitle: "Incremental adverse-drug-event cost",
      incidentValue: "USD 5,746 / event",
      incidentNote: "AHRQ estimate for US hospitals, published in 2019. It is not Vietnamese data, is not specific to interpreting errors, and has a wide uncertainty interval.",
      pilotTitle: "Pilot program",
      pilotValue: "TODO-pricing",
      pilotNote: "Pricing will be published after support scope, duration, and responsibilities are defined. No fake markdown or scarcity.",
    },
    pilot: {
      kicker: "Your clinic's demo",
      title: "Keep the demo you just created",
      body: "Your clinic, specialty, scenario, and viewed transcript travel with the pilot request. There is no preselected marketing consent.",
      transcriptNote: "The current bilingual transcript is attached to the request data.",
    },
    footer: {
      promise: "AI assistance, clinician confirmed.",
      posture: "Designed around data minimization, awareness of Decree 13/PDP obligations, and §1557-aligned language-access positioning. This is not a legal certification claim.",
      honesty: "The simulation does not translate live, record audio, or provide medical advice.",
      contact: "Contact the pilot program",
    },
  },
};

strings.en.safety.items = strings.vi.safety.items;

export function copyFor(language: Language): PageCopy {
  return strings[language];
}
