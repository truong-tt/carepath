// Copy for the paperwork route at /dich-giay-to/.
//
// This route exists because the document reader had no front door: it was only
// reachable from inside a started live visit, so a clinician who wanted to
// translate a đơn thuốc had to open an interpreted consultation first. The copy
// below has to make the task, and only the task, obvious.
//
// Three rules it exists to hold:
//
// 1. Say what is held and why. A line the gate is holding is not "loading" and
//    not "failed" — it is withheld, deliberately, until the clinician confirms.
// 2. Never claim to be faster than it is. Translation runs one call per line at
//    roughly 13s/line on the live provider (see the measured note in
//    scribe/carepath/main.py), so a six-line prescription takes over a minute.
//    The waiting copy says so rather than letting the screen look broken.
// 3. The consent sentence is the visit screen's, verbatim. It is about
//    translation being fallible, the clinician staying responsible, and the
//    patient's right to a human interpreter — all true of paperwork. Changing
//    safety copy is hard-gated and is not this story's to do.

export const PAPERWORK = {
  navBack: "← Trang chủ",
  label: "Giấy tờ",
  title: "Dịch giấy tờ cho người bệnh",
  lede:
    "Chụp đơn thuốc, phiếu xét nghiệm hoặc giấy ra viện. CarePath dịch từng dòng và giữ lại dòng có liều thuốc cho tới khi bác sĩ xác nhận.",

  // Verbatim from VisitScreen. Do not reword here without a safety decision.
  consent:
    "Bệnh nhân đã được thông báo rằng CarePath là công cụ hỗ trợ dịch có thể sai, bác sĩ vẫn chịu trách nhiệm chuyên môn, và bệnh nhân có quyền yêu cầu phiên dịch viên.",
  consentCta: "Bắt đầu dịch giấy tờ",
  consentNote:
    "Không bật micro. Ảnh giấy tờ chỉ được xử lý trong bộ nhớ và không được lưu lại.",

  emptyTitle: "Chưa có giấy tờ nào",
  emptyBody: "Chụp hoặc tải ảnh để bắt đầu. Mỗi lần một tệp.",

  waiting: "Đang dịch từng dòng…",
  waitingSlow: "Bản dịch chạy từng dòng nên có thể mất hơn một phút.",
  elapsed: (seconds: number) => `Đã chờ ${seconds} giây`,

  sheetTitle: "Bản đưa cho người bệnh",
  sheetReady: (n: number) => `${n} dòng đã sẵn sàng đưa cho người bệnh.`,
  sheetEmpty: "Chưa có dòng nào được xác nhận.",
  sheetNote:
    "Chỉ những dòng bác sĩ đã xác nhận mới xuất hiện ở đây. Bác sĩ chịu trách nhiệm chuyên môn cho mọi nội dung.",

  heldMark: "Giữ lại",
  heldNote: "Chờ bác sĩ xác nhận",

  print: "In bản này",
  again: "Đọc giấy tờ khác",

  // Every failure names what happened and what to do next. None of them ever
  // falls back to a scripted sample: showing canned output for a document the
  // clinician actually uploaded would be a fabrication about the one thing this
  // product claims to do.
  errors: {
    start: "Không tạo được phiên. Kiểm tra kết nối rồi thử lại.",
    read: "Không đọc được giấy tờ. Chụp lại rõ hơn hoặc thử ảnh khác.",
    empty: "Không đọc được chữ nào. Chụp lại rõ hơn, đủ sáng và thẳng khung.",
    confirm: "Không lưu được xác nhận. Thử lại.",
  },

  offlineTitle: "Chưa đọc được giấy tờ",
  offlineBody:
    "Máy chủ chưa bật chế độ đọc giấy tờ, nên phần này đang tạm tắt. Chúng tôi không hiển thị kết quả dựng sẵn như thể đó là ảnh của bạn.",
  offlineCta: "Liên hệ xem trình diễn",
} as const;
