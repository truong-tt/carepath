# Kiên — Kỹ thuật AI và đánh giá mô hình

## Mục tiêu

Kiên trả lời câu hỏi: **PhoWhisper LoRA hoặc GEC có giảm lỗi thuật ngữ y khoa
khó so với Gipformer mà không làm hỏng thuốc, số, đơn vị hoặc tốc độ không?**

## Công việc

| Tuần | Nhiệm vụ | Kết quả |
| --- | --- | --- |
| 1 | Học Git/Python, vẽ pipeline và chạy toàn bộ `smoke` | Branch riêng, sơ đồ và bằng chứng command/artifact |
| 2 | Kiểm tra manifest rồi chạy baseline ASR | Bảng revision/split/hash và các metric nền |
| 3 | Chạy PhoWhisper-small LoRA `pilot` | Seed 13, ≤1.000 train rows, 200 step, checkpoint trên Drive |
| 4 | Phân loại ít nhất 20 lỗi và áp dụng gate | Quyết định pass/fail theo tiêu chí có trước |
| 5 | Nếu có lý do: GEC pilot; nếu không: cải tiến metric/test nhỏ | Một pull request tập trung, không thêm dependency |
| 6 | Kiểm tra staging bundle và viết báo cáo | Xác nhận adapter thật được load, không silent fallback |

## Tệp bàn giao

1. `environment-and-smoke-proof.md`
2. `dataset-governance-notes.md`
3. `asr-baseline-report.md`
4. `asr-pilot-run-log.md`
5. `asr-error-analysis.csv`
6. Một pull request nhỏ có test
7. `final-technical-report.md`

Metric bắt buộc: overall/hard WER, medical-term error/recall, number-unit
preservation, real-time factor và peak VRAM. Code-switch proxy không được gọi là
PIER thật.

## Quy tắc an toàn và kỹ thuật

- `train` mới được học; `validation`, `test`, `hard` và VietMed test chỉ để đánh giá.
- Audio công khai chỉ ở cache `/content`, không lưu Drive; không dùng dữ liệu bệnh nhân.
- Không dùng token của người hướng dẫn hoặc đưa token vào code/output.
- Không chạy near-miss chưa triển khai; không stack ASR LoRA + GEC trước khi từng phần pass.
- Không tự bật paid profile, upload model, mở tunnel hoặc sửa production.
- Kiên hỗ trợ Sơn tối đa 30 phút/tuần nhưng không làm hộ nhật ký hoặc đánh giá.

## Hoàn thành khi

- Có bằng chứng smoke và một ASR pilot hoặc blocker Colab rõ ràng.
- Manifest/split được giải thích đúng; ít nhất 20 lỗi được phân tích.
- Pull request nhỏ có kiểm tra đạt.
- Báo cáo không dùng kết quả mock để tuyên bố model thật hoặc clinical readiness.
