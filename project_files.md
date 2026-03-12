# Speech Mech Project Files

This document contains the source code for the key components of the Speech Mech application.

## 1. `main.py`
Main entry point of the Speech Mech application, tying all components together.

```python
from speech_to_text import listen
from text_to_speech import speak
from assistant import ask_ai, reset_memory, get_full_response
from command_router import route_intent
from intent_detector import detect_intent
from identity import (
    fuzzy_match_user,
    verify_password,
    switch_active_user,
    get_password_hash,
    set_user_password,
    create_user,
    register_face,
    verify_face
)
import time
import sys
import getpass

TIMEOUT_SECONDS = 30

def should_exit(command):
    return any(phrase in command for phrase in [
        "exit control",
        "stop assistant",
        "shutdown assistant"
    ])

print("Wake word system active...")

authenticated_user = None

while True:

    command = listen(prompt="Waiting for wake word (or type 'hello control')...")

    if not command:
        continue

    if should_exit(command):
        speak("Shutting down. Goodbye.")
        sys.exit()

    if "hello" not in command or "control" not in command:
        continue

    # 🔹 If already authenticated, skip login
    if authenticated_user:
        speak("Yes, I am here.")

    else:

        # 🔐 IDENTIFICATION STAGE
        speak("Who are you? Say I am followed by your name.(better if you type your username)")

        name_input = listen()

        if not name_input:
            speak("I did not hear your name.")
            continue

        if should_exit(name_input):
            speak("Shutting down. Goodbye.")
            sys.exit()

        if "i am" in name_input:
            spoken_name = name_input.split("i am", 1)[1].strip()
        else:
            spoken_name = name_input.strip()

        if not spoken_name:
            speak("I could not detect your name.")
            continue

        matches = fuzzy_match_user(spoken_name)

        if len(matches) == 0:
            speak("User not recognized. Would you like to register?")
            reg_choice = listen()
            if reg_choice and ("yes" in reg_choice or "register" in reg_choice):
                print("Registration mode triggered.")
                new_user = input("Enter new username: ").strip()
                if not new_user:
                    speak("Username cannot be empty. Registration aborted.")
                    continue
                
                success = create_user(new_user)
                if not success:
                    speak("User already exists or database error occurred.")
                    continue
                
                speak(f"User {new_user} created. Say, I want to use my face, or, I want to use a password.")
                method = listen()
                if method and "face" in method:
                    speak("Starting face registration.")
                    register_face(new_user)
                else:
                    speak("Please type your new password in the terminal.")
                    new_password = getpass.getpass("Create Password: ")
                    if new_password:
                        set_user_password(new_user, new_password)
                        speak("Password created successfully.")
                    else:
                        speak("Skipping password creation.")
                
                speak(f"Registration complete. Please log in again, {new_user}.")
            else:
                speak("Registration cancelled.")
            continue

        if len(matches) == 1:
            selected_user = matches[0]
            speak(f"I identified you as {selected_user}.")
        else:
            speak("I found multiple matches.")
            for i, user in enumerate(matches, start=1):
                speak(f"Option {i}: {user}")

            speak("Say, I choose option one, or, I choose option two.")

            selection = listen()

            if not selection:
                speak("No selection detected.")
                continue

            if should_exit(selection):
                speak("Shutting down. Goodbye.")
                sys.exit()

            if "one" in selection or "1" in selection:
                selected_user = matches[0]
            elif "two" in selection or "2" in selection:
                selected_user = matches[1]
            else:
                speak("Invalid selection.")
                continue

            speak(f"You selected {selected_user}.")

        # 🔐 AUTHENTICATION
        stored_hash = get_password_hash(selected_user)
        
        speak("Initiating face verification. Please look at the camera.")
        auth_success = False
        
        if verify_face(selected_user):
            auth_success = True
        else:
            speak("Face verification failed. Falling back to password.")
            if not stored_hash:
                speak("No password found. Please create a new password.")
                new_password = getpass.getpass("Create Password: ")
                if not new_password:
                    speak("Password cannot be empty.")
                    continue
                set_user_password(selected_user, new_password)
                speak("Password created successfully.")
                auth_success = True
            else:
                speak("Enter your password in the terminal.")
                password = getpass.getpass("Password: ")
                if verify_password(selected_user, password):
                    auth_success = True
                    
        if not auth_success:
            speak("Authentication failed.")
            continue

        # 🔐 AUTH SUCCESS
        switch_active_user(selected_user)
        authenticated_user = selected_user
        speak(f"Authentication successful. Welcome {selected_user}.")

    last_activity = time.time()

    # 🔹 SESSION LOOP
    while True:

        if time.time() - last_activity > TIMEOUT_SECONDS:
            print("Assistant sleeping. Say 'hello control' to wake.")
            break

        command = listen()

        if not command:
            continue

        last_activity = time.time()

        if should_exit(command):
            speak("Shutting down. Goodbye.")
            sys.exit()

        if "expand" in command:
            full = get_full_response()
            if full:
                speak(full)
            continue

        intent = detect_intent(command)
        response = route_intent(intent, command)

        if response:
            speak(response)
        else:
            reply = ask_ai(command)
            speak(reply)
```

