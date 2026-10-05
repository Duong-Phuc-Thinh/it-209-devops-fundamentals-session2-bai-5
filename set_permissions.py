#!/usr/bin/env python3
import os
import sys
import pwd
import grp

def setup_mock_environment():
    """Tạo thư mục giả lập để test quyền nếu không chạy trên server thật."""
    mock_dir = "/tmp/ptit-web"
    print(f"[*] Đang tạo môi trường giả lập tại {mock_dir}...")
    os.makedirs(os.path.join(mock_dir, "html"), exist_ok=True)
    with open(os.path.join(mock_dir, "html", "index.html"), "w") as f:
        f.write("<h1>PTIT Web Deploy v1.0</h1>\n")
    print(f"[+] Đã tạo môi trường giả lập. Chạy lại script với tham số: sudo python3 set_permissions.py --path {mock_dir}")

def set_permissions(path, owner_name, group_name):
    try:
        # Lấy thông tin UID và GID tương ứng
        uid = pwd.getpwnam(owner_name).pw_uid
        gid = grp.getgrnam(group_name).gr_gid
    except KeyError as e:
        print(f"[!] Lỗi: User '{owner_name}' hoặc Group '{group_name}' không tồn tại trên hệ thống.")
        print("Vui lòng tạo user/group trước khi phân quyền.")
        return False

    if not os.path.exists(path):
        print(f"[!] Lỗi: Thư mục target '{path}' không tồn tại.")
        return False

    try:
        print(f"[*] Đang đổi quyền sở hữu thư mục {path} sang {owner_name}:{group_name}...")
        # Thay đổi owner và group cho thư mục gốc
        os.chown(path, uid, gid)
        os.chmod(path, 0o755)

        # Phân quyền đệ quy cho toàn bộ tệp tin và thư mục con
        for root, dirs, files in os.walk(path):
            for d in dirs:
                dir_path = os.path.join(root, d)
                os.chown(dir_path, uid, gid)
                os.chmod(dir_path, 0o755) # Thư mục cần quyền thực thi (x) để cd vào
            for f in files:
                file_path = os.path.join(root, f)
                os.chown(file_path, uid, gid)
                os.chmod(file_path, 0o644) # Tệp tin tĩnh chỉ cần quyền đọc (r) cho group/others
        
        print("[+] Phân quyền thành công!")
        print(f" - Chủ sở hữu (Owner): {owner_name} (Quyền: rw- hoặc rwx)")
        print(f" - Nhóm sở hữu (Group): {group_name} (Quyền: r-- hoặc r-x)")
        return True
    except PermissionError:
        print("[!] Lỗi: Từ chối truy cập. Bạn cần chạy script này dưới quyền root (sudo).")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quản lý phân quyền thư mục Web tĩnh trên Linux.")
    parser.add_argument("--path", default="/var/www/ptit-web", help="Đường dẫn thư mục web")
    parser.add_argument("--owner", default="devops", help="Tên user sở hữu (devops)")
    parser.add_argument("--group", default="www-data", help="Tên group sở hữu (www-data)")
    parser.add_argument("--mock-setup", action="store_true", help="Tạo thư mục test giả lập tại /tmp/ptit-web")
    
    args = parser.parse_args()

    if args.mock_setup:
        setup_mock_environment()
        sys.exit(0)

    if os.getuid() != 0:
        print("[!] Chú ý: Script cần quyền sudo/root để thực hiện thay đổi owner/group.")
        print(f"Vui lòng chạy lệnh: sudo python3 {sys.argv[0]} --path {args.path} --owner {args.owner} --group {args.group}")
        sys.exit(1)

    success = set_permissions(args.path, args.owner, args.group)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
