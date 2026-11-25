# Phòng Biên Tập & Soạn Thảo Văn Bản 3D (AI Document Studio)

Không gian văn phòng 3D chạy trực tiếp trên trình duyệt, gồm **4 chuyên viên văn bản AI** làm việc quanh bàn biên tập gỗ óc chó — chuyên soạn công văn, báo cáo, đề án, kế hoạch, hiệu đính thể thức và xuất thẳng ra **Microsoft Word (`.doc`)** hoặc **Markdown (`.md`)**.

> **Gọn nhẹ — mang sang máy nào cũng chạy được:** Không cần `pip install`, chỉ cần **Python 3.8+** có sẵn trên máy.

## 4 Chuyên viên trong phòng
| Bàn | Chuyên viên | Chuyên môn |
| :--- | :--- | :--- |
| **Bàn 1** | **Minh** | Nghiên cứu & Lập dàn ý, cấu trúc, luận điểm |
| **Bàn 2** | **Lan** | Chấp bút & Soạn thảo chính (công văn, báo cáo, đề án, thư từ...) |
| **Bàn 3** | **Tuấn** | Biên tập, hiệu đính văn phong & chuẩn thể thức (Nghị định 30), rà soát rủi ro |
| **Bàn 4** | **Vy** | Tổng hợp nhiều bản thảo, tóm tắt điều hành, bảng biểu & xuất bản |

## 3 Chế độ giao việc thông minh
1. **Tự chọn người giỏi nhất**: Nhập yêu cầu, hệ thống tự chọn đúng chuyên viên phù hợp nhất cho loại văn bản đó.
2. **Dự án lớn — Chia 3 bàn & Vy tổng hợp**: Minh, Lan, Tuấn làm song song 3 phần bổ trợ → Vy tự động ghép thành **1 văn bản hoàn chỉnh duy nhất**.
3. **Chọn đích danh bàn**: Giao trực tiếp cho 1 chuyên viên bất kỳ.

## Cách khởi động trên máy tính Windows (1 click)
1. Cài Python 3 (nếu máy chưa có: https://www.python.org/downloads/ — nhớ tick *Add Python to PATH*).
2. Bấm đúp file **`start.bat`** (hoặc mở terminal chạy `python server.py` rồi vào `http://127.0.0.1:8080`).
3. Nếu máy chưa chạy Antigravity, bấm nút **Cài đặt AI** ở góc trên phải để dán **Google Gemini API Key** (tạo miễn phí tại https://aistudio.google.com/apikey) hoặc trỏ tới **Ollama** chạy nội bộ.

## Lấy kết quả văn bản
- Bấm nút **Kho văn bản** ở góc trên phải (hoặc bấm vào thông báo khi làm xong).
- Hỗ trợ **Copy**, **Tải Word (`.doc`)** mở trực tiếp trong Microsoft Word, và **Tải `.md`**.
- Toàn bộ file cũng được tự động lưu tại thư mục `results/`.
