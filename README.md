# Bài tập 5: Thiết lập thư mục Web an toàn tại phân vùng hệ thống (/opt/)

## 1. Giới thiệu mục tiêu
* Chuyển vị trí lưu trữ website tĩnh và logs ra khỏi các đường dẫn mặc định (`/var/www/html/` và `/var/log/nginx/`) sang `/opt/my-app/` để cô lập mã nguồn và dữ liệu log.
* Thực hiện phân quyền đệ quy nâng cao phân tách vai trò rõ ràng giữa tài khoản quản trị thường (`devops`) và tiến trình chạy của Nginx (`www-data`).

--- 

## 2. Ma trận phân quyền thiết kế

| Thư mục / Tệp tin | Quyền sở hữu (Owner:Group) | Quyền truy cập (Numeric) | Giải thích lý do |
| :--- | :--- | :--- | :--- |
| `/opt/my-app/` | `devops:www-data` | `750` | `devops` có toàn quyền quản trị, `www-data` có quyền đọc & thực thi để đi sâu vào các thư mục bên trong. Người dùng khác không có quyền. |
| `/opt/my-app/html/` | `devops:www-data` | `750` | `devops` có quyền thay đổi mã nguồn, `www-data` có quyền đọc và phục vụ tài nguyên cho client. |
| `/opt/my-app/logs/` | `devops:www-data` | `770` | Cả `devops` và tiến trình `www-data` (Nginx) đều có quyền ghi logs và đọc logs phục vụ giám sát. |
| `/opt/my-app/html/index.html` | `devops:www-data` | `640` | `devops` có thể ghi/sửa, `www-data` chỉ đọc, loại bỏ hoàn toàn các nguy cơ tấn công thay đổi nội dung trang web từ các tiến trình khác. |

---

## 3. Cấu hình Server Block Nginx (`nginx.conf`)
Cấu hình Server Block lưu tại `/etc/nginx/sites-available/my-app` và tạo symlink sang `/etc/nginx/sites-enabled/my-app`:
```nginx
server {
    listen 80;
    server_name localhost;

    root /opt/my-app/html;
    index index.html;

    access_log /opt/my-app/logs/access.log;
    error_log /opt/my-app/logs/error.log;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

---

## 4. Hướng dẫn chạy và cài đặt tự động bằng Python

Tệp tin mã nguồn `setup.py` sẽ thực hiện tự động hoàn toàn tất cả các yêu cầu từ việc kiểm tra/tạo người dùng, cấp quyền, cấu hình Nginx và reload dịch vụ.

### Bước 1: Chạy kịch bản tự động hóa bằng quyền root (sudo)
```bash
sudo python3 setup.py
```

### Bước 2: Kiểm tra phân quyền thực tế
```bash
ls -la /opt/my-app/
```
*Kết quả dự kiến hiển thị:*
```text
drwxr-x---  4 devops  www-data 4096 Oct 24 10:00 .
drwxr-xr-x  3 root    root     4096 Oct 24 09:55 ..
drwxr-x---  2 devops  www-data 4096 Oct 24 10:05 html
drwxrwx---  2 devops  www-data 4096 Oct 24 10:10 logs
```

### Bước 3: Ghi thử file bằng user thường `devops` (Không dùng sudo)
```bash
sudo -u devops bash -c 'echo "Update Test Success" >> /opt/my-app/html/index.html'
cat /opt/my-app/html/index.html
```
*Kết quả kì vọng:* Không có lỗi "Permission denied", dữ liệu được ghi thành công vào file `index.html`.

### Bước 4: Kiểm tra khả năng hoạt động và ghi log tự động của Nginx
```bash
# Tạo request kiểm tra HTTP
curl -I http://localhost/

# Xem file log đã chuyển hướng sang đường dẫn mới
cat /opt/my-app/logs/access.log
```
*Kết quả kì vọng:* Trả về HTTP Status `200 OK`, đồng thời xuất hiện log truy cập tại `/opt/my-app/logs/access.log` mới tạo.
