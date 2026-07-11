import type { Language, LocalizedText } from "../demo/types";

export const sources = {
  research: {
    label: "CarePath research report",
    href: "https://github.com/truong-tt/carepath/blob/main/docs/research.md",
  },
} as const;

interface SafetyItem {
  title: LocalizedText;
  body: LocalizedText;
}

export type ProductKey = "interpreter" | "scribe";

interface ProductCopy {
  name: string;
  helper: string;
  preview: string;
  timing: string;
  chooserSafety: string;
  audience: string;
  input: string;
  output: string;
  status: string;
  disclosure: string;
  title: string;
  body: string;
  workflow: Array<{ title: string; body: string }>;
  safety: string[];
  cta: {
    explore: string;
    open: string;
    pilot: string;
  };
}

interface SafetyCardCopy {
  title: string;
  body: string;
  items: SafetyItem[];
}

interface PageCopy {
  language: {
    label: string;
    vi: string;
    en: string;
  };
  nav: {
    interpreter: string;
    scribe: string;
    safety: string;
    pilot: string;
    menu: string;
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
    interest: string;
    interestOptions: Record<"interpreter" | "scribe" | "both", string>;
    message: string;
    prepare: string;
    submitting: string;
    posted: string;
    mailOpened: string;
    failed: string;
    required: string;
  };
  hero: {
    title: string;
    body: string;
    interpreterCta: string;
    scribeCta: string;
  };
  gateway: {
    heading: string;
    body: string;
    audience: string;
    input: string;
    output: string;
    workflow: string;
    useWhen: string;
    detailLabel: string;
  };
  products: Record<ProductKey, ProductCopy>;
  scribe: {
    brand: string;
    disclosure: string;
    steps: Record<"raw" | "corrected" | "soap", { label: string; caption: string }>;
    status: string;
    soapLabels: Record<"s" | "o" | "a" | "p", string>;
    note: string;
  };
  scribeTool: {
    title: string;
    helper: string;
    intro: string;
    preStartSteps: [string, string, string, string];
    preStartReminder: string;
    uploadNotice: string;
    continue: string;
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
  evidence: {
    title: string;
    body: string;
    sampleLabel: string;
    researchLabel: string;
    source: string;
    items: Array<{
      kind: "interpreter" | "scribe" | "research";
      product: string;
      title: string;
      body: string;
      detail: string;
    }>;
  };
  safety: {
    title: string;
    body: string;
    trust: Array<{ title: string; body: string }>;
    shared: SafetyCardCopy;
    interpreter: SafetyCardCopy;
    scribe: SafetyCardCopy;
  };
  pilot: {
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
      interpreter: "Phiên dịch khám bệnh trực tiếp",
      scribe: "Ghi chép bệnh án AI",
      safety: "An toàn",
      pilot: "Thí điểm",
      menu: "Mở điều hướng",
    },
    demo: {
      brand: "CarePath Phiên dịch",
      consoleCta: "Mở công cụ Phiên dịch",
      disclosure: "Bản mô phỏng — không phải bản dịch trực tiếp",
      privacy: "Không thu âm",
      clinic: "Tên cơ sở",
      specialty: "Chuyên khoa",
      chooseScenario: "Chọn kịch bản",
      progress: ["Kịch bản đã chọn", "Nghe hội thoại", "Đọc lại để xác nhận", "Nhận bản ghi"],
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
      interest: "Chức năng quan tâm",
      interestOptions: {
        interpreter: "Phiên dịch khám bệnh trực tiếp",
        scribe: "Ghi chép bệnh án AI",
        both: "Cả hai chức năng",
      },
      message: "Lời nhắn",
      prepare: "Chuẩn bị yêu cầu thí điểm",
      submitting: "Đang gửi yêu cầu…",
      posted: "Đã gửi yêu cầu thí điểm.",
      mailOpened: "Đã mở bản nháp email. Hãy kiểm tra và gửi thư để hoàn tất.",
      failed: "Không thể gửi yêu cầu. Vui lòng kiểm tra kết nối và thử lại.",
      required: "Vui lòng điền trường này.",
    },
    hero: {
      title: "Bạn muốn hỗ trợ việc gì hôm nay?",
      body: "Chọn một công việc để bắt đầu.",
      interpreterCta: "Bắt đầu phiên dịch",
      scribeCta: "Bắt đầu ghi chép",
    },
    gateway: {
      heading: "Bạn muốn hỗ trợ việc gì hôm nay?",
      body: "Hai công việc riêng biệt, cùng giữ bác sĩ ở vị trí quyết định.",
      audience: "Dành cho",
      input: "Đầu vào",
      output: "Đầu ra",
      workflow: "Luồng chính",
      useWhen: "Dùng khi",
      detailLabel: "Thông tin chi tiết về hai chức năng",
    },
    products: {
      interpreter: {
        name: "Phiên dịch khám bệnh trực tiếp",
        helper: "Medical Interpreter",
        preview: "Bác sĩ nói → Bệnh nhân nghe → Bệnh nhân trả lời → Bác sĩ hiểu",
        timing: "Trong buổi khám",
        chooserSafety: "Chỉ phiên dịch, không đưa ra lời khuyên y tế.",
        audience: "Phù hợp khi bác sĩ và bệnh nhân không cùng ngôn ngữ.",
        input: "Hội thoại Việt–Anh theo từng lượt.",
        output: "Bản dịch hiển thị theo mức rủi ro; nội dung nguy cơ cao chờ bác sĩ xác nhận.",
        status: "Mô phỏng tương tác — chưa phải phiên dịch trực tiếp.",
        disclosure: "Bản mô phỏng không sử dụng micro và không lưu âm thanh.",
        title: "Giữ quyền xác nhận ở phía bác sĩ.",
        body: "Dịch hai chiều giữa bác sĩ tiếng Việt và bệnh nhân tiếng Anh trong lúc khám.",
        workflow: [
          {
            title: "Hội thoại",
            body: "Bác sĩ và người bệnh trao đổi theo từng lượt ngắn.",
          },
          {
            title: "Bác sĩ xác nhận",
            body: "Thuốc, liều, phủ định và nội dung rủi ro được tách ra để kiểm tra.",
          },
          {
            title: "Bản dịch được phát",
            body: "Lượt nguy cơ cao hoặc nghiêm trọng chỉ đến người bệnh sau xác nhận; cảnh báo vẫn hiển thị ở các lượt còn lại.",
          },
        ],
        safety: [
          "Chặn lượt nguy cơ cao và nghiêm trọng",
          "Hiện cảnh báo khi độ tin cậy thấp",
          "Đọc lại để xác nhận trước khi phát nội dung quan trọng",
          "Luôn có đường chuyển sang phiên dịch viên",
        ],
        cta: {
          explore: "Tìm hiểu phiên dịch",
          open: "Bắt đầu phiên dịch",
          pilot: "Thí điểm phiên dịch",
        },
      },
      scribe: {
        name: "Ghi chép bệnh án AI",
        helper: "AI Scribe",
        preview: "Nghe buổi khám → Tạo ghi chú → Bác sĩ kiểm tra",
        timing: "Sau buổi khám",
        chooserSafety: "Bác sĩ cần kiểm tra trước khi sử dụng.",
        audience: "Phù hợp khi bác sĩ muốn giảm thời gian nhập liệu sau khám.",
        input: "Tệp âm thanh buổi khám do cơ sở chủ động tải lên.",
        output: "Bản nháp SOAP có đánh dấu thông tin còn thiếu.",
        status: "Công cụ thí điểm — mọi bản nháp cần bác sĩ duyệt.",
        disclosure: "Tệp âm thanh do cơ sở chủ động tải lên được xử lý để tạo bản nháp; bản nháp không tự đi vào hồ sơ.",
        title: "Từ lời đã nói đến bản nháp có cấu trúc.",
        body: "AI nghe buổi khám và tạo ghi chú y khoa có cấu trúc.",
        workflow: [
          {
            title: "Tải lên hội thoại",
            body: "Cơ sở chủ động chọn tệp âm thanh của buổi khám.",
          },
          {
            title: "Hiệu chỉnh thuật ngữ",
            body: "Các thuật ngữ và con số nhận dạng sai được làm nổi bật.",
          },
          {
            title: "Bản nháp SOAP",
            body: "Nội dung được xếp theo SOAP và giữ ở trạng thái chờ bác sĩ duyệt.",
          },
        ],
        safety: [
          "Luôn ghi rõ đây là bản nháp",
          "Hiện danh sách thông tin còn thiếu",
          "Đối chiếu nội dung y khoa với hội thoại",
          "Bác sĩ duyệt trước khi đưa vào hồ sơ",
        ],
        cta: {
          explore: "Tìm hiểu ghi chép",
          open: "Bắt đầu ghi chép",
          pilot: "Thí điểm ghi chép",
        },
      },
    },
    scribe: {
      brand: "Ghi chép bệnh án AI",
      disclosure: "Bản mô phỏng với dữ liệu mẫu, không phải hồ sơ thật",
      steps: {
        raw: {
          label: "1. Phiên âm tự động",
          caption: "Gạch chân: đoạn hệ thống nghe sai trong bản phiên âm tự động.",
        },
        corrected: {
          label: "2. Sau hiệu chỉnh thuật ngữ",
          caption: "Tô nền: thuật ngữ và con số đã được hiệu chỉnh.",
        },
        soap: {
          label: "3. Bản ghi y khoa theo bốn mục SOAP",
          caption: "Bản nháp xếp theo bốn mục SOAP, chờ bác sĩ duyệt từng dòng.",
        },
      },
      status: "Chờ bác sĩ duyệt",
      soapLabels: {
        s: "Chủ quan",
        o: "Khách quan",
        a: "Đánh giá",
        p: "Kế hoạch",
      },
      note: "Trong bản mô phỏng này, mọi mục đều truy nguyên từ dữ liệu mẫu; khi sử dụng công cụ, bác sĩ vẫn phải đối chiếu bản nháp với hội thoại.",
    },
    scribeTool: {
      title: "Ghi chép bệnh án AI",
      helper: "AI Scribe",
      intro: "AI nghe buổi khám và tạo ghi chú y khoa có cấu trúc.",
      preStartSteps: [
        "Bật ghi âm buổi khám",
        "AI chuyển lời nói thành văn bản",
        "AI tạo ghi chú y khoa có cấu trúc",
        "Bác sĩ kiểm tra và chỉnh sửa trước khi sử dụng",
      ],
      preStartReminder: "AI chỉ hỗ trợ soạn thảo. Bác sĩ cần kiểm tra lại nội dung trước khi sử dụng.",
      uploadNotice: "CarePath dùng tệp ghi âm do cơ sở chọn và tải lên; màn hình này không tự bắt đầu micro.",
      continue: "Tiếp tục ghi chép",
      back: "Tất cả chức năng",
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
    evidence: {
      title: "Xem cách mỗi sản phẩm giữ điểm cần duyệt ở đúng chỗ.",
      body: "Các màn hình dưới đây dùng dữ liệu mẫu đã làm sạch. Bằng chứng nghiên cứu dẫn về báo cáo nguồn của CarePath; không có lời chứng thực hoặc tuyên bố kết quả giả định.",
      sampleLabel: "Dữ liệu mẫu đã làm sạch",
      researchLabel: "Nguồn nghiên cứu",
      source: "Đọc báo cáo nghiên cứu và nguồn trích dẫn",
      items: [
        {
          kind: "interpreter",
          product: "Phiên dịch khám bệnh trực tiếp",
          title: "Lượt nguy cơ được giữ lại cho bác sĩ.",
          body: "Màn hình mô phỏng hiển thị đồng thời câu nguồn, bản dịch, nhãn rủi ro và hành động xác nhận.",
          detail: "Dữ liệu mẫu: dị ứng penicillin được đánh dấu và chưa phát cho người bệnh.",
        },
        {
          kind: "scribe",
          product: "Ghi chép bệnh án AI",
          title: "Bản nháp cho thấy phần cần kiểm tra.",
          body: "Màn hình mẫu đặt bản gõ thô, thuật ngữ đã sửa và bốn mục SOAP trong cùng một luồng duyệt.",
          detail: "Dữ liệu mẫu: mục Đánh giá vẫn ở trạng thái chờ bác sĩ duyệt.",
        },
        {
          kind: "research",
          product: "Cơ sở nghiên cứu",
          title: "Thiết kế cho việc xác nhận nhìn thấy được.",
          body: "Báo cáo CarePath tổng hợp các nguồn về khả năng quên thông tin y khoa bằng lời và sai sót trong bản dịch máy hướng dẫn xuất viện.",
          detail: "Các nguồn, giới hạn và bối cảnh nghiên cứu được giữ cùng báo cáo thay vì chuyển thành tuyên bố tiếp thị.",
        },
      ],
    },
    safety: {
      title: "Một lớp giám sát chung. Hai cơ chế an toàn riêng.",
      body: "CarePath không thay bác sĩ ra quyết định. Mỗi sản phẩm dừng đầu ra cần xác nhận ở đúng cổng duyệt của quy trình mà nó phục vụ.",
      trust: [
        {
          title: "Bác sĩ kiểm tra trước khi dùng",
          body: "Bản nháp và nội dung cần xác nhận không tự trở thành quyết định điều trị.",
        },
        {
          title: "Độ không chắc chắn luôn hiển thị",
          body: "Kết quả thiếu hoặc chưa chắc chắn được gắn cờ rõ ràng.",
        },
        {
          title: "Không thay thế chẩn đoán hoặc tư vấn",
          body: "CarePath chỉ hỗ trợ quy trình; bác sĩ vẫn quyết định chuyên môn.",
        },
      ],
      shared: {
        title: "Giám sát chung cho CarePath",
        body: "Bốn nguyên tắc áp dụng cho cả hai chức năng.",
        items: [
          {
            title: { vi: "Bác sĩ giữ quyền quyết định", en: "Clinician authority" },
            body: { vi: "Bác sĩ giữ quyền kiểm soát; lượt phiên dịch nguy cơ cao và mọi bản nháp ghi chép đều chờ bước xác nhận phù hợp.", en: "The clinician stays in control; high-risk Interpreter turns and every Scribe draft wait at the appropriate review gate." },
          },
          {
            title: { vi: "Thông báo AI rõ ràng", en: "Clear AI disclosure" },
            body: { vi: "Trạng thái mô phỏng, thí điểm và bản nháp luôn được gọi đúng tên.", en: "Simulation, pilot, and draft states are always named plainly." },
          },
          {
            title: { vi: "Độ không chắc chắn nhìn thấy được", en: "Visible uncertainty" },
            body: { vi: "Kết quả thiếu hoặc không chắc chắn không bị giao im lặng.", en: "Missing or uncertain output is never delivered silently." },
          },
          {
            title: { vi: "Giảm thiểu dữ liệu", en: "Data minimization" },
            body: { vi: "Chỉ xử lý dữ liệu cần cho lượt dịch hoặc bản nháp đang thực hiện.", en: "Only data needed for the active translation turn or draft is processed." },
          },
        ],
      },
      interpreter: {
        title: "An toàn khi phiên dịch khám bệnh",
        body: "Nội dung nguy cơ không đi thẳng tới người bệnh.",
        items: [
          {
            title: { vi: "Chặn nguy cơ cao", en: "High-risk blocking" },
            body: { vi: "Lượt nguy cơ cao và nghiêm trọng chờ bác sĩ xác nhận.", en: "High- and critical-risk turns wait for clinician confirmation." },
          },
          {
            title: { vi: "Cảnh báo độ tin cậy thấp", en: "Low-confidence warnings" },
            body: { vi: "Kết quả không chắc chắn luôn được gắn cờ rõ ràng.", en: "Uncertain output is always visibly flagged." },
          },
          {
            title: { vi: "Đọc lại để xác nhận hoặc chuyển người", en: "Read-back or human escalation" },
            body: { vi: "Bác sĩ xác nhận, chỉnh sửa hoặc yêu cầu phiên dịch viên.", en: "The clinician confirms, edits, or requests an interpreter." },
          },
          {
            title: { vi: "Thông báo sử dụng AI", en: "AI-use disclosure" },
            body: {
              vi: "Công cụ phiên dịch không lưu âm thanh; người dùng luôn được biết đây là AI và có thể yêu cầu con người hỗ trợ.",
              en: "The Interpreter stores no audio; users are told AI is involved and may request human support.",
            },
          },
        ],
      },
      scribe: {
        title: "An toàn khi ghi chép bệnh án AI",
        body: "Bản nháp không tự trở thành hồ sơ bệnh án.",
        items: [
          {
            title: { vi: "Trạng thái bản nháp", en: "Draft-only status" },
            body: { vi: "Mọi kết quả đều ghi rõ cần bác sĩ kiểm tra.", en: "Every result states that clinician review is required." },
          },
          {
            title: { vi: "Thông tin còn thiếu", en: "Missing information" },
            body: { vi: "Phần chưa có trong hội thoại được nêu ra thay vì tự điền.", en: "Details absent from the conversation are surfaced rather than invented." },
          },
          {
            title: { vi: "Đối chiếu với nội dung nguồn", en: "Check against source content" },
            body: { vi: "Mô hình được yêu cầu không tự thêm chẩn đoán, tư vấn hoặc thuốc; bác sĩ vẫn phải đối chiếu bản nháp với hội thoại.", en: "The model is instructed not to add diagnoses, advice, or medication; the clinician must still check the draft against the conversation." },
          },
          {
            title: { vi: "Duyệt trước hồ sơ", en: "Review before record entry" },
            body: { vi: "Bác sĩ kiểm tra trước khi bản nháp được đưa vào hồ sơ.", en: "A clinician checks the draft before it enters the record." },
          },
        ],
      },
    },
    pilot: {
      title: "Chọn chức năng phù hợp với quy trình của bạn.",
      body: "Yêu cầu thí điểm có thể dành cho phiên dịch, ghi chép hoặc cả hai. Phạm vi và giá được xác định sau khi cùng xem quy trình thực tế; không có báo giá giả định trên trang này.",
      transcriptNote: "Nếu chọn phiên dịch, kịch bản và bản ghi song ngữ hiện tại sẽ đi cùng yêu cầu.",
    },
    footer: {
      promise: "AI hỗ trợ, bác sĩ giữ quyền quyết định.",
      posture: "Thiết kế theo hướng giảm thiểu dữ liệu, nhận biết yêu cầu của Nghị định 13/PDP và định vị phù hợp với nguyên tắc tiếp cận ngôn ngữ của §1557. Đây không phải tuyên bố chứng nhận pháp lý.",
      honesty: "Phiên dịch khám bệnh trực tiếp là bản mô phỏng tương tác; Ghi chép bệnh án AI là công cụ thí điểm tạo bản nháp. Cả hai đều cần giám sát của nhân viên y tế.",
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
      interpreter: "Interpreter",
      scribe: "Scribe",
      safety: "Safety",
      pilot: "Pilot",
      menu: "Open navigation",
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
      interest: "Product interest",
      interestOptions: {
        interpreter: "CarePath Interpreter",
        scribe: "CarePath Scribe",
        both: "Both products",
      },
      message: "Message",
      prepare: "Prepare pilot request",
      submitting: "Sending request…",
      posted: "Pilot request sent.",
      mailOpened: "An email draft was opened. Review and send it to finish.",
      failed: "The request could not be sent. Check the connection and try again.",
      required: "Please complete this field.",
    },
    hero: {
      title: "One care journey. Two CarePath products.",
      body: "Interpreter supports Vietnamese–English clinical conversations with risk blocking and clinician confirmation. Scribe turns uploaded visit audio into a SOAP draft for clinician review.",
      interpreterCta: "Explore Interpreter",
      scribeCta: "Explore Scribe",
    },
    gateway: {
      heading: "Choose the right product for the right point in care.",
      body: "Two separate jobs, both keeping the clinician in control.",
      audience: "For",
      input: "Input",
      output: "Output",
      workflow: "Core flow",
      useWhen: "Use when",
      detailLabel: "Product details",
    },
    products: {
      interpreter: {
        name: "CarePath Interpreter",
        helper: "Medical Interpreter",
        preview: "Doctor speaks → Patient hears → Patient replies → Doctor understands",
        timing: "During the visit",
        chooserSafety: "Translation only; it does not provide medical advice.",
        audience: "Clinicians and care teams who need clear Vietnamese–English communication during a visit.",
        input: "Turn-by-turn Vietnamese–English conversation.",
        output: "Translation follows the risk tier; high-risk content waits for clinician confirmation.",
        status: "Interactive simulation — not live interpreting.",
        disclosure: "The simulation does not use the microphone or store audio.",
        title: "Keep confirmation with the clinician.",
        body: "Interpreter only translates the conversation. High- or critical-risk content stays blocked from the patient until the clinician confirms, edits, or escalates to a human interpreter.",
        workflow: [
          {
            title: "Conversation",
            body: "Clinician and patient exchange short, turn-based statements.",
          },
          {
            title: "Clinician confirmation",
            body: "Drugs, doses, negations, and risky content are separated for review.",
          },
          {
            title: "Translation delivered",
            body: "High- or critical-risk turns reach the patient only after confirmation; warnings remain visible on other turns.",
          },
        ],
        safety: [
          "Block high- and critical-risk turns",
          "Show low-confidence warnings",
          "Require read-back for critical information",
          "Keep human-interpreter escalation available",
        ],
        cta: {
          explore: "Explore Interpreter",
          open: "Open Interpreter",
          pilot: "Pilot Interpreter",
        },
      },
      scribe: {
        name: "CarePath Scribe",
        helper: "AI Scribe",
        preview: "Listen to the visit → Create notes → Clinician reviews",
        timing: "After the visit",
        chooserSafety: "Clinician review is required before use.",
        audience: "Clinicians who want to reduce documentation time after Vietnamese visits.",
        input: "Visit audio intentionally uploaded by the care team.",
        output: "A SOAP draft with missing information called out.",
        status: "Pilot tool — every draft requires clinician review.",
        disclosure: "Audio intentionally uploaded by the care team is processed to create the draft; the draft never enters the record automatically.",
        title: "Turn what was said into a structured draft.",
        body: "Scribe transcribes the Vietnamese conversation, corrects medical terms, and is instructed to arrange only spoken content into a SOAP draft. The clinician must still compare the draft with the conversation and remove unsupported content.",
        workflow: [
          {
            title: "Upload the visit",
            body: "The care team intentionally selects the visit audio file.",
          },
          {
            title: "Correct terminology",
            body: "Misrecognized medical terms and numbers are highlighted.",
          },
          {
            title: "SOAP draft",
            body: "Content is arranged into SOAP and held for clinician review.",
          },
        ],
        safety: [
          "Always label output as a draft",
          "Surface missing information",
          "Check clinical content against the conversation",
          "Require review before record entry",
        ],
        cta: {
          explore: "Explore Scribe",
          open: "Open Scribe",
          pilot: "Pilot Scribe",
        },
      },
    },
    scribe: {
      brand: "CarePath Scribe",
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
      note: "In this simulation, every item is traceable to sample data; when using the tool, the clinician must still check the draft against the conversation.",
    },
    scribeTool: {
      title: "From visit recording to a SOAP note",
      helper: "AI Scribe",
      intro: "Upload a Vietnamese consultation recording. The system transcribes it, corrects medical terms, and drafts a SOAP note for clinician review.",
      preStartSteps: [
        "Record the visit",
        "AI turns speech into text",
        "AI creates a structured clinical note",
        "The clinician checks and edits before use",
      ],
      preStartReminder: "AI assists with drafting only. The clinician must review the content before use.",
      uploadNotice: "CarePath uses the recording file selected and uploaded by the clinic; this screen does not start the microphone.",
      continue: "Continue to notes",
      back: "All products",
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
    evidence: {
      title: "See how each product keeps review points in the right place.",
      body: "These screens use sanitized sample data. Research evidence links to CarePath's source report; there are no invented testimonials or outcome claims.",
      sampleLabel: "Sanitized sample data",
      researchLabel: "Research source",
      source: "Read the research report and cited sources",
      items: [
        {
          kind: "interpreter",
          product: "CarePath Interpreter",
          title: "A risky turn stays with the clinician.",
          body: "The simulation shows source text, translation, risk labels, and the confirmation action together.",
          detail: "Sample data: a penicillin allergy is flagged and has not been delivered to the patient.",
        },
        {
          kind: "scribe",
          product: "CarePath Scribe",
          title: "The draft exposes what still needs review.",
          body: "The sample screen keeps the raw transcript, corrected terms, and four SOAP sections in one review flow.",
          detail: "Sample data: Assessment remains marked as awaiting clinician review.",
        },
        {
          kind: "research",
          product: "Research basis",
          title: "Designed for visible confirmation.",
          body: "CarePath's report collects sources on recall of spoken medical information and errors in machine-translated discharge instructions.",
          detail: "Sources, limitations, and study context stay with the report instead of becoming detached marketing claims.",
        },
      ],
    },
    safety: {
      title: "One shared oversight layer. Two product-specific safety systems.",
      body: "CarePath does not replace clinician judgment. Each product stops output that requires confirmation at the review gate that belongs to its workflow.",
      trust: [
        {
          title: "Clinician review before use",
          body: "Drafts and content requiring confirmation never become treatment decisions automatically.",
        },
        {
          title: "Visible uncertainty",
          body: "Missing or uncertain output is clearly flagged.",
        },
        {
          title: "No replacement for diagnosis or advice",
          body: "CarePath supports the workflow; the clinician remains responsible for clinical decisions.",
        },
      ],
      shared: {
        title: "Shared CarePath oversight",
        body: "Four principles apply to both Interpreter and Scribe.",
        items: [
          {
            title: { vi: "Bác sĩ giữ quyền quyết định", en: "Clinician authority" },
            body: { vi: "Bác sĩ giữ quyền kiểm soát; lượt Interpreter nguy cơ cao và mọi bản nháp Scribe đều chờ bước xác nhận phù hợp.", en: "The clinician stays in control; high-risk Interpreter turns and every Scribe draft wait at the appropriate review gate." },
          },
          {
            title: { vi: "Thông báo AI rõ ràng", en: "Clear AI disclosure" },
            body: { vi: "Trạng thái mô phỏng, thí điểm và bản nháp luôn được gọi đúng tên.", en: "Simulation, pilot, and draft states are always named plainly." },
          },
          {
            title: { vi: "Độ không chắc chắn nhìn thấy được", en: "Visible uncertainty" },
            body: { vi: "Kết quả thiếu hoặc không chắc chắn không bị giao im lặng.", en: "Missing or uncertain output is never delivered silently." },
          },
          {
            title: { vi: "Giảm thiểu dữ liệu", en: "Data minimization" },
            body: { vi: "Chỉ xử lý dữ liệu cần cho lượt dịch hoặc bản nháp đang thực hiện.", en: "Only data needed for the active translation turn or draft is processed." },
          },
        ],
      },
      interpreter: {
        title: "Interpreter safety",
        body: "Risky content does not pass straight to the patient.",
        items: [
          {
            title: { vi: "Chặn nguy cơ cao", en: "High-risk blocking" },
            body: { vi: "Lượt nguy cơ cao và nghiêm trọng chờ bác sĩ xác nhận.", en: "High- and critical-risk turns wait for clinician confirmation." },
          },
          {
            title: { vi: "Cảnh báo độ tin cậy thấp", en: "Low-confidence warnings" },
            body: { vi: "Kết quả không chắc chắn luôn được gắn cờ rõ ràng.", en: "Uncertain output is always visibly flagged." },
          },
          {
            title: { vi: "Read-back hoặc chuyển người", en: "Read-back or human escalation" },
            body: { vi: "Bác sĩ xác nhận, chỉnh sửa hoặc yêu cầu phiên dịch viên.", en: "The clinician confirms, edits, or requests an interpreter." },
          },
          {
            title: { vi: "Thông báo sử dụng AI", en: "AI-use disclosure" },
            body: {
              vi: "Công cụ phiên dịch không lưu âm thanh; người dùng luôn được biết đây là AI và có thể yêu cầu con người hỗ trợ.",
              en: "The Interpreter stores no audio; users are told AI is involved and may request human support.",
            },
          },
        ],
      },
      scribe: {
        title: "Scribe safety",
        body: "A draft never becomes a medical record by itself.",
        items: [
          {
            title: { vi: "Trạng thái bản nháp", en: "Draft-only status" },
            body: { vi: "Mọi kết quả đều ghi rõ cần bác sĩ kiểm tra.", en: "Every result states that clinician review is required." },
          },
          {
            title: { vi: "Thông tin còn thiếu", en: "Missing information" },
            body: { vi: "Phần chưa có trong hội thoại được nêu ra thay vì tự điền.", en: "Details absent from the conversation are surfaced rather than invented." },
          },
          {
            title: { vi: "Đối chiếu với nội dung nguồn", en: "Check against source content" },
            body: { vi: "Mô hình được yêu cầu không tự thêm chẩn đoán, tư vấn hoặc thuốc; bác sĩ vẫn phải đối chiếu bản nháp với hội thoại.", en: "The model is instructed not to add diagnoses, advice, or medication; the clinician must still check the draft against the conversation." },
          },
          {
            title: { vi: "Duyệt trước hồ sơ", en: "Review before record entry" },
            body: { vi: "Bác sĩ kiểm tra trước khi bản nháp được đưa vào hồ sơ.", en: "A clinician checks the draft before it enters the record." },
          },
        ],
      },
    },
    pilot: {
      title: "Choose the product that fits your workflow.",
      body: "A pilot request can cover Interpreter, Scribe, or both. Scope and pricing follow a review of the real workflow; this page does not publish a placeholder quote.",
      transcriptNote: "For Interpreter interest, the current scenario and bilingual transcript travel with the request.",
    },
    footer: {
      promise: "AI assistance, clinician in control.",
      posture: "Designed around data minimization, awareness of Decree 13/PDP obligations, and §1557-aligned language-access positioning. This is not a legal certification claim.",
      honesty: "Interpreter is an interactive simulation; Scribe is a pilot draft tool. Both require healthcare-staff oversight.",
      contact: "Contact the pilot program",
    },
  },
};

export function copyFor(language: Language): PageCopy {
  return strings[language];
}
