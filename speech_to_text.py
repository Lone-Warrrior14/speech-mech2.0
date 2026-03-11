import speech_recognition as sr
import sys
import threading
import queue
import msvcrt
import pyaudio

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5  # Allow 1.5 seconds of silence before cutting off
recognizer.dynamic_energy_threshold = False  # DO NOT recalibrate while listening (prevents early cutoff)
recognizer.dynamic_energy_ratio = 2.5  # Ignore moderate fan noise
recognizer.energy_threshold = 4000  # Start higher for fan noise

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

# Create a single global microphone object to avoid initialization delays
# and PyAudio crashing from repeatedly reopening the device.
_global_mic = None

# Global background worker variables
_speech_queue = queue.Queue()
_is_listening_now = False
_bg_thread_started = False

def get_global_mic():
    global _global_mic
    if _global_mic is None:
        _global_mic = sr.Microphone(device_index=_BT_DEVICE_INDEX)
        # Enter the context manager ONCE (this opens the stream)
        _global_mic.__enter__()
        # Adjust for ambient noise once
        recognizer.adjust_for_ambient_noise(_global_mic, duration=2.0)
    return _global_mic

def _mic_worker():
    # Initialize the mic only once in this persistent daemon thread
    mic = get_global_mic()
    while True:
        try:
            # timeout=None GUARANTEES we never dump the pre-roll audio buffer.
            # This ensures the very start of your words are perfectly captured.
            audio = recognizer.listen(mic, timeout=None, phrase_time_limit=10.0)
            
            if _is_listening_now:
                # We only transcribe if the main loop is actively waiting
                try:
                    text = recognizer.recognize_google(audio).strip()
                    if text and _is_listening_now:
                        _speech_queue.put(text)
                except Exception:
                    pass
        except Exception:
            # Fallback if PyAudio hiccups
            import time
            time.sleep(0.1)

def listen(prompt="Listening (or type command)..."):
    global _is_listening_now, _bg_thread_started
    import time
    
    print(prompt)
    
    # Start the permanent background mic thread on the very first listen()
    if not _bg_thread_started:
        _bg_thread_started = True
        threading.Thread(target=_mic_worker, daemon=True).start()
    
    # Flush any stale speech that happened BEFORE this point
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
        except queue.Empty:
            break
            
    _is_listening_now = True
    
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

    t_key = threading.Thread(target=keyboard_listener, daemon=True)
    t_key.start()
    
    text_result = None
    start_time = time.time()
    
    try:
        # 10 second timeout limit overall
        while time.time() - start_time < 10:
            # Check if keyboard caught anything
            try:
                text_result = result_queue.get_nowait()
                break
            except queue.Empty:
                pass
                
            # Check if background mic thread transcribed anything
            try:
                text_result = _speech_queue.get_nowait()
                break
            except queue.Empty:
                pass
                
            time.sleep(0.1)
            
    except Exception as e:
        print(f"[Listen Loop Error]: {e}")
        
    # Turn off mic transcriptions before leaving
    _is_listening_now = False
    stop_event.set()
    
    if text_result:
        print(f"You: {text_result}")
        return text_result.lower()
        
    return None