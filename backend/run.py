import os
import sys
import subprocess
import urllib.request
import webbrowser
import time

# Reconfigure stdout to support UTF-8 print outputs on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Định nghĩa các thư viện React offline cần thiết
LIBS = {
    "react.production.min.js": "https://unpkg.com/react@18.2.0/umd/react.production.min.js",
    "react-dom.production.min.js": "https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js",
    "babel.min.js": "https://unpkg.com/@babel/standalone@7.24.0/babel.min.js"
}

def install_dependencies():
    print("=== [1/3] Kiểm tra dependencies Python ===")
    required_packages = ["fastapi", "uvicorn", "python-multipart"]
    
    # Kiểm tra xem gói nào chưa cài đặt
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_packages.append(pkg)
            
    if missing_packages:
        print(f"Phát hiện thiếu các gói: {', '.join(missing_packages)}")
        print("Đang cài đặt tự động từ requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Cài đặt dependencies thành công!")
        except Exception as e:
            print(f"❌ Lỗi cài đặt dependencies: {e}")
            print("Đang thử cài đặt trực tiếp các gói bị thiếu...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("Cài đặt thành công!")
            except Exception as e2:
                print(f"❌ Lỗi cài đặt trực tiếp: {e2}")
                sys.exit(1)
    else:
        print("Mọi dependencies Python đã sẵn sàng.")

def download_offline_libs():
    print("\n=== [2/3] Kiểm tra các thư viện React offline ===")
    libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "libs")
    os.makedirs(libs_dir, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for filename, url in LIBS.items():
        filepath = os.path.join(libs_dir, filename)
        if not os.path.exists(filepath):
            print(f"Đang tải {filename} từ CDN...")
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    with open(filepath, "wb") as f:
                        f.write(response.read())
                print(f"Đã tải và lưu {filename} thành công.")
            except Exception as e:
                print(f"❌ Lỗi khi tải {filename} từ {url}: {e}")
                print("Ứng dụng có thể không hoạt động hoàn toàn offline nếu tải thất bại.")
        else:
            print(f"Đã có sẵn {filename} (Offline).")

def start_server():
    print("\n=== [3/3] Khởi chạy FastAPI Server ===")
    port = 8000
    url = f"http://127.0.0.1:{port}"
    
    # Đợi 1 giây rồi mở trình duyệt tự động
    def open_browser():
        time.sleep(1.5)
        print(f"Mở trình duyệt truy cập: {url}")
        webbrowser.open_new_tab(url)
        
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        import uvicorn
        uvicorn.run("app_api:app", host="127.0.0.1", port=port, reload=True)
    except KeyboardInterrupt:
        print("\nĐã tắt server SmartDocAI.")
    except Exception as e:
        print(f"❌ Lỗi khi chạy server: {e}")
        sys.exit(1)

def main():
    install_dependencies()
    download_offline_libs()
    start_server()

if __name__ == "__main__":
    main()
