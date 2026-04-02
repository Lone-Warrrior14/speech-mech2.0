import subprocess
import sys
import os

# Capture traceback of rag_server startup
venv_py = r"D:\SPEECH_MECH3\SPEECH_MECH\venv\Scripts\python.exe"
rag_srv = r"D:\SPEECH_MECH3\SPEECH_MECH\RAG\rag_server.py"

print("Starting RAG Intelligence check...")
try:
    # use -u to avoid buffering and capture immediate output
    result = subprocess.run([venv_py, "-u", rag_srv], 
                           cwd=os.path.dirname(rag_srv),
                           capture_output=True, 
                           text=True, 
                           timeout=60)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except subprocess.TimeoutExpired as e:
    print("STDOUT (Timed Out):", e.stdout)
    print("STDERR (Timed Out):", e.stderr)
except Exception as e:
    print("Execution failed:", e)
