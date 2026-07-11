export type Language = "vi" | "en";

const languageStorageKey = "carepath-demo-language";

export const copy = {
  vi: {
    title: "CarePath | Phiên dịch khám bệnh trực tiếp",
    breadcrumb: "Đường dẫn sản phẩm",
    status: "Bản mô phỏng tương tác",
    allProducts: "Tất cả chức năng",
    language: "Ngôn ngữ thanh sản phẩm",
    productName: "Phiên dịch khám bệnh trực tiếp",
    consent: {
      eyebrow: "Phiên dịch khám bệnh trực tiếp",
      heading: "Phiên dịch khám bệnh trực tiếp",
      description: "Dịch hai chiều giữa bác sĩ tiếng Việt và bệnh nhân tiếng Anh trong lúc khám.",
      steps: "Cách phiên dịch diễn ra",
      doctorSpeaks: "Bác sĩ nói tiếng Việt",
      aiToPatient: "AI dịch sang tiếng Anh cho bệnh nhân",
      patientSpeaks: "Bệnh nhân trả lời bằng tiếng Anh",
      aiToDoctor: "AI dịch lại sang tiếng Việt cho bác sĩ",
      limitation: "CarePath chỉ hỗ trợ phiên dịch, không đưa ra chẩn đoán hoặc tư vấn điều trị.",
      acknowledgements: "Xác nhận trước khi bắt đầu",
      aiDisclosure:
        "Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi và cần được bác sĩ kiểm tra trước khi sử dụng.",
      interpreterRight:
        "Tôi đã được giải thích rằng có thể yêu cầu thông dịch viên trực tiếp bất cứ lúc nào.",
      start: "Bắt đầu phiên dịch",
      starting: "Đang bắt đầu…",
      retry: "Thử lại để bắt đầu phiên dịch",
      startError: "Không thể bắt đầu phiên dịch. Vui lòng kiểm tra kết nối máy chủ và thử lại.",
    },
  },
  en: {
    title: "CarePath | Medical Interpreter",
    breadcrumb: "Product breadcrumb",
    status: "Interactive mock simulation",
    allProducts: "All products",
    language: "Product bar language",
    productName: "Medical Interpreter",
    consent: {
      eyebrow: "Medical Interpreter",
      heading: "Live medical interpretation",
      description: "Two-way interpretation between a Vietnamese-speaking clinician and an English-speaking patient during a visit.",
      steps: "How interpretation works",
      doctorSpeaks: "The clinician speaks Vietnamese",
      aiToPatient: "AI translates to English for the patient",
      patientSpeaks: "The patient replies in English",
      aiToDoctor: "AI translates back to Vietnamese for the clinician",
      limitation: "CarePath provides translation support only; it does not provide diagnoses or treatment advice.",
      acknowledgements: "Confirm before starting",
      aiDisclosure:
        "I have been told that AI-generated translations can contain errors and must be reviewed by the clinician before use.",
      interpreterRight:
        "I have been told that a human interpreter can be requested at any time.",
      start: "Start interpreting",
      starting: "Starting…",
      retry: "Try starting interpretation again",
      startError: "Unable to start interpretation. Check the server connection and try again.",
    },
  },
} as const;

export function initialLanguage(): Language {
  const value = new URLSearchParams(window.location.search).get("lang");
  if (value !== null) {
    return value === "en" || value === "vi" ? value : "vi";
  }
  return localStorage.getItem(languageStorageKey) === "en" ? "en" : "vi";
}

export function persistLanguage(language: Language) {
  localStorage.setItem(languageStorageKey, language);
}
