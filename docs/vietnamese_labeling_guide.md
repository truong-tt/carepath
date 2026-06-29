# Hướng dẫn gắn nhãn audio y khoa (Whisper + Label Studio)

Tài liệu này dành cho người chưa từng lập trình và máy tính chưa cài gì sẵn (chưa có Python, Whisper hay Label Studio). Bạn chỉ cần biết mở thư mục, bấm đúp chuột (double-click) và copy/paste.

Công việc gồm ba bước:

1. Whisper nghe audio và tạo bản chép lời nháp (có thể sai).
2. Bạn nghe lại và sửa bản nháp thành bản đúng.
3. Xuất một file kết quả để nhóm kỹ thuật dùng.

Mục tiêu là bổ sung dữ liệu cho bộ dữ liệu ViMedCSS.

## Từ ngữ cần biết

| Từ | Nghĩa |
|---|---|
| Audio | File ghi âm (`.wav`, `.mp3`, `.m4a`, ...) |
| Transcript | Bản chép lời từ audio ra chữ |
| Python | Phần mềm nền để chạy Whisper và Label Studio |
| Whisper | Phần mềm AI nghe audio và tạo bản nháp |
| Label Studio | Trang web chạy trên máy của bạn để nghe audio và sửa |
| Task | Một file audio cần xử lý |
| Import | Đưa dữ liệu vào Label Studio |
| Export | Lấy kết quả ra khỏi Label Studio |

Lưu ý: mỗi khi bấm một file `.cmd`, một cửa sổ đen sẽ hiện ra. Đây là điều bình thường, không phải lỗi. Chỉ cần chú ý khi thấy chữ "error" hoặc "failed"; khi đó hãy chụp màn hình và hỏi người phụ trách kỹ thuật.

## Cần chuẩn bị

- Máy Windows.
- Kết nối internet (để tải Python, Whisper và Label Studio).
- Khoảng 5 GB dung lượng trống.
- Trình duyệt. Windows có sẵn Microsoft Edge, không cần cài thêm.

## Phần A. Cài đặt lần đầu trên máy trống

Phần này chỉ làm một lần. Làm lần lượt A1, A2, A3.

### A1. Cài Python 3.12

Whisper và Label Studio cần Python để chạy. Nếu máy chưa có thì cài trước.

1. Mở trình duyệt, vào địa chỉ:

   ```text
   https://www.python.org/downloads/windows/
   ```

2. Tìm mục Python 3.12, tải bản "Windows installer (64-bit)".
3. Mở file vừa tải về.
4. Ở màn hình đầu tiên của trình cài đặt, tick vào ô **Add python.exe to PATH** (nằm ở phía dưới). Bước này rất quan trọng.
5. Bấm **Install Now** và chờ cài xong.
6. Bấm **Close** để đóng.

### A2. Tải dự án CarePath về máy

Bạn cần thư mục dự án nằm trên máy. Hỏi người phụ trách kỹ thuật để nhận file `carepath.zip` (hoặc link tải). Không tải dự án từ nguồn lạ.

1. Tải file `carepath.zip` về.
2. Bấm chuột phải vào file, chọn **Extract All**.
3. Chọn nơi giải nén sao cho kết quả là thư mục:

   ```text
   C:\Users\ADMIN\carepath
   ```

4. Mở thư mục đó và kiểm tra có các thư mục con như `docs`, `scripts`, `data`.

Lưu ý về đường dẫn: tài liệu này dùng `C:\Users\ADMIN\carepath` làm ví dụ. Nếu tên người dùng Windows của bạn không phải `ADMIN`, đường dẫn sẽ bắt đầu bằng tên của bạn, ví dụ `C:\Users\Lan\carepath`. Các bước vẫn giống hệt, chỉ thay phần đầu đường dẫn cho đúng.

### A3. Cài Whisper và Label Studio

1. Mở File Explorer, dán đường dẫn sau vào thanh địa chỉ và bấm Enter:

   ```text
   C:\Users\ADMIN\carepath\scripts\labeling
   ```

   Bạn sẽ thấy năm file:

   ```text
   setup_labeling.cmd
   transcribe_audio.cmd
   start_audio_server.cmd
   start_label_studio.cmd
   export_labels.cmd
   ```

2. Bấm đúp `setup_labeling.cmd`. File này tự tạo môi trường riêng và tải Whisper, Label Studio về máy. Bạn không cần gõ gì. Việc này cần internet và mất vài phút.
3. Khi xong, cửa sổ hiện dòng:

   ```text
   Done. You can close this window.
   ```

   Bấm một phím để đóng.

Nếu cửa sổ báo `py is not recognized`, nghĩa là bước A1 chưa xong hoặc chưa tick "Add python.exe to PATH". Cài lại Python theo A1 (nhớ tick ô đó), rồi bấm lại `setup_labeling.cmd`.

Sau khi A1, A2, A3 xong, máy đã sẵn sàng. Lần sau làm việc, bạn vào thẳng Phần B.

## Phần B. Mỗi buổi làm việc

Làm theo đúng thứ tự sau.

### Bước 1. Chép audio vào thư mục

Mở thư mục:

```text
C:\Users\ADMIN\carepath\data\labeling\audio
```

Chép các file audio cần xử lý vào đây. Định dạng nhận: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.opus`, `.webm`, `.aac`.

Đặt tên file đơn giản, không dấu tiếng Việt, ví dụ `bn001.wav`. Tên có dấu dễ gây lỗi.

### Bước 2. Chạy Whisper

Bấm đúp `transcribe_audio.cmd`. Whisper sẽ nghe toàn bộ audio trong thư mục trên.

Lần đầu chạy sẽ lâu (khoảng 5 đến 15 phút) vì máy phải tải mô hình Whisper về (khoảng 1,5 GB). Đây là lần tải khác với bước A3. Những lần sau nhanh hơn. Cứ để cửa sổ chạy, không tắt.

Khi xong, máy tạo file `label_studio_tasks.json`. Bạn không cần mở file này.

Nếu thấy dòng `No audio files found`, nghĩa là chưa có audio trong thư mục ở Bước 1.

### Bước 3. Mở audio server và giữ cửa sổ mở

Label Studio cần audio server để phát ghi âm. Bấm đúp `start_audio_server.cmd`.

Cửa sổ này phải giữ mở trong suốt buổi làm việc. Nếu tắt, audio sẽ không phát được.

Để kiểm tra, mở trình duyệt và vào `http://127.0.0.1:8765/`. Nếu thấy danh sách file audio là đúng.

Nếu cửa sổ báo `address already in use`, nghĩa là đã có một audio server cũ đang chạy. Hãy đóng các cửa sổ audio server cũ, rồi bấm lại `start_audio_server.cmd` một lần.

### Bước 4. Mở Label Studio

Bấm đúp `start_label_studio.cmd`. Sau một lúc, trình duyệt mở trang `http://localhost:8080`. Nếu không tự mở, dán địa chỉ đó vào trình duyệt.

### Bước 5. Thiết lập trong trình duyệt

Lần đầu tiên, làm ba việc sau (chỉ làm một lần):

1. Tạo tài khoản. Đây là tài khoản chỉ nằm trên máy này, không phải tài khoản Google. Nhập email bất kỳ và mật khẩu, bấm Create Account.
2. Tạo project. Bấm Create Project, đặt tên ví dụ `CarePath Audio Labeling`.
3. Dán cấu hình giao diện:
   - Vào Settings > Labeling Interface, chọn chế độ Code.
   - Mở file `C:\Users\ADMIN\carepath\docs\label_studio_transcription_config.xml` bằng Notepad.
   - Bôi đen toàn bộ (Ctrl+A), copy (Ctrl+C), dán vào ô Code, bấm Save.

Nếu Label Studio báo lỗi XML, thường do copy thiếu hoặc thừa. Mở lại file, copy lại toàn bộ từ dòng `<View>` đến `</View>`, rồi dán lại.

Mỗi buổi sau, chỉ cần mở đúng project đã tạo.

### Bước 6. Import task

Trong project, bấm Import và chọn file:

```text
C:\Users\ADMIN\carepath\data\labeling\label_studio_tasks.json
```

Sau khi import, bạn thấy danh sách task, mỗi task là một file audio.

Nếu bấm nút phát mà không nghe gì, kiểm tra cửa sổ audio server (Bước 3) còn mở không, rồi bấm F5 để tải lại trang.

### Bước 7. Gắn nhãn từng task

Mở một task. Bạn sẽ thấy thanh phát audio, bản nháp Whisper, ô chọn chất lượng và ô sửa.

Làm theo thứ tự:

1. Bấm phát, nghe hết một lần.
2. Đọc bản nháp Whisper.
3. Nghe lại từng đoạn ngắn.
4. Sửa ô chữ thành bản đúng.
5. Chọn chất lượng.
6. Bấm Submit.

Không bấm Submit khi chưa nghe lại ít nhất một lần. Whisper có thể nghe nhầm, thậm chí tạo ra câu không có trong audio, nên tai của bạn là người quyết định.

### Bước 8. Xuất kết quả

1. Trong project, bấm Export, chọn định dạng JSON, tải file về.
2. Lưu file đúng tên sau (phải đúng tên, nếu sai thì bước tiếp theo không tìm thấy):

   ```text
   C:\Users\ADMIN\carepath\data\labeling\label_studio_export.json
   ```

3. Quay lại thư mục `scripts\labeling`, bấm đúp `export_labels.cmd`.

Kết quả cuối nằm ở:

```text
C:\Users\ADMIN\carepath\data\labeling\training_transcripts.jsonl
```

Gửi file này cho nhóm kỹ thuật.

## Phần C. Quy tắc gắn nhãn

### Chọn chất lượng

| Giá trị | Khi nào chọn |
|---|---|
| OK | Audio rõ, bạn tự tin phần lớn bản ghi đúng |
| Khó nghe | Có tạp âm hoặc người nói nhỏ, vài chỗ không chắc, nhưng vẫn sửa được phần lớn |
| Bỏ qua | Gần như không nghe được, sai file, hoặc mất tiếng quá nhiều |

