import speech_recognition as sr
import sys
import threading
import queue
import msvcrt
import pyaudio

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.0

# ── Bluetooth device auto-detection ──────────────────────────────────────────
_BT_PREFERRED = ["headset", "airdopes", "earphone", "buds", "airpods", "bluetooth"]
_BT_FALLBACK  = ["hands-free", "handsfree"]  # HFP profile, 8kHz — lower priority

def _find_bluetooth_device_index():
    """Probes BT devices in order of preference, returns first that opens at 16kHz."""
    p = pyaudio.PyAudio()
    candidates = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            n = info["name"].lower()
            if any(kw in n for kw in _BT_PREFERRED):
                candidates.append((0, i))
            elif any(kw in n for kw in _BT_FALLBACK):
                candidates.append((1, i))
    p.terminate()

    candidates.sort()
    for _, idx in candidates:
        try:
            tp = pyaudio.PyAudio()
            ts = tp.open(format=pyaudio.paInt16, channels=1, rate=16000,
                         input=True, input_device_index=idx, frames_per_buffer=480)
            ts.stop_stream(); ts.close(); tp.terminate()
            return idx  # First device that opens cleanly
        except Exception:
            pass
    return None  # Fallback to system default

# Detect once at module load so every listen() call reuses it
_BT_DEVICE_INDEX = _find_bluetooth_device_index()
# ─────────────────────────────────────────────────────────────────────────────

def listen(prompt="Listening (or type command)..."):
    print(prompt)
    
    result_queue = queue.Queue()
    stop_event = threading.Event()
    
    # Thread 1: Keyboard Input
    def keyboard_listener():
        buffer = ""
        while not stop_event.is_set():
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ('\r', '\n'): # Enter pressed
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    if buffer.strip():
                        result_queue.put(buffer.strip())
                        break
                elif char == '\x08': # Backspace
                    if len(buffer) > 0:
                        buffer = buffer[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                else:
                    buffer += char
                    sys.stdout.write(char)
                    sys.stdout.flush()
            else:
                stop_event.wait(0.1)

    # Thread 2: Microphone Input (Using speech_recognition directly)
    def mic_listener():
        try:
            with sr.Microphone(device_index=_BT_DEVICE_INDEX) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                while not stop_event.is_set():
                    try:
                        audio = recognizer.listen(source, timeout=1.0, phrase_time_limit=10.0)
                        if stop_event.is_set():
                            break
                        text = recognizer.recognize_google(audio)
                        text = text.strip()
                        if text:
                            result_queue.put(text)
                            break
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        break
        except Exception:
            pass
            
    # Start both streams
    t_key = threading.Thread(target=keyboard_listener, daemon=True)
    t_mic = threading.Thread(target=mic_listener, daemon=True)
    
    t_key.start()
    t_mic.start()
    
    # Wait for either to return a transcribed string, or timeout and loop
    text_result = None
    try:
        # 10 second timeout limit for either input method to catch up
        text_result = result_queue.get(timeout=10)
    except queue.Empty:
        pass
        
    # Send kill signal to threads
    stop_event.set()
    
    if text_result:
        print(f"You: {text_result}")
        return text_result.lower()
        
    return None