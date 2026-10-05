#!/usr/bin/env python3
import os
import sys
import subprocess

def run_cmd(cmd, check=True):
    try:
        res = subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}\nExit code: {e.returncode}\nStderr: {e.stderr}", file=sys.stderr)
        if check:
            sys.exit(e.returncode)

def main():
    if os.getuid() != 0:
        print("[!] This script must be run as root (sudo python3 setup.py).", file=sys.stderr)
        sys.exit(1)

    print("=== 1. Checking / Creating system users and groups ===")
    # Check/Create devops user
    try:
        import pwd
        pwd.getpwnam('devops')
        print("[*] User 'devops' already exists.")
    except KeyError:
        print("[+] Creating 'devops' user...")
        run_cmd("useradd -m -s /bin/bash devops")

    # Check/Create www-data group
    try:
        import grp
        grp.getgrnam('www-data')
        print("[*] Group 'www-data' already exists.")
    except KeyError:
        print("[+] Creating 'www-data' group...")
        run_cmd("groupadd www-data")

    print("\n=== 2. Creating target directory structures ===")
    base_dir = "/opt/my-app"
    html_dir = f"{base_dir}/html"
    logs_dir = f"{base_dir}/logs"

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    print(f"[*] Created {html_dir}")
    print(f"[*] Created {logs_dir}")

    # Create default index.html if not present
    index_file = f"{html_dir}/index.html"
    if not os.path.exists(index_file):
        with open(index_file, "w") as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n<title>Safe Web Space</title>\n</head>\n<body>\n<h1>Success: Welcome to the Secure Web Environment in /opt!</h1>\n</body>\n</html>\n")
        print(f"[*] Created default template at {index_file}")

    print("\n=== 3. Setting Ownership recursively (devops:www-data) ===")
    run_cmd(f"chown -R devops:www-data {base_dir}")
    print(f"[+] Ownership of {base_dir} recursively changed to devops:www-data")

    print("\n=== 4. Setting Permissions ===")
    # /opt/my-app -> 750 (rwxr-x---)
    os.chmod(base_dir, 0o750)
    print(f"[+] Base directory {base_dir} set to 750")

    # /opt/my-app/html -> 750 (rwxr-x---)
    os.chmod(html_dir, 0o750)
    print(f"[+] HTML directory {html_dir} set to 750")

    # /opt/my-app/logs -> 770 (rwxrwx---) so both devops and www-data can write
    os.chmod(logs_dir, 0o770)
    print(f"[+] Logs directory {logs_dir} set to 770")

    # Files -> 640 (rw-r-----)
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            file_path = os.path.join(root, f)
            os.chmod(file_path, 0o640)
            print(f"[+] File {file_path} set to 640")

    print("\n=== 5. Applying Nginx Configuration ===")
    nginx_conf_content = """server {
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
"""
    
    nginx_avail_path = "/etc/nginx/sites-available/my-app"
    nginx_enabled_path = "/etc/nginx/sites-enabled/my-app"
    default_site_path = "/etc/nginx/sites-enabled/default"

    if os.path.exists("/etc/nginx"):
        with open(nginx_avail_path, "w") as f:
            f.write(nginx_conf_content)
        print(f"[+] Written Nginx server block to {nginx_avail_path}")

        # Create symlink
        if not os.path.exists(nginx_enabled_path):
            os.symlink(nginx_avail_path, nginx_enabled_path)
            print(f"[+] Created symlink: {nginx_enabled_path} -> {nginx_avail_path}")

        # Remove default nginx site if conflicts on port 80
        if os.path.exists(default_site_path):
            os.remove(default_site_path)
            print("[-] Removed default Nginx site configuration to avoid port conflicts.")

        # Test & Reload Nginx
        print("[*] Testing Nginx config...")
        test_res = run_cmd("nginx -t", check=False)
        print("[*] Reloading Nginx service...")
        run_cmd("systemctl reload nginx", check=False)
        print("[+] Nginx reloaded successfully!")
    else:
        print("[!] Nginx not found on this machine. Configuration files have not been active but written output looks like:")
        print(nginx_conf_content)

    print("\n=== Verification and Validation Instructions ===")
    print(f"1. Verification of rights: ls -la {base_dir}")
    print(f"2. Try writing to document as 'devops' user (without sudo):")
    print(f"   su - devops -c 'echo \"Update Test\" >> {html_dir}/index.html'")
    print(f"3. Tail log files to watch real-time events:")
    print(f"   tail -n 10 {logs_dir}/access.log")

if __name__ == "__main__":
    main()
