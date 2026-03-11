# Speech Mech Project Files

This document contains the source code for the key components of the Speech Mech application.

## 1. `identity.py`
Handles user authentication, facial recognition using OpenCV and `face_recognition`, database interactions with MySQL, and password hashing with `bcrypt`.

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


def fuzzy_match_user(spoken_name, threshold=0.7):
    usernames = get_all_usernames()
    matches = difflib.get_close_matches(
        spoken_name,
        usernames,
        n=3,
        cutoff=threshold
    )
    return matches


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
    video = cv2.VideoCapture(0)

    print("Look at the camera. Press 's' to capture face.")

    while True:
        ret, frame = video.read()
        if not ret:
            continue

        cv2.imshow("Face Registration", frame)

        if cv2.waitKey(1) & 0xFF == ord('s'):
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)

            if len(encodings) == 0:
                print("No face detected.")
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
    print("Look at the camera for verification.")

    success = False

    while True:
        ret, frame = video.read()
        if not ret:
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
                break

        cv2.imshow("Face Verification", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

    return success
```

---

## 2. `intent_detector.py`
Determines the user's intent by calling the LLM with the transcribed command. Returns general intent categories such as `ask_time`, `ask_date`, or `general`.

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

## 3. `command_router.py`
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

## 4. `assistant.py`
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

## 5. `speech_to_text.py`
Captures audio input via the user's microphone and utilizes `speech_recognition` module with Google's speech recognition to return transcribed text.

```python
import speech_recognition as sr

recognizer = sr.Recognizer()

def listen():

    with sr.Microphone(device_index=2) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print("You:", text)
            return text.lower()
        except:
            return None
```
