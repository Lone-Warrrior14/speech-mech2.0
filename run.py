import subprocess
import sys
import os

def main():
    print("="*60)
    print("   SPEECH-MECH NEURAL ECOSYSTEM UNIFIED LAUNCHER")
    print("="*60)
    
    # Path Resolution
    root_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.join(root_dir, "launch_web_system", "launch_web.py")
    
    # Check for venv
    venv_python = os.path.join(root_dir, "venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    if not os.path.exists(launcher_path):
        print(f"[ERROR] Could not find the launch script at: {launcher_path}")
        return

    print(f"[BOOT] Initializing system from root: {root_dir}")
    print(f"[BOOT] Executing System Launch Sequence...")
    
    # Execute the launch script
    try:
        process = subprocess.Popen([python_exe, launcher_path], cwd=root_dir)
        process.wait()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Launcher interrupted. Synchronizing shutdown...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("[SHUTDOWN] System Offline.")
    except Exception as e:
        print(f"\n[CRITICAL] Launcher failed: {e}")

if __name__ == "__main__":
    main()
