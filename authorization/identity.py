import os
import pyodbc
import difflib
import bcrypt
import face_recognition
import cv2
import pickle
from dotenv import load_dotenv

# Load environment from root .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def get_connection():
    az_server = os.getenv("az_server")
    az_database = os.getenv("az_database")
    az_username = os.getenv("az_username")
    az_password = os.getenv("az_password")
    
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={az_server};"
        f"DATABASE={az_database};"
        f"UID={az_username};"
        f"PWD={az_password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
        f"LoginTimeout=10;" # Support faster failure
    )
    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"[DB ERROR] Connectivity Failure: {e}")
        if "is not allowed to access the server" in str(e):
            print("[CRITICAL] Firewall Block Detected. Please allow your current IP in Azure portal.")
        return None



# ---------------- USERNAME LOGIC ----------------

def get_all_usernames():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]



def get_all_users_with_ids():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    rows = cursor.fetchall()
    
    result = [{"id": row.id, "username": row.username} for row in rows]
    
    cursor.close()
    conn.close()
    return result



def get_user_id(username):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result.id



def get_user_role(username):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result.role



def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
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
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
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
            "INSERT INTO users (username, greeting) VALUES (?, ?)", 
            (username, default_greeting)
        )
        conn.commit()
        success = True
    except Exception as e:
        # Check for unique constraint violation (username already exists)
        if "Violation of UNIQUE KEY constraint" in str(e) or "Cannot insert duplicate key" in str(e):
             success = False
        else:
            print(f"DB Error: {e}")
            success = False
    cursor.close()
    conn.close()
    return success


def fuzzy_match_user(spoken_name, threshold=0.4):
    if not spoken_name:
        return []
    
    usernames = get_all_usernames()
    spoken_name_lower = spoken_name.lower().strip()
    spoken_name_clean = "".join(spoken_name_lower.split())
    
    # 1. Exact or Case-Insensitive Match
    for u in usernames:
        if u.lower().strip() == spoken_name_lower:
            return [u]
            
    # 2. Whitespace-Agnostic Match (e.g. "LoneWarrior" matching "Lone Warrior")
    for u in usernames:
        u_clean = "".join(u.lower().split())
        if u_clean == spoken_name_clean:
            return [u]
            
    # 3. Fuzzy matching using difflib
    matches = difflib.get_close_matches(
        spoken_name,
        usernames,
        n=3,
        cutoff=threshold
    )
    
    # 4. Substring Match Falling Back
    if not matches:
        for u in usernames:
            if spoken_name_lower in u.lower() or u.lower() in spoken_name_lower:
                matches.append(u)
                
    return list(set(matches))


# ---------------- PASSWORD LOGIC ----------------

