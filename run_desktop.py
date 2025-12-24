import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path

def load_env_from_exe_or_project():
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    # Project root .env
    project_root = Path(__file__).resolve().parent
    load_dotenv(project_root / ".env")

    # EXE folder .env (when packaged)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        load_dotenv(exe_dir / ".env")

def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

def port_is_free(host: str, port: int) -> bool:
    return not port_is_open(host, port)

def wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if port_is_open(host, port):
            return True
        time.sleep(0.25)
    return False

def pick_port(host: str, start_port: int) -> int:
    # try 8000..8010
    for p in range(start_port, start_port + 11):
        if port_is_free(host, p):
            return p
    return start_port  # fallback

def main():
    load_env_from_exe_or_project()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    host = os.getenv("APP_HOST", "127.0.0.1")
    base_port = int(os.getenv("APP_PORT", "8000"))
    port = pick_port(host, base_port)

    url = f"http://{host}:{port}/"

    # open browser only when server is listening
    def open_browser_when_ready():
        if wait_for_port(host, port, timeout=20.0):
            webbrowser.open(url)
        else:
            print(f"[ERROR] Server did not start on {url}. Check console logs.")

    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    # Start Django server
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0], "runserver", f"{host}:{port}", "--noreload"])

if __name__ == "__main__":
    main()
