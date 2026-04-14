import webbrowser
import time
import subprocess
import sys
import os

def kill_process_on_port(port):
    try:
        # Find PIDs using the port (Windows specific)
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True).decode()
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                if pid != "0":
                    print(f"[INIT] Port {port} is occupied by PID {pid}. Terminating...")
                    subprocess.run(f"taskkill /F /PID {pid} /T", shell=True, capture_output=True)
    except Exception:
        pass # No process found or error killing

def start_server():
    print("\n" + "="*50)
    print("   SPEECH-MECH NEURAL ECOSYSTEM BOOT SEQUENCE")
    print("="*50 + "\n")

    # Port management
    ports = [8000, 5000, 5060, 5050]
    print(f"[INIT] Clearing potential conflicting ports {ports}...")
    for port in ports:
        kill_process_on_port(port)
    time.sleep(1)

    # Path Resolution
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir) # The project root
    
    venv_python = os.path.join(root_dir, "venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    server_path = os.path.join(base_dir, "web_server.py")
    
    print(f"[BOOT] Starting Unified Neural Ecosystem (Port 8000)...")
    # Main dashboard runs from launch_web_system
    # Removed CREATE_NEW_PROCESS_GROUP to allow Ctrl+C propagation
    main_process = subprocess.Popen([python_exe, server_path], cwd=base_dir)
    
    print("\n[WAIT] Synchronizing neural links (3s)...")
    time.sleep(3)
    
    if main_process.poll() is not None:
        print("[CRITICAL] Main Dashboard failed to start. Review server_log.txt.")
        return
        
    print("\n" + "!"*50)
    print("   SYSTEM IS NOW LIVE - UNIFIED CORE")
    print("   Local URL:  http://127.0.0.1:8000")
    print("   NGROK Tip:  Run 'ngrok http 8000' in a new terminal")
    print("!"*50 + "\n")
    
    webbrowser.open("http://127.0.0.1:8000")
    
    try:
        main_process.wait()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating unified neural links...")
        main_process.terminate()
        try:
            main_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            main_process.kill()
        print("Ecosystem offline.")

if __name__ == "__main__":
    start_server()