Dữ liệu tốt nhất là loại OK. Loại Khó nghe cần người khác kiểm tra lại. Loại Bỏ qua thường không dùng.

### Quy tắc sửa transcript

Nguyên tắc chính: chép đúng những gì nghe được. Không thêm, không suy đoán, không tóm tắt.

Nên làm:

- Sửa chính tả và thêm dấu tiếng Việt đầy đủ.
- Thêm dấu câu vừa phải cho dễ đọc.
- Giữ đúng số, đơn vị, liều lượng, thời gian.
- Giữ đúng tên thuốc, bệnh, triệu chứng nếu nghe được.

Không nên làm:

- Không thêm thông tin không có trong audio.
- Không tự suy ra chẩn đoán mà người nói không nói.
- Không dịch toàn bộ tiếng Việt sang tiếng Anh.

Ví dụ đúng:

```text
Whisper nháp:  bệnh nhân đau ngực spo hai chín mươi tám phần trăm
Bản đúng:      bệnh nhân đau ngực, SpO2 98%.
```

Ví dụ sai:

```text
Audio nói:            bệnh nhân đau bụng vùng thượng vị
Không được sửa thành: bệnh nhân có khả năng viêm loét dạ dày
```

Lý do: "viêm loét dạ dày" là suy luận thêm, không phải nội dung nghe được.

#### Số và đơn vị

Nghe số đọc bằng lời thì viết lại dạng gọn:

```text
ba mươi bảy phẩy tám độ C              -> 37,8 độ C
chín mươi tám phần trăm                -> 98%
spo hai                                -> SpO2
huyết áp một trăm hai mươi trên tám mươi -> huyết áp 120/80
paracetamol năm trăm mi li gam         -> paracetamol 500 mg
```

#### Khi không chắc một tên thuốc hoặc từ khó

Nghe lại vài lần và dựa vào kiến thức y khoa. Nếu vẫn không chắc, ghi `[không rõ]` tại vị trí đó:

```text
Bệnh nhân đang dùng [không rõ] 500 mg mỗi ngày.
```

Không đoán bừa tên thuốc, vì sai tên thuốc nguy hiểm về y khoa và làm hỏng dữ liệu.

#### Tiếng Anh và nhiều người nói

Giữ nguyên thuật ngữ tiếng Anh khi người nói dùng tiếng Anh, ví dụ `COPD`, `SpO2`, `salbutamol`. Không dịch sang tiếng Việt.

Nếu có nhiều người nói và phân biệt được vai trò, có thể ghi `Bác sĩ:` hoặc `Bệnh nhân:` trước câu. Nếu không rõ, chỉ cần chép liền mạch.

## Phần D. Tham khảo nhanh

### Checklist trước khi báo hoàn thành

- Đã cài Python, đã chạy `setup_labeling.cmd` thành công (chỉ cần một lần).
- Đã chép audio vào `data\labeling\audio`.
- Đã chạy `transcribe_audio.cmd`.
- Cửa sổ `start_audio_server.cmd` vẫn mở trong lúc làm.
- Đã mở Label Studio và đăng nhập.
- Đã import `label_studio_tasks.json`.
- Đã nghe lại và Submit tất cả task.
- Đã export và lưu đúng tên `label_studio_export.json`.
- Đã chạy `export_labels.cmd`.
- Đã có file `training_transcripts.jsonl`.

### Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `py is not recognized` | Cài lại Python 3.12, nhớ tick "Add python.exe to PATH", rồi chạy lại `setup_labeling.cmd` |
| Không mở được Label Studio | Bấm lại `start_label_studio.cmd`, đợi, rồi mở `http://localhost:8080` |
| Bấm phát không nghe gì | Kiểm tra cửa sổ audio server còn mở không, rồi bấm F5 |
| Báo `address already in use` | Đóng các cửa sổ audio server cũ, rồi mở lại một lần |
| Whisper chạy lâu | Bình thường, nhất là lần đầu. Cứ chờ, không tắt |
| Lỡ đóng audio server | Mở lại `start_audio_server.cmd`, rồi bấm F5 |
| Lỡ Submit, muốn sửa | Mở lại task đó, sửa rồi lưu. Không chắc thì ghi tên audio và hỏi |
| Không biết một từ y khoa | Nghe lại; vẫn không chắc thì ghi `[không rõ]` |
| Có chữ đỏ hoặc "failed" | Chụp màn hình và gửi người phụ trách kỹ thuật |

### Tóm tắt

```text
Cài đặt một lần:
A1. Cài Python 3.12 (tick "Add python.exe to PATH")
A2. Giải nén carepath.zip thành C:\Users\ADMIN\carepath
A3. Chạy setup_labeling.cmd

Mỗi buổi làm việc:
1. Chép audio vào data\labeling\audio
2. Chạy transcribe_audio.cmd
3. Chạy start_audio_server.cmd và giữ cửa sổ mở
4. Chạy start_label_studio.cmd
5. Import label_studio_tasks.json
6. Nghe, sửa transcript, bấm Submit
7. Export JSON
8. Lưu thành label_studio_export.json
9. Chạy export_labels.cmd
10. Gửi training_transcripts.jsonl cho nhóm kỹ thuật
```