---

## 2. `identity.py`
Handles user authentication, facial recognition using OpenCV and face_recognition, database interactions with MySQL, and password hashing with bcrypt.

```python
import os
import mysql.connector
import difflib
import bcrypt
import face_recognition
import cv2
import pickle
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=3306
    )


# ---------------- USERNAME LOGIC ----------------

def get_all_usernames():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]


def create_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        default_greeting = f"Hello, {username}!"
        cursor.execute(
            "INSERT INTO users (username, greeting) VALUES (%s, %s)", 
            (username, default_greeting)
        )
        conn.commit()
        success = True
    except mysql.connector.IntegrityError:
        success = False # User likely already exists
    except Exception as e:
        print(f"DB Error: {e}")
        success = False
    cursor.close()
    conn.close()
    return success


def fuzzy_match_user(spoken_name, threshold=0.4):
    usernames = get_all_usernames()
    matches = difflib.get_close_matches(
        spoken_name,
        usernames,
        n=3,
        cutoff=threshold
    )
    
    # Optional logic: if they gave a single word, automatically check if it's partly inside any username string
    if not matches and len(spoken_name.split()) == 1:
        for u in usernames:
            if spoken_name in u.lower():
                matches.append(u)
                
    return list(set(matches))


# ---------------- PASSWORD LOGIC ----------------

def get_password_hash(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = %s",
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result["password_hash"]


def verify_password(username, input_password):
    stored_hash = get_password_hash(username)
    if not stored_hash:
        return False
    return bcrypt.checkpw(
        input_password.encode(),
        stored_hash.encode()
    )


def set_user_password(username, plain_password):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(
        plain_password.encode(),
        bcrypt.gensalt()
    ).decode()
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE username = %s",
        (hashed, username)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


# ---------------- ACTIVE USER ----------------

def switch_active_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_default = FALSE WHERE id > 0")
    cursor.execute(
        "UPDATE users SET is_default = TRUE WHERE username = %s",
        (username,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


# ---------------- FACE REGISTRATION ----------------

def register_face(username):
    import time
    from src.anti_spoof import is_real_face
    video = cv2.VideoCapture(0)

    print("Look at the camera. Auto-capturing in 3 seconds...")
    start_time = time.time()
    attempts = 0

    while attempts < 3:
        ret, frame = video.read()
        if not ret:
            continue

        display_frame = frame.copy()
        
        elapsed = time.time() - start_time
        time_left = max(0, 3.0 - elapsed)
        
        if time_left > 0:
            cv2.putText(display_frame, f"Capturing in: {time_left:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.imshow("Face Registration", display_frame)
            cv2.waitKey(1)
            continue
            
        cv2.putText(display_frame, "Processing...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Face Registration", display_frame)
        cv2.waitKey(1)

        is_real = is_real_face(frame)

        if not is_real:
            print("Cannot register a spoofed face. Please try again.")
            attempts += 1
            start_time = time.time()
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_frame)

        if len(encodings) == 0:
            print("No face detected. Please try again.")
            attempts += 1
            start_time = time.time()
            continue

        face_encoding = encodings[0]

        serialized = pickle.dumps(face_encoding).hex()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET face_encoding = %s WHERE username = %s",
            (serialized, username)
        )
        conn.commit()
        cursor.close()
        conn.close()

        print("Face registered successfully.")
        break

    video.release()
    cv2.destroyAllWindows()


# ---------------- FACE VERIFICATION ----------------

def verify_face(username):
    from src.anti_spoof import is_real_face
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT face_encoding FROM users WHERE username = %s",
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result["face_encoding"]:
        return False

    stored_encoding = pickle.loads(
        bytes.fromhex(result["face_encoding"])
    )

    video = cv2.VideoCapture(0)
    print("Look at the camera for auto-verification in 3 seconds.")
    import time
    start_time = time.time()
    attempts = 0

    success = False

    while attempts < 3:
        ret, frame = video.read()
        if not ret:
            continue
            
        display_frame = frame.copy()
        
        elapsed = time.time() - start_time
        time_left = max(0, 3.0 - elapsed)
        
        if time_left > 0:
            cv2.putText(display_frame, f"Verifying in: {time_left:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow("Face Verification", display_frame)
            cv2.waitKey(1)
            continue
            
        cv2.putText(display_frame, "Processing...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Face Verification", display_frame)
        cv2.waitKey(1)

        is_real = is_real_face(frame)
        if not is_real:
            print("Spoofing Detected! Please try again.")
            attempts += 1
            start_time = time.time()
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_frame)

        if len(encodings) > 0:
            match = face_recognition.compare_faces(
                [stored_encoding],
                encodings[0]
            )

            if match[0]:
                success = True
                print("Face verified successfully.")
                break
            else:
                print("Face did not match. Please try again.")
                attempts += 1
                start_time = time.time()
                continue
        else:
            print("No face detected. Please try again.")
            attempts += 1
            start_time = time.time()
            continue

    video.release()
    cv2.destroyAllWindows()

    return success
```

