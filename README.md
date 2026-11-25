# Phòng Biên Tập & Soạn Thảo Văn Bản 3D — Chuẩn Nghị định 30/2020/NĐ-CP

Không gian văn phòng 3D **Agent Chibi** được dựng bằng Blender, tích hợp **4 chuyên viên văn bản AI** (mặc định dùng model **Pro / Neon Medium**) — chuyên soạn thảo, rà soát, tổng hợp văn bản hành chính và xuất thẳng ra **Microsoft Word (`.docx` thật)** hoặc **In / Lưu PDF khổ A4** đúng chuẩn **Nghị định 30/2020/NĐ-CP**.

## Chạy ngay bằng 1 file `.exe` duy nhất (Không cần cài Python hay Blender)
1. Tải file **[`dist/PhongBienTap3D.exe`](dist/PhongBienTap3D.exe)** về máy Windows.
2. **Nếu máy có Antigravity**: Mở thư mục chứa file trong Antigravity và nhắn *"chạy `PhongBienTap3D.exe`"* → tự kết nối **Antigravity Pro** không cần API key.
3. **Nếu bấm đúp trực tiếp `PhongBienTap3D.exe` ngoài Desktop**: Trình duyệt tự mở; vào nút **Cài đặt** góc trên phải để dán **Google Gemini API Key** hoặc kết nối **Ollama** nội bộ.

## Tính năng nổi bật (Bản Chốt Đơn)
- **Chuẩn Nghị định 30/2020/NĐ-CP 100%**: Khổ A4, lề Trên 20mm / Dưới 20mm / Trái 30mm / Phải 15mm, phông Times New Roman, bảng tiêu đề 2 cột có đường kẻ liền nét thật, đánh số trang canh giữa lề trên (ẩn trang 1), nội dung 14pt lùi đầu dòng 1.27cm, kết thúc `./.`, bảng Nơi nhận & Chữ ký chuẩn.
- **Lưu sẵn Hồ sơ Đơn vị**: Khai báo 1 lần Tên cơ quan chủ quản, Đơn vị ban hành, Chữ viết tắt, Địa danh, Chức vụ & Người ký trong mục **Cài đặt**.
- **Gửi Hình Ảnh như chat AI thực thụ**: Bấm nút **Ảnh**, kéo thả, hoặc bấm **`Ctrl+V` dán thẳng ảnh chụp màn hình / ảnh chụp công văn giấy / bảng biểu** vào ô chat để chuyên viên đọc ảnh và soạn nội dung theo yêu cầu.
- **Chế độ Thư mục làm việc (ngang chức nghiệp Antigravity)**: Bấm nút **Thư mục** trên ô chat để chọn bất kỳ thư mục nào trên máy — chuyên viên AI sẽ đọc tài liệu, tạo/sửa file/code và tự xuất văn bản `.docx` trực tiếp ngay bên trong thư mục đó (không đụng tới thư mục ngoài).
- **Đính kèm tài liệu gốc (`.docx`, `.txt`, `.md`)**: Tải văn bản thô có sẵn lên để giao chuyên viên hiệu đính thể thức NĐ30, tóm tắt hoặc chuyển thể thành Báo cáo/Tờ trình.
- **Chỉnh sửa nhanh ngay trên Web**: Sửa trực tiếp Số ký hiệu, Trích yếu, Nội dung, Nơi nhận... và bấm **Lưu** để cập nhật lại ngay file `.docx` & bản in PDF.
- **3 chế độ điều phối**: *Tự chọn người giỏi nhất* • *Dự án lớn: Chia 3 bàn & Vy tổng hợp* • *Chọn đích danh bàn*.
