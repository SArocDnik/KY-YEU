# 🎓 Kỷ Yếu Số - Yearbook 2026

Chào mừng đến với dự án **Kỷ Yếu Số** (Digital Yearbook) của lớp 12 Tin. Đây là một website tương tác hiện đại, mang phong cách Cyberpunk, giúp lưu giữ những kỷ niệm đẹp nhất của tuổi học trò.

## ✨ Tính Năng Nổi Bật

### 1. 🎵 Trải Nghiệm Âm Nhạc
- Nhạc nền tự động phát (Autoplay) với cơ chế fallback thông minh.
- Nút bật/tắt (Toggle) nổi bật góc màn hình.
- Tự động lặp lại (Loop).

### 2. 📱 Giao Diện Responsive (Mobile-First)
- Tối ưu hóa hoàn toàn cho điện thoại di động và máy tính bảng.
- **Timeline**: Bố cục khoa học, không bị chồng chéo trên màn hình nhỏ.
- **Navigation**: Menu điều hướng dính (Sticky Header) tiện lợi.

### 3. ✍️ Lưu Bút Số (Digital Guestbook)
- Gửi lời nhắn chúc mừng tới cả lớp.
- **Backend**: Sử dụng Python Flask lưu trữ dữ liệu vào file `guestbook.json` (bền vững, không mất khi tải lại trang).
- **Discord Integration**: Tự động bắn thông báo về kênh Discord của lớp khi có lưu bút mới.
- **Profanity Filter**: Hệ thống tự động chặn các từ ngữ không phù hợp (Tiếng Việt & Tiếng Anh).

### 4. 🎨 Hiệu Ứng Visual
- **Tech Stack**: HTML5, Tailwind CSS, Anime.js.
- Hiệu ứng gõ phím (Typing effect), đếm ngược (Countdown), và các animation mượt mà.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Yêu cầu hệ thống
- Python 3.x đã được cài đặt.
- Thư viện Flask (`pip install flask`).

### Các bước thực hiện

1. **Chuẩn bị môi trường**:
   Mở terminal tại thư mục dự án và cài đặt thư viện cần thiết:
   ```bash
   pip install flask
   ```

2. **Khởi chạy Server**:
   ```bash
   python app.py
   ```
   *Server sẽ chạy tại địa chỉ: `http://localhost:5000`*

3. **Truy cập Website**:
   Mở trình duyệt và vào địa chỉ `http://localhost:5000` để trải nghiệm đầy đủ tính năng (Lưu bút, Nhạc, v.v.).

---

## 📂 Cấu Trúc Dự Án

```text
KY YEU/
├── app.py              # Backend Server (Flask) - Xử lý API, Discord, Filter
├── guestbook.json      # Database lưu trữ tin nhắn (JSON)
├── index.html          # Giao diện chính (HTML/JS/CSS)
├── README.md           # Tài liệu hướng dẫn
└── MUSIC/              # Thư mục chứa file nhạc
```

## 🛠️ API Endpoints

- **GET** `/api/messages`: Lấy danh sách lưu bút.
- **POST** `/api/messages`: Gửi lưu bút mới.
  - *Body*: `{ "name": "...", "msg": "..." }`
  - *Check*: Validate dữ liệu & Kiểm tra từ ngữ xấu.
- **POST** `/api/seed`: (Ẩn) Tạo dữ liệu mẫu.

---

*"Thanh xuân giống như một cơn mưa rào, dù cho bạn từng bị cảm lạnh vì tắm mưa, bạn vẫn muốn được đắm mình trong cơn mưa ấy lần nữa."*
