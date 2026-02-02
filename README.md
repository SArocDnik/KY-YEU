# 🎓 Digital Yearbook & Invitation Platform (Kỷ Yếu Online)

Một nền tảng web tạo thiệp mời kỷ yếu online với khả năng cá nhân hóa cao, hỗ trợ xem trước (Open Graph) cực đẹp khi chia sẻ lên mạng xã hội (Facebook, Zalo).

![Demo Admin Panel](https://placehold.co/600x400/161b22/58a6ff?text=Admin+Panel+Preview)

## ✨ Tính Năng Nổi Bật

### 1. 💌 Thiệp Mời Cá Nhân Hóa (Personalized Links)
- Tạo đường dẫn riêng cho từng người nhận: `domain.com/p/ten-nguoi-nhan`.
- **Dynamic Open Graph:** Tùy chỉnh ảnh nền (thumbnail), tiêu đề và lời nhắn hiển thị trên Messenger/Facebook cho từng link.
- Hỗ trợ tải ảnh lên server hoặc dùng URL ảnh ngoài (Imgur, Cloudinary).

### 2. 🛠️ Admin Panel Mạnh Mẽ (`/admin`)
- Giao diện Dark Mode hiện đại, dễ sử dụng.
- **Quản lý Link:** Tạo, Xem, Sửa, Xóa link.
- **Template Lời Chúc:** Lưu các mẫu lời chúc hay để tái sử dụng nhanh.
- **Live Preview:** Xem trước ảnh upload ngay lập tức.

### 3. 📒 Lưu Bút Kỹ Thuật Số (Guestbook)
- Mọi người có thể để lại lời nhắn chung cho cả lớp.
- **Discord Notification:** Tự động bắn thông báo về Discord khi có tin nhắn mới.
- Hỗ trợ lọc từ ngữ không phù hợp (Profanity Filter).

### 4. 🎵 Trải Nghiệm Người Dùng
- **Background Music:** Nhạc nền tự động phát (hoặc chờ tương tác) với trình phát nhạc tùy chỉnh.
- **Typing Effect:** Hiệu ứng gõ chữ lời chào ấn tượng.
- **Responsive:** Hiển thị tốt trên cả Mobile và Desktop.

---

## 🛠️ Cài Đặt & Chạy Local

### Yêu cầu
- Python 3.8+
- Git

### Các bước thực hiện

1. **Clone dự án:**
   ```bash
   git clone https://github.com/your-username/KY-YEU-main.git
   cd KY-YEU-main
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình môi trường (Tùy chọn):**
   - Mặc định hệ thống sẽ dùng file JSON (`guestbook.json`, `personalized_links.json`) để lưu dữ liệu.
   - Nếu muốn dùng **MongoDB Atlas**, set biến môi trường:
     ```bash
     export MONGO_URI="mongodb+srv://..."
     ```

4. **Chạy ứng dụng:**
   ```bash
   python app.py
   ```
   - Web sẽ chạy tại: `http://localhost:1000`
   - Admin Panel: `http://localhost:1000/admin`

---

## 🚀 Triển Khai (Deployment)

Dự án đã được cấu hình sẵn để chạy tốt trên **Vercel** (Serverless Function).

### Cấu trúc file quan trọng
- `app.py`: Backend chính (Flask).
- `index.html`: Giao diện trang chủ & trang cá nhân.
- `admin.html`: Giao diện trang quản trị.
- `static/`: Chứa file tĩnh (nhạc, ảnh mặc định).
- `vercel.json`: Cấu hình cho Vercel.

### Lưu ý khi deploy
1. **File Upload:** Trên môi trường Serverless (Vercel), file upload vào folder `/uploads` sẽ bị mất sau khi function restart.
   - 👉 **Khuyến nghị:** Sử dụng tính năng "Dùng URL ảnh" trong Admin Panel để ảnh hiển thị ổn định lâu dài.
2. **MongoDB:** Nên kết nối MongoDB Atlas để dữ liệu không bị mất khi redeploy code.

---

## 🧩 Cấu Trúc Dự Án

```
KY-YEU-main/
├── app.py                  # Core Logic (API, Routing, DB)
├── admin.html              # Admin Frontend
├── index.html              # User Frontend
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel config
├── static/                 # Static assets
│   └── music.mp3           # Background music
├── uploads/                # Temp upload folder
├── guestbook.json          # Local DB (Guestbook)
├── personalized_links.json # Local DB (Links)
└── message_templates.json  # Local DB (Templates)
```

---
**Developed with ❤️ for Yearbook 2026**
