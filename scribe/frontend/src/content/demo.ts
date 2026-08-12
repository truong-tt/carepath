// Copy for the public demo hub at /thu-nghiem/.
//
// Kept honest on purpose. Two rules this file exists to hold:
//
// 1. A scripted sample is labelled a scripted sample. `demo` provider mode
//    never looks at the uploaded bytes, so calling its output "your document"
//    would be a fabrication about the one thing this product claims to do.
// 2. Nothing here promises a capability the backend is not currently serving.
//    The hub reads provider_mode from /api/health and says what is actually
//    available rather than failing at the moment the visitor tries.

export const DEMO = {
  navBack: "← Trang chủ",
  label: "Thử trực tiếp",
  title: "Thử CarePath ngay trên trình duyệt",
  lede:
    "Ba chức năng, chạy qua đúng bộ máy mà phòng khám dùng: cùng bộ luật lâm sàng, cùng bước giữ lại phần rủi ro, cùng bước bác sĩ xác nhận. Không cần tài khoản, không cần cài đặt.",

  limitsTitle: "Giới hạn của bản thử",
  limits: [
    "5 lượt mỗi ngày cho mỗi người truy cập.",
    "Ảnh tối đa 4 MB, mỗi lần một tệp.",
    "Không lưu ảnh, không lưu âm thanh, không lưu lời chép.",
    "Kết quả chỉ để xem thử, không dùng cho chẩn đoán hay điều trị.",
  ],
  remaining: (n: number) => `Còn ${n} lượt hôm nay`,

  panels: {
    prescription: {
      label: "Đơn thuốc",
      title: "Ảnh đơn thuốc tiếng Việt → bản song ngữ",
      body: "Đọc chữ trên đơn, dịch từng dòng, và giữ lại dòng có liều thuốc hoặc tên thuốc dễ nhầm cho tới khi bác sĩ xác nhận.",
      sampleCta: "Xem ví dụ dựng sẵn",
      uploadCta: "Tải ảnh đơn thuốc của bạn",
      uploadHint: "JPG, PNG, WEBP hoặc HEIC. Tối đa 4 MB.",
    },
    discharge: {
      label: "Giấy ra viện",
      title: "Giấy ra viện → bản tiếng Anh cho người bệnh",
      body: "Lúc ra viện là một trong ba thời điểm y văn ghi nhận dễ gây hại nhất cho người bệnh không thạo ngôn ngữ. Tải ảnh giấy ra viện hoặc phiếu xét nghiệm để xem CarePath xử lý thế nào.",
      uploadCta: "Tải ảnh giấy ra viện",
      uploadHint: "JPG, PNG, WEBP hoặc HEIC. Tối đa 4 MB.",
    },
    conversation: {
      label: "Khám hai chiều",
      title: "Câu hội thoại → dịch có kiểm soát rủi ro",
      body: "Gõ một câu bác sĩ nói với người bệnh, hoặc chọn một câu có sẵn. Câu chứa liều thuốc sẽ bị giữ lại thay vì đến thẳng người bệnh.",
      inputLabel: "Bác sĩ nói (tiếng Việt)",
      placeholder: "Ví dụ: Uống 1 viên Amoxicillin 500 mg, ngày 2 lần, sau ăn",
      send: "Dịch câu này",
      presetsLabel: "Hoặc thử một câu có sẵn",
      presets: [
        "Uống 1 viên Amoxicillin 500 mg, ngày 2 lần, sau ăn",
        "Nhỏ mắt trái 2 giọt, ngày 3 lần",
        "Anh hãy nghỉ ngơi và quay lại khám vào tuần sau",
        "Không uống rượu trong thời gian dùng thuốc",
      ],
    },
  },

  sampleBadge: "Ví dụ dựng sẵn",
  sampleNote:
    "Đây là đơn thuốc mẫu, không phải ảnh bạn tải lên. Bước nhận diện rủi ro và bước bác sĩ xác nhận vẫn chạy thật.",
  liveBadge: "Đọc từ ảnh bạn tải lên",

  gated: "Chờ bác sĩ xác nhận",
  gatedNote: "Người bệnh chưa nhìn thấy và chưa nghe thấy dòng này.",
  delivered: "Đã gửi tới người bệnh",
  showDoctorView: "Xem như bác sĩ",
  hideDoctorView: "Xem như người bệnh",
  doctorViewNote:
    "Bác sĩ thấy đầy đủ cả hai ngôn ngữ để đối chiếu. Người bệnh chỉ thấy dòng đã được xác nhận.",

  resultDisclaimer: "Kết quả demo — không dùng cho lâm sàng.",
  sourceColumn: "Tiếng Việt trên giấy",
  targetColumn: "Bản tiếng Anh cho người bệnh",

  waiting: {
    sample: "Đang chạy ví dụ…",
    upload: "Đang đọc giấy tờ…",
    uploadSlow:
      "Đọc giấy tờ thật mất khoảng 10–15 giây mỗi dòng, nên một đơn thuốc đầy đủ có thể mất hơn một phút. Đừng đóng trang.",
    elapsed: (s: number) => `Đã chờ ${s} giây`,
  },

  errors: {
    quota: "Bạn đã dùng hết lượt thử hôm nay. Mời quay lại vào ngày mai.",
    tooLarge: "Ảnh quá lớn. Chọn ảnh dưới 4 MB.",
    notImage: "Hãy chọn một tệp ảnh.",
    unreadable: "Không đọc được giấy tờ này. Thử chụp rõ hơn, đủ sáng và thẳng góc.",
    upstream: "Máy chủ đang bận hoặc vừa khởi động lại. Thử lại sau ít phút.",
    empty: "Không tìm thấy dòng chữ nào trên ảnh.",
    retry: "Thử lại",
  },

  capability: {
    checking: "Đang kiểm tra máy chủ…",
    sampleOnly: {
      title: "Hiện chỉ chạy được ví dụ dựng sẵn",
      body: "Máy chủ đang ở chế độ trình diễn nên chưa đọc được ảnh bạn tải lên. Ví dụ dựng sẵn vẫn chạy qua đầy đủ bộ luật rủi ro và bước xác nhận.",
    },
    // A panel with no runnable action must say why, not sit there empty.
    uploadUnavailable:
      "Phần tải ảnh của bạn đang tạm tắt vì máy chủ chưa bật chế độ đọc giấy tờ. Chúng tôi không hiển thị kết quả dựng sẵn như thể đó là ảnh của bạn.",
    offline: {
      title: "Bản thử đang tạm dừng",
      body: "Máy chủ chưa bật chế độ đọc giấy tờ, nên phần thử trực tiếp sẽ hiển thị sai nếu vẫn chạy. Chúng tôi không hiển thị kết quả giả. Mời liên hệ để được xem bản trình diễn trực tiếp.",
      cta: "Liên hệ xem trình diễn",
    },
  },
} as const;