def get_password_hash(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        return None
    return result.password_hash


def verify_password(username, input_password):
    if not input_password:
        return False
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
        "UPDATE users SET password_hash = ? WHERE username = ?",
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
    # SQL Server uses 0 and 1 for bit/boolean columns usually, or bit literals.
    cursor.execute("UPDATE users SET is_default = 0")
    cursor.execute(
        "UPDATE users SET is_default = 1 WHERE username = ?",
        (username,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


# ---------------- FACE REGISTRATION ----------------

def register_face(username):
    import time
    import numpy as np
    from src.anti_spoof import is_real_face
    video = cv2.VideoCapture(0)

    print("Look at the camera. Auto-capturing starts in 3 seconds...")
    start_time = time.time()
    
    epochs_collected = []
    required_epochs = 3
    
    while len(epochs_collected) < required_epochs:
        ret, frame = video.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        elapsed = time.time() - start_time
        
        if elapsed < 3.0:
            time_left = 3.0 - elapsed
            cv2.putText(display_frame, f"Readying: {time_left:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.imshow("Multi-Epoch Neural Capturing", display_frame)
            cv2.waitKey(1)
            continue
            
        epoch_num = len(epochs_collected) + 1
        cv2.putText(display_frame, f"Capturing Epoch {epoch_num}/{required_epochs}...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Multi-Epoch Neural Capturing", display_frame)
        cv2.waitKey(1)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        
        # 🟢 MANUAL OVERRIDE (Press 'S' to force capture if spoofing check fails)
        manual_sync = (key == ord('s'))
        if manual_sync:
            print("[SYNC] Manual Neural Override Engaged.")

        # Liveness & Detection check
        is_real = is_real_face(frame)
        if is_real or manual_sync:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)
            
            if len(encodings) > 0:
                print(f"[EPOCH] Epoch {epoch_num} synchronized.")
                epochs_collected.append(encodings[0])
                time.sleep(0.5) # Longer cooldown for stability
            else:
                cv2.putText(display_frame, "FACE NOT DETECTED", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(display_frame, "NEURAL SIGNAL WEAK / ADJUST LIGHT", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(display_frame, "PRESS 'S' TO MANUALLY SYNC", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
        cv2.imshow("Multi-Epoch Neural Capturing", display_frame)

    if len(epochs_collected) == required_epochs:
        # Average the encodings for a "Clear Output"
        avg_encoding = np.mean(epochs_collected, axis=0)
        serialized = pickle.dumps(avg_encoding).hex()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET face_encoding = ? WHERE username = ?",
            (serialized, username)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("Neural Master Synchronization Complete. Face registered.")
    else:
        print("Registration Aborted.")

    video.release()
    cv2.destroyAllWindows()


# ---------------- FACE VERIFICATION ----------------

def has_face(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT face_encoding FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result or not result.face_encoding:
        return False
    return True

def verify_face(username, cap=None):
    from src.anti_spoof import is_real_face
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT face_encoding FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result.face_encoding: return False

    stored_encoding = pickle.loads(bytes.fromhex(result.face_encoding))
    
    created_cap = False
    if cap is None:
        cap = cv2.VideoCapture(0)
        created_cap = True

    print("Look at the camera. Neural Verification starts in 3 seconds...")
    import time
    start_time = time.time()
    
    success_epochs = 0
    required_epochs = 3
    
    while success_epochs < required_epochs:
        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        elapsed = time.time() - start_time
        
        if elapsed < 3.0:
            time_left = 3.0 - elapsed
            cv2.putText(display_frame, f"Synchronizing: {time_left:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow("Multi-Epoch Neural Uplink", display_frame)
            cv2.waitKey(1)
            continue
            
        cv2.putText(display_frame, f"Verifying Phase {success_epochs+1}/{required_epochs}...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Multi-Epoch Neural Uplink", display_frame)
        cv2.waitKey(1)

        if is_real_face(frame):
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)
            
            if len(encodings) > 0:
                match = face_recognition.compare_faces([stored_encoding], encodings[0])
                if match[0]:
                    success_epochs += 1
                    print(f"[VERIFY] Phase {success_epochs} Clear.")
                    time.sleep(0.1)
                else:
                    print("[VERIFY] Pattern Mismatch. Resetting...")
                    success_epochs = 0 # Optional: Reset or just continue
        
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        if time.time() - start_time > 15: break # 15s timeout

    if created_cap:
        cap.release()
        cv2.destroyAllWindows()

    return success_epochs == required_epochs

def verify_face_from_frame(username, frame):
    from src.anti_spoof import is_real_face
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT face_encoding FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result.face_encoding:
        return False

    stored_encoding = pickle.loads(bytes.fromhex(result.face_encoding))
    
    # Check liveness (Safety fallback if model missing)
    try:
        from src.anti_spoof import is_real_face
        if not is_real_face(frame):
            return False
    except (ImportError, Exception):
        pass

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_frame)

    if len(encodings) > 0:
        match = face_recognition.compare_faces([stored_encoding], encodings[0])
        return match[0]
    return False