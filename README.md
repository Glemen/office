# Phòng Biên Tập & Soạn Thảo Văn Bản 3D (AI Document Studio)

Không gian văn phòng 3D **Agent Chibi** được dựng bằng Blender, tích hợp **4 chuyên viên văn bản AI** — chuyên soạn công văn, báo cáo, đề án, kế hoạch, rà soát thể thức và xuất thẳng ra **Microsoft Word (`.doc`)** hoặc **Markdown (`.md`)**.

## Cách chạy nhanh nhất (1 file `.exe` duy nhất — không cần cài Python hay Blender!)
1. Tải file **[`dist/PhongBienTap3D.exe`](dist/PhongBienTap3D.exe)** về máy Windows.
2. **Bấm đúp `PhongBienTap3D.exe`** (hoặc nếu máy có Antigravity, bảo Antigravity: *"chạy PhongBienTap3D.exe"* để tự kết nối **Antigravity Live** không cần API key).
3. Trình duyệt tự mở Phòng Biên Tập 3D. Nếu chạy độc lập ngoài Antigravity, bấm nút **Cài đặt AI** góc trên phải để dán **Google Gemini API Key** (miễn phí tại https://aistudio.google.com/apikey) hoặc trỏ sang **Ollama** nội bộ.

## 4 Chuyên viên trong phòng
| Bàn | Chuyên viên | Chuyên môn |
| :--- | :--- | :--- |
| **Bàn 1** | **Minh** | Nghiên cứu & Lập dàn ý, cấu trúc, luận điểm |
| **Bàn 2** | **Lan** | Chấp bút & Soạn thảo chính (công văn, báo cáo, đề án, thư từ...) |
| **Bàn 3** | **Tuấn** | Biên tập, hiệu đính văn phong & chuẩn thể thức (Nghị định 30), rà soát rủi ro |
| **Bàn 4** | **Vy** | Tổng hợp nhiều bản thảo, tóm tắt điều hành, bảng biểu & xuất bản |

## 3 Chế độ giao việc thông minh
1. **Tự chọn người giỏi nhất**: Nhập yêu cầu, hệ thống tự chọn đúng chuyên viên phù hợp nhất.
2. **Dự án lớn — Chia 3 bàn & Vy tổng hợp**: Minh, Lan, Tuấn làm song song 3 phần bổ trợ → Vy tự động tổng hợp thành **1 văn bản hoàn chỉnh duy nhất**.
3. **Chọn đích danh bàn**: Giao trực tiếp cho 1 chuyên viên bất kỳ.

## Lấy kết quả văn bản
- Bấm vào thông báo hoàn thành hoặc nút **Kho văn bản** góc trên phải → **Copy**, **Tải Word (`.doc`)** mở trực tiếp trong Microsoft Word, hoặc **Tải `.md`**.
- Toàn bộ file cũng được tự động lưu vào thư mục `results/` ngay cạnh file `PhongBienTap3D.exe`.
