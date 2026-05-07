# Nền tảng Kết nối Freelance (Freelance Job Platform)

Dự án cuối khóa cho môn **Phát triển phần mềm mã nguồn mở**. Đây là một ứng dụng web đầy đủ tính năng (Full-stack) được xây dựng trên nền tảng Django, giúp kết nối sinh viên (freelancers) với các nhà tuyển dụng.

## 🌟 Giới thiệu

Hệ thống cung cấp một môi trường trực tuyến cho phép:
- **Sinh viên:** Tìm kiếm việc làm freelance, quản lý CV và theo dõi trạng thái ứng tuyển.
- **Nhà tuyển dụng:** Đăng tin tuyển dụng, quản lý hồ sơ ứng viên và quản lý quy trình tuyển dụng.
- **Quản trị viên:** Giám sát toàn bộ hoạt động của hệ thống, quản lý người dùng và danh mục.

## 🚀 Công nghệ sử dụng

Dự án tận dụng sức mạnh của các công nghệ hiện đại:
- **Backend:** [Django 6.0](https://www.djangoproject.com/)
- **API:** [Django REST Framework](https://www.django-rest-framework.org/)
- **Cơ sở dữ liệu:** [PostgreSQL](https://www.postgresql.org/)
- **Xử lý hình ảnh:** [Pillow](https://python-pillow.org/)
- **Giao diện:** Django Templates, CSS tùy chỉnh (site.css)
- **Xử lý văn bản:** Rich Text Support

## ✨ Tính năng chính

### 👥 Quản lý người dùng (Role-based)
- Phân quyền 3 vai trò: `Sinh viên`, `Nhà tuyển dụng`, `Quản trị viên`.
- Luồng xác thực đầy đủ: Đăng ký, đăng nhập, đăng xuất và kích hoạt tài khoản qua email.
- Hồ sơ cá nhân: Cập nhật thông tin, avatar, kỹ năng, kinh nghiệm và học vấn.

### 💼 Quản lý công việc
- Đăng tin tuyển dụng với đầy đủ thông tin: Lương (thỏa thuận/khoảng/cố định), loại hình (toàn thời gian/bán thời gian), hình thức làm việc (trực tiếp/từ xa/hybrid).
- Tìm kiếm và lọc công việc theo danh mục, địa điểm, mức lương và kỹ năng.
- Chức năng lưu công việc yêu thích.

### 📝 Quy trình ứng tuyển
- Ứng tuyển trực tiếp với tệp CV hoặc CV mặc định trên hệ thống.
- Nhà tuyển dụng duyệt hồ sơ và cập nhật trạng thái ứng tuyển (Đã nhận, Đang xem xét, Chấp nhận, Từ chối).
- Quản lý danh sách ứng viên chuyên nghiệp.

### 📊 Trang quản trị (Admin Center)
- Dashboard dành riêng cho nhà tuyển dụng và quản trị viên.
- Quản lý danh mục công việc, mức độ kinh nghiệm và các loại hình làm việc.
- Quản lý người dùng và cấp quyền.

### 🌐 API RESTful
- Hệ thống API đầy đủ cho việc tích hợp với các ứng dụng khác hoặc mở rộng sau này.
- Xác thực bằng Token (DRF Authtoken).

## 🛠️ Hướng dẫn cài đặt

Làm theo các bước sau để thiết lập dự án trên môi trường cục bộ:

### 1. Sao chép dự án
```bash
git clone https://github.com/yourusername/freelance-job.git
cd freelance-job
```

### 2. Thiết lập môi trường ảo
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Cài đặt các thư viện cần thiết
```powershell
pip install -r requirements.txt
```

### 4. Cấu hình cơ sở dữ liệu
Tạo tệp `.env` dựa trên `.env.example` và điền thông tin PostgreSQL của bạn:
```env
DB_NAME=freelance_platform
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Áp dụng Migrations
```powershell
python manage.py migrate
```

### 6. Tạo tài khoản quản trị (Superuser)
```powershell
python manage.py createsuperuser
```

### 7. Khởi tạo dữ liệu mẫu (Tùy chọn)
Dự án có sẵn lệnh để nạp dữ liệu demo giúp bạn trải nghiệm nhanh:
```powershell
python manage.py seed_demo
```
*Tài khoản demo sau khi seed:*
- **Nhà tuyển dụng:** `employer_demo` / `123456Aa!`
- **Sinh viên:** `student_demo` / `123456Aa!`

### 8. Chạy máy chủ phát triển
```powershell
python manage.py runserver
```
Truy cập ứng dụng tại: `http://127.0.0.1:8000/`

## 📁 Cấu trúc thư mục chính

- `core/`: Cấu hình chính của dự án Django.
- `users/`: Quản lý người dùng, hồ sơ và CV.
- `jobs/`: Quản lý tin tuyển dụng và danh mục.
- `applications/`: Quản lý hồ sơ ứng tuyển và quy trình tuyển dụng.
- `templates/`: Chứa các tệp giao diện HTML.
- `media/`: Chứa các tệp tải lên (Avatar, CV, ảnh thương hiệu).
- `static/`: Chứa các tệp tĩnh (CSS, JS, Images).

## 🤝 Đóng góp

Đây là một dự án mã nguồn mở. Mọi đóng góp đều được trân trọng:
1. Fork dự án.
2. Tạo nhánh tính năng (`git checkout -b feature/AmazingFeature`).
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`).
4. Push lên nhánh (`git push origin feature/AmazingFeature`).
5. Tạo một Pull Request.

## 📄 Giấy phép

Dự án này được cấp phép theo Giấy phép MIT - xem tệp [LICENSE](LICENSE) để biết thêm chi tiết.

---
*Dự án được thực hiện bởi Phuc Le - 2026*
