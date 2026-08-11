# Phương — Nghiên cứu ngôn ngữ y khoa

## Mục tiêu

Phương trả lời câu hỏi: **AI có ghi đúng thuật ngữ, thuốc, liều, số, đơn vị và
phủ định trong hội thoại khám bệnh tiếng Việt hay không?**

## Công việc

| Tuần | Nhiệm vụ | Kết quả |
| --- | --- | --- |
| 1 | Học khái niệm AI y khoa và quy tắc an toàn | Giải thích 15 thuật ngữ bằng lời của mình |
| 2 | Đọc ViMedCSS, near-miss, DARAG, PiDA và SOAP | 5 phiếu nghiên cứu, mỗi phiếu tối đa 1 trang |
| 3 | Kiểm tra 50 thuật ngữ Việt–Anh có nguy cơ cao | Bảng thuật ngữ, loại rủi ro và câu ví dụ |
| 4 | Viết 30 hội thoại giả lập | Đủ thuốc/liều, số/đơn vị, phủ định, không chắc chắn và code-switching |
| 5 | Kiểm tra 20 SOAP và phân tích 10 lỗi pilot | Đánh dấu nguồn, mức độ, nguyên nhân và ca kiểm thử cần thêm |
| 6 | Viết kết luận và thuyết trình | Tóm tắt song ngữ và 5–7 slide |

## Tệp bàn giao

1. `paper-evidence-cards.md`
2. `medical-terms-review.csv`
3. `synthetic-safety-cases.jsonl`
4. `soap-grounding-review.csv`
5. `final-bilingual-summary.md`

Mỗi phiếu bài báo gồm: câu hỏi, dữ liệu, phương pháp, kết quả chính, giới hạn và
một giả thuyết có thể kiểm tra cho CarePath.

## Quy tắc an toàn

- Chỉ dùng bài báo, dữ liệu công khai đã được duyệt và ca hoàn toàn giả lập.
- Không dùng hoặc kể lại ca bệnh thật, kể cả từ bố mẹ.
- Bố mẹ có thể góp ý tối đa 10 ca giả lập; đây không phải kiểm định lâm sàng.
- Không đưa ra chẩn đoán hoặc hướng dẫn thuốc cho người thật.
- Không nhận secret, chạy GPU trả phí hoặc đăng dữ liệu/mô hình.

## Hoàn thành khi

- Có đủ 5 sản phẩm; tiếng Việt đúng dấu và UTF-8/NFC.
- 30 ca phủ đủ các nhóm rủi ro; 20 SOAP có câu nguồn được kiểm tra.
- Không có dữ liệu bệnh nhân hoặc tuyên bố “sẵn sàng dùng lâm sàng”.