---

## 3. `intent_detector.py`
Determines the user's intent by calling the LLM with the transcribed command. Returns general intent categories such as ask_time, ask_date, or general.

```python
from assistant import client


def detect_intent(command):

    prompt = f"""
    Classify the user intent into one of these categories:
    - ask_time
    - ask_date
    - general

    Only respond with the category name.
    User input: "{command}"
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip().lower()
```

---

## 4. `command_router.py`
Routes commands based on user intent, including functionality to start or close local processes and web browsers, as well as fetch current time or date.

```python
import os
from datetime import datetime

# 🔹 Application Configuration
APPS = {
    "chrome": {
        "open": "start chrome",
        "process": "chrome.exe"
    },
    "edge": {
        "open": "start msedge",
        "process": "msedge.exe"
    },
    "notepad": {
        "open": "start notepad",
        "process": "notepad.exe"
    },
    "calculator": {
        "open": "start calc",
        "process": "CalculatorApp.exe"
    },
    "youtube": {
        "open": "start msedge https://www.youtube.com",
        "process": "msedge.exe"
    },
    "whatsapp": {
        "open": "start msedge https://web.whatsapp.com",
        "process": "msedge.exe"
    },
    "antigravity": {
        "open": "start antigravity",
        "process": "antigravity.exe"
    },
    "chat gpt": {
        "open": "start msedge https://chat.openai.com",
        "process": "msedge.exe"
    },
    "gemini": {
        "open": "start msedge https://gemini.google.com",
        "process": "msedge.exe"
    },
    "claude": {
        "open": "start msedge https://claude.ai",
        "process": "msedge.exe"
    }
}


def route_intent(intent, command):

    command = command.strip().lower()

    # 🔹 OPEN / START APPLICATIONS
    for trigger in ["open ", "start "]:
        if command.startswith(trigger):
            app_name = command.replace(trigger, "").strip()

            if app_name in APPS:
                os.system(APPS[app_name]["open"])
                return f"Opening {app_name}."

            return "Application not recognized."

    # 🔹 CLOSE APPLICATIONS
    if command.startswith("close "):
        app_name = command.replace("close ", "").strip()

        if app_name in APPS:
            process_name = APPS[app_name]["process"]
            os.system(f"taskkill /IM {process_name} /F")
            return f"Closing {app_name}."

        return "Application not recognized."

    # 🔹 TIME
    if intent == "ask_time":
        return f"The current time is {datetime.now().strftime('%H:%M')}"

    # 🔹 DATE
    if intent == "ask_date":
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"

    return None
```

---

## 5. `assistant.py`
Interfaces directly with the Groq API utilizing Llama models to maintain conversational context and act as the core intelligent component of the application.

```python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

conversation_history = []
MAX_HISTORY = 6
last_full_response = ""


def ask_ai(user_input):
    global conversation_history, last_full_response

    conversation_history.append({"role": "user", "content": user_input})

    if len(conversation_history) > MAX_HISTORY * 2:
        conversation_history = conversation_history[-MAX_HISTORY * 2:]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history
    )

    full_reply = response.choices[0].message.content
    last_full_response = full_reply

    conversation_history.append(
        {"role": "assistant", "content": full_reply}
    )

    summary_prompt = f"""
    Summarize the following answer in 1-2 short sentences:

    {full_reply}
    """

    summary = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": summary_prompt}]
    )

    short_reply = summary.choices[0].message.content

    return short_reply


def get_full_response():
    return last_full_response


def reset_memory():
    global conversation_history, last_full_response
    conversation_history = []
    last_full_response = ""
```

---

## 6. `speech_to_text.py`
Captures audio input via the user's microphone and utilizes speech_recognition module with Google's speech recognition to return transcribed text(or similar library).

```python
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
```

---

## 7. `text_to_speech.py`
Converts text to speech using pyttsx3 or similar library, giving the assistant a voice.

```python
import asyncio
import edge_tts
import pygame
import os
import uuid
import time
import keyboard

VOICE = "en-US-AriaNeural"

pygame.mixer.init()


async def generate_audio(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)


def speak(text):

    print("Assistant:", text)

    filename = f"temp_{uuid.uuid4().hex}.mp3"

    asyncio.run(generate_audio(text, filename))

    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    # Wait until playback finishes
    while pygame.mixer.music.get_busy():
        if keyboard.is_pressed('space'):
            print("\n[Playback interrupted]")
            break
        pygame.time.Clock().tick(10)

    pygame.mixer.music.stop()

    # 🔹 IMPORTANT: release file handle
    pygame.mixer.music.unload()

    # Small delay to ensure Windows releases lock
    time.sleep(0.1)

    # Delete file safely
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            pass
```

---
