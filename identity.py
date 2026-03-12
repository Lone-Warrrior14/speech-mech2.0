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


def get_all_users_with_ids():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username FROM users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_user_id(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result["id"]


def get_user_role(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result.get("role")


def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        success = True
    except Exception as e:
        print(f"DB Error: {e}")
        success = False
    cursor.close()
    conn.close()
    return success


def delete_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        success = True
    except Exception as e:
        print(f"DB Error: {e}")
        success = False
    cursor.close()
    conn.close()
    return success


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