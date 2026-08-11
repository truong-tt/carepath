# Sơn — Tham gia huấn luyện AI y khoa

## Sơn sẽ tham gia training như thế nào?

Sơn không phải tự viết mô hình. Sơn sẽ:

1. Kiểm tra dữ liệu trước huấn luyện.
2. Chạy pipeline `smoke` không tốn GPU.
3. Cùng người hướng dẫn chạy **một SOAP QLoRA pilot** trên Colab.
4. Ghi step, loss, checkpoint, thời gian, GPU và lỗi.
5. So sánh đầu ra trước–sau và áp dụng cổng an toàn.

## Công việc

| Tuần | Nhiệm vụ | Kết quả |
| --- | --- | --- |
| 1 | Học Colab, an toàn dữ liệu và 20 khái niệm AI | Bảng thuật ngữ do Sơn tự giải thích |
| 2 | Chạy SOAP `smoke` và kiểm tra 20 ví dụ giả lập | Nhật ký run và quyết định chấp nhận/loại dữ liệu |
| 3 | Tập đọc step, loss, checkpoint và safety gate | Bảng phân biệt “run xong” với “model đạt” |
| 4 | Chạy SOAP QLoRA `pilot` có giám sát | Nhật ký profile `pilot`, seed 13, ≤500 ví dụ, 200 step |
| 5 | So sánh CKey, Qwen nền và adapter trên 20 ca | Lỗi thiếu, bịa, đổi số/phủ định và kết luận gate |
| 6 | Xem bundle, viết phản ánh và thuyết trình | “Tôi đã làm gì trong quá trình huấn luyện AI?” |

## Tệp bàn giao

1. `ai-training-glossary.md`
2. `soap-data-safety-checklist.csv`
3. `smoke-run-log.md`
4. `soap-pilot-run-log.md`
5. `before-after-review.csv`
6. `final-medical-ai-reflection.md`

## Quy tắc an toàn

- Chỉ dùng dữ liệu công khai đã duyệt hoặc dữ liệu giả lập; không dùng bệnh nhân thật.
- Người hướng dẫn nhập secret, xác nhận chi phí và bật paid profile.
- Sơn không đổi model, seed, số step, dữ liệu hoặc bộ lọc an toàn.
- Khi hash sai, thiếu GPU, lộ secret hoặc không lưu được checkpoint: dừng và báo.
- Không upload model, tạo endpoint hoặc gọi đầu ra là lời khuyên y khoa.

## Hoàn thành khi

- Sơn tự chạy được `smoke` và trực tiếp tham gia một pilot có giám sát.
- Nhật ký đủ cấu hình, checkpoint, thời gian và lỗi.
- 20 ví dụ training và 20 đầu ra đều được kiểm tra có nguồn.
- Sơn giải thích được: **đã train không đồng nghĩa được dùng cho bệnh nhân**.
