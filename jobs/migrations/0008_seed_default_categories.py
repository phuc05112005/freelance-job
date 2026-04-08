from django.db import migrations


DEFAULT_CATEGORIES = [
    ('Khoa học dữ liệu & AI', 'khoa-hoc-du-lieu-ai'),
    ('An ninh mạng', 'an-ninh-mang'),
    ('Thiết kế đồ họa', 'thiet-ke-do-hoa'),
    ('UI/UX Design', 'ui-ux-design'),
    ('Kiến trúc & Nội thất', 'kien-truc-noi-that'),
    ('Xây dựng', 'xay-dung'),
    ('Cơ khí - Chế tạo', 'co-khi-che-tao'),
    ('Điện - Điện tử', 'dien-dien-tu'),
    ('Tự động hóa', 'tu-dong-hoa'),
    ('Viễn thông', 'vien-thong'),
    ('Sản xuất', 'san-xuat'),
    ('Vận hành', 'van-hanh'),
    ('Logistics & Chuỗi cung ứng', 'logistics-chuoi-cung-ung'),
    ('Mua hàng', 'mua-hang'),
    ('Bán hàng', 'ban-hang'),
    ('Kinh doanh quốc tế', 'kinh-doanh-quoc-te'),
    ('Marketing', 'marketing'),
    ('Digital Marketing', 'digital-marketing'),
    ('Nội dung & Copywriting', 'noi-dung-copywriting'),
    ('Truyền thông', 'truyen-thong'),
    ('Quảng cáo', 'quang-cao'),
    ('Nhân sự', 'nhan-su'),
    ('Hành chính - Văn phòng', 'hanh-chinh-van-phong'),
    ('Kế toán', 'ke-toan'),
    ('Kiểm toán', 'kiem-toan'),
    ('Tài chính - Ngân hàng', 'tai-chinh-ngan-hang'),
    ('Chứng khoán - Đầu tư', 'chung-khoan-dau-tu'),
    ('Bảo hiểm', 'bao-hiem'),
    ('Pháp chế', 'phap-che'),
    ('Luật', 'luat'),
    ('Giáo dục - Đào tạo', 'giao-duc-dao-tao'),
    ('Ngoại ngữ - Biên phiên dịch', 'ngoai-ngu-bien-phien-dich'),
    ('Y tế', 'y-te'),
    ('Dược', 'duoc'),
    ('Điều dưỡng', 'dieu-duong'),
    ('Công nghệ sinh học', 'cong-nghe-sinh-hoc'),
    ('Công nghệ thông tin', 'cong-nghe-thong-tin'),
    ('Nông nghiệp', 'nong-nghiep'),
    ('Thực phẩm - Đồ uống', 'thuc-pham-do-uong'),
    ('Nhà hàng - Khách sạn', 'nha-hang-khach-san'),
    ('Du lịch', 'du-lich'),
    ('Bất động sản', 'bat-dong-san'),
    ('Thương mại điện tử', 'thuong-mai-dien-tu'),
    ('Chăm sóc khách hàng', 'cham-soc-khach-hang'),
    ('Dịch vụ khách hàng', 'dich-vu-khach-hang'),
    ('Kho vận', 'kho-van'),
    ('Vận tải', 'van-tai'),
    ('Môi trường', 'moi-truong'),
    ('Năng lượng', 'nang-luong'),
    ('Nghiên cứu & Phát triển (R&D)', 'nghien-cuu-phat-trien-rd'),
    ('Thống kê', 'thong-ke'),
    ('Báo chí', 'bao-chi'),
    ('Sự kiện', 'su-kien'),
]


def seed_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    for name, slug in DEFAULT_CATEGORIES:
        JobCategory.objects.get_or_create(slug=slug, defaults={'name': name})


def unseed_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    slugs = [slug for _, slug in DEFAULT_CATEGORIES]
    JobCategory.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_alter_jobcategory_options_alter_job_employment_type_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
