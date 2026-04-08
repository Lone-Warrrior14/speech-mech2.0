from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
import os
import sys
import json
import time
import subprocess
import webbrowser
import threading

# --- NEW PATH SYSTEM COMPATIBILITY ---
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(base_dir)
# Inject related task modules into path
sys.path.append(os.path.join(root_dir, 'authorization'))
sys.path.append(os.path.join(root_dir, 'speech_assistant'))
sys.path.append(os.path.join(root_dir, 'rag_system'))
# ------------------------------------

# Import project modules from task folders
try:
    from identity import (
        fuzzy_match_user, verify_password, switch_active_user, get_password_hash,
        set_user_password, create_user, register_face, verify_face,
        verify_face_from_frame, has_face, get_user_id, get_user_role, get_all_usernames
    )
    from speech_to_text import listen
    from text_to_speech import speak
    from assistant import ask_ai, get_full_response
    from intent_detector import detect_intent
    from command_router import route_intent
except ImportError as e:
    print(f"[CRITICAL] Failed to link neural modules across task folders: {e}")
    # Fallbacks or dummy functions would go here if needed

# RAG Neural Link Initialization (Redirected to rag_system)
RAG_BASE_PATH = os.path.join(root_dir, 'rag_system', 'RAG')
# RAG Intelligence is now handled on Port 5060.
print(f"[BOOT] RAG Proxy Channel initialized. Target: http://127.0.0.1:5060")

# Media/Entertainment Imports (Redirected to speech_assistant/media)
media_path = os.path.join(root_dir, 'speech_assistant', 'media')
sys.path.append(media_path)
try:
    from backend import entertainment_mode
except ImportError:
    entertainment_mode = None

import cv2
import base64
import numpy as np

camera = None

def decode_base64_image(image_data):
    if "base64," in image_data:
        image_data = image_data.split("base64,")[1]
    img_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            camera = cv2.VideoCapture(0)
    return camera

def release_camera():
    global camera
    if camera is not None:
        try:
            camera.release()
        except: pass
        camera = None

def gen_frames():
    try:
        while True:
            cap = get_camera()
            success, frame = cap.read()
            if not success:
                break
            # 🪞 Mirror for UX
            frame = cv2.flip(frame, 1)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        release_camera()

app = Flask(__name__)
app.secret_key = "speech_mech_secret_key"

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password')
        auth_type = data.get('type')

        if not username:
             return jsonify({"success": False, "message": "Identity string required"})

        print(f"[AUTH] Seeking identity: '{username}'")
        matches = fuzzy_match_user(username)
        if not matches:
            return jsonify({"success": False, "message": f"Identity '{username}' not found in Neural Database"})
        
        selected_user = matches[0]
        
        if auth_type == 'face_init':
            return jsonify({"success": True, "user": selected_user, "has_face": has_face(selected_user)})

        if auth_type == 'face_step':
            frame_b64 = data.get('frame')
            if frame_b64:
                print(f"[AUTH] Verifying Web-Camera biometric signature for {selected_user}...")
                frame = decode_base64_image(frame_b64)
                
                if frame is not None:
                    # Biometric Check
                    success = verify_face_from_frame(selected_user, frame)
                    if success:
                        session['user'] = selected_user
                        session['user_id'] = get_user_id(selected_user)
                        session['user_role'] = get_user_role(selected_user)
                        switch_active_user(selected_user)
                        return jsonify({"success": True})
                    return jsonify({"success": False, "message": "Biometric mismatch."})
                return jsonify({"success": False, "message": "Neural Core: Failed to decode visual signal."})

            cap = get_camera()
            attempts = 0
            max_attempts = 10
            matched = False
            
            print(f"[AUTH] Initiating biometric verification for {selected_user}...")
            
            while attempts < max_attempts and not matched:
                attempts += 1
                ret, frame = cap.read()
                if not ret: continue
                
                # Mirroring
                frame = cv2.flip(frame, 1)
                
                # 🧪 Diagnostic Liveness
                from src.anti_spoof import is_real_face
                is_real = is_real_face(frame)
                
                success = verify_face_from_frame(selected_user, frame)
                if success:
                    print(f"[AUTH] Biometric match confirmed on attempt {attempts}.")
                    session['user'] = selected_user
                    session['user_id'] = get_user_id(selected_user)
                    session['user_role'] = get_user_role(selected_user)
                    switch_active_user(selected_user)
                    matched = True
                    return jsonify({"success": True})
                
                time.sleep(0.1)

            if not matched:
                return jsonify({"success": False, "message": "Biometric signature mismatch or poor visibility."})

        if auth_type == 'password':
            if verify_password(selected_user, password):
                session['user'] = selected_user
                session['user_id'] = get_user_id(selected_user)
                session['user_role'] = get_user_role(selected_user)
                switch_active_user(selected_user)
                return jsonify({"success": True})
            return jsonify({"success": False, "message": "Invalid access string"})
        
        return jsonify({"success": False, "message": "Neural Protocol Mismatch"})
    except Exception as e:
        print(f"Neural Core Error: {e}")
        return jsonify({"success": False, "message": f"Core Connection Failure: {str(e)}"})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/rag')
def rag():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('rag.html', user=session['user'])

@app.route('/code_assist')
def code_assist():
    if 'user' not in session: return redirect(url_for('index'))
    code_assist_path = os.path.join(root_dir, "unwanted", "code_assists", "app.py")
    subprocess.Popen([sys.executable, code_assist_path], cwd=os.path.join(root_dir, "unwanted", "code_assists"))
    time.sleep(2)
    # Redirect to proxy if using ngrok, or local directly
    target_host = request.host.split(':')[0]
    if "ngrok" in request.host:
        return redirect("/proxy/5010/")
    return redirect(f"http://{target_host}:5010")

@app.route('/entertainment')
def entertainment():
    if 'user' not in session: return redirect(url_for('index'))
    if entertainment_mode:
        role = session.get('user_role', 'user')
        threading.Thread(target=entertainment_mode).start()
        time.sleep(2)
        target_host = request.host.split(':')[0]
        if "ngrok" in request.host:
             return redirect(f"/proxy/5050/?role={role}")
        return redirect(f"http://{target_host}:5050?role={role}")
    return "Entertainment module not available."

@app.route('/image_gen')
def image_gen():
    target_host = request.host.split(':')[0]
    if "ngrok" in request.host:
        return redirect("/proxy/5000/")
    return redirect(f"http://{target_host}:5000")

@app.route('/proxy/<int:port>/')
@app.route('/proxy/<int:port>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def service_proxy(port, path=""):
    import requests
    # Forward the request to the local sub-service
    local_url = f"http://127.0.0.1:{port}/{path}"
    if request.query_string:
        local_url += "?" + request.query_string.decode('utf-8')
    
    resp = requests.request(
        method=request.method,
        url=local_url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    content = resp.content
    if 'text/html' in resp.headers.get('Content-Type', ''):
        try:
            # Inject <base> tag to fix relative resource loading (CSS/JS/Images)
            # This is critical for ngrok tunnels on a single port.
            base_tag = f'<base href="/proxy/{port}/">'.encode('utf8')
            if b'<head>' in content:
                content = content.replace(b'<head>', b'<head>' + base_tag)
            elif b'<html>' in content:
                content = content.replace(b'<html>', b'<html>' + base_tag)
            else:
                content = base_tag + content
        except: pass

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    return Response(content, resp.status_code, headers)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    release_camera()
    return jsonify({"success": True})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if create_user(username):
        set_user_password(username, password)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "User already exists"})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({"success": False})
    data = request.json
    username = session['user']
    new_pass = data.get('password')
    if new_pass:
        set_user_password(username, new_pass)
        return jsonify({"success": True, "message": "Core password updated."})
    return jsonify({"success": False})

@app.route('/settings')
def settings_page():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('settings.html', user=session['user'])

@app.route('/register_face_direct', methods=['POST'])
def register_face_direct():
    if 'user' not in session: return jsonify({"success": False})
    username = session['user']
    data = request.json or {}
    frame_b64 = data.get('frame')

    import face_recognition
    import pickle
    import numpy as np
    from identity import get_connection
    from src.anti_spoof import is_real_face

    if frame_b64:
        frame = decode_base64_image(frame_b64)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 🔎 Enhanced Neural Detection (Upsampled)
        locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=2)
        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=locations)
        
        if len(encodings) > 0:
            if 'reg_epochs' not in session: session['reg_epochs'] = []
            
            # Store encoding to list in session
            epochs = session['reg_epochs']
            epochs.append(encodings[0].tolist())
            session['reg_epochs'] = epochs
            
            print(f"[AUTH] Web-Epoch {len(epochs)} synchronized for {username}.")
            
            if len(epochs) >= 3:
                # Average and save
                avg_encoding = np.mean(np.array(epochs), axis=0)
                serialized = pickle.dumps(avg_encoding).hex()
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET face_encoding = %s WHERE username = %s", (serialized, username))
                conn.commit()
                cursor.close()
                conn.close()
                session.pop('reg_epochs', None)
                print(f"[AUTH] Neural Master synchronized via Web-Camera.")
                return jsonify({"success": True, "done": True})
            
            return jsonify({"success": True, "done": False, "count": len(epochs)})
        return jsonify({"success": False, "message": "Face not detected in frame."})


    cap = get_camera()
    epochs = []
    attempts = 0
    max_attempts = 15 # Try to get 3 epochs within 15 frames (~5 seconds)
    
    print(f"[AUTH] Starting Neural Registration for {username} (3 Epochs required)")
    
    while len(epochs) < 3 and attempts < max_attempts:
        attempts += 1
        ret, frame = cap.read()
        if not ret: continue
        
        # Mirror for consistent processing
        frame = cv2.flip(frame, 1)
        
        # 🧪 Diagnostic Spoofing Check (Log but don't hard-block if it's the only issue)
        is_real = is_real_face(frame)
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 🔎 Enhanced Neural Detection (Upsampled)
        locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=2)
        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=locations)
        
        if len(encodings) > 0:
            print(f"[AUTH] Epoch {len(epochs)+1} synchronized. (Liveness: {is_real})")
            epochs.append(encodings[0])
            time.sleep(0.1) # Cooldown
        else:
            time.sleep(0.1)

    if len(epochs) >= 3:
        # Average the encodings for "Clear Output"
        avg_encoding = np.mean(epochs, axis=0)
        serialized = pickle.dumps(avg_encoding).hex()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET face_encoding = %s WHERE username = %s", (serialized, username))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[AUTH] Neural Master synchronized for {username}.")
        return jsonify({"success": True, "done": True})
    
    return jsonify({"success": False, "message": "Neural synchronization failed. Ensure face is clearly visible and well-lit."})

@app.route('/get_rag_folders')
def get_rag_folders_route():
    if 'user' not in session: return jsonify([])
    user_id = session['user_id']
    path = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}")
    os.makedirs(path, exist_ok=True)
    return jsonify([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])

@app.route('/get_rag_files', methods=['POST'])
def get_rag_files_route():
    if 'user' not in session: return jsonify([])
    user_id = session['user_id']
    folder = request.json.get('folder')
    path = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}", folder)
    if not os.path.exists(path): return jsonify([])
    # List all files in the folder
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return jsonify(files)

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    if 'user' not in session: return jsonify({"success": False})
    user_id = session['user_id']
    name = request.json.get('name')
    path = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}", name)
    os.makedirs(path, exist_ok=True)
    return jsonify({"success": True})

@app.route('/api/upload_docs', methods=['POST'])
def upload_docs():
    if 'user' not in session: return jsonify({"success": False})
    user_id = session['user_id']
    data = request.json
    folder = data.get('folder')
    is_media = data.get('media', False)
    
    import requests
    try:
        res = requests.post("http://127.0.0.1:5060/upload", json={
            "user_id": user_id,
            "folder": folder,
            "media": is_media
        })
        return jsonify(res.json())
    except:
        return jsonify({"success": False, "message": "RAG Intelligence is unreachable."})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    if 'user' not in session: return jsonify({"answer": "Authorization required."})
    data = request.json
    
    import requests
    # 🧪 Health Check Uplink
    try:
        health_check = requests.get("http://127.0.0.1:5060/health", timeout=2)
        if health_check.json().get("status") != "online":
            return jsonify({"answer": "RAG Neural Core is still initializing. Please wait 10 seconds..."})
    except:
        return jsonify({"answer": "RAG Intelligence Core is offline. Check if Port 5060 is active."})

    try:
        res = requests.post("http://127.0.0.1:5060/ask", json=data)
        return jsonify(res.json())
    except:
        return jsonify({"answer": "RAG Uplink Failure: The intelligence port refused the connection."})

@app.route('/api/get_chat_history', methods=['POST'])
def get_chat_history_route():
    if 'user' not in session: return jsonify([])
    folder = request.json.get('folder')
    user_id = session['user_id']
    history_file = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}", folder, "chat_history.txt")
    
    if not os.path.exists(history_file):
        return jsonify([])
    
    chats = []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            content = f.read()
            blocks = content.split('---')
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 2:
                    user_msg = lines[0].replace("USER: ", "").strip()
                    ai_msg = lines[1].replace("AI: ", "").strip()
                    chats.append({"user": user_msg, "ai": ai_msg})
    except: pass
    return jsonify(chats)

@app.route('/api/process_text_command', methods=['POST'])
def process_text_command():
    data = request.json
    command = data.get('command', '').strip()
    if not command: return jsonify({"response": "No input."})
    
    intent = detect_intent(command)
    
    # 👤 Identification (Neural Fill)
    if intent == "identification":
        matches = fuzzy_match_user(command)
        if matches: return jsonify({"response": "IDENT:" + matches[0]})
        return jsonify({"response": "User identity not found."})

    # 📁 RAG Folder Selection (select folder [name] OR select [name])
    low_cmd = command.lower()
    if "select folder" in low_cmd or low_cmd.startswith("select "):
        folder_target = low_cmd.replace("select folder", "").replace("select", "").strip()
        if 'user' in session and folder_target:
            import difflib
            user_id = session['user_id']
            path = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}")
            os.makedirs(path, exist_ok=True)
            existing_folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            
            if existing_folders:
                matches = difflib.get_close_matches(folder_target, existing_folders, n=1, cutoff=0.3)
                if matches:
                    best_match = matches[0]
                    return jsonify({"response": f"FOLDER_SELECT:{best_match}"})
            return jsonify({"response": f"Neural Link: Folder '{folder_target}' not found."})

    # 📁 RAG Folder Creation (+folder)
    
    # 📚 RAG Subject Creation (+subject)
    if command.startswith("+subject"):
        parts = command.replace("+subject", "").strip().split(None, 1)
        if len(parts) == 2 and 'user' in session:
            folder, subject = parts
            user_id = session['user_id']
            path = os.path.join(RAG_BASE_PATH, "users", f"user_{user_id}", folder, subject)
            os.makedirs(path, exist_ok=True)
            return jsonify({"response": f"Subject '{subject}' created in '{folder}'."})

    response = route_intent(intent, command)
    if not response:
        response = ask_ai(command)
    
    return jsonify({"response": response})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Listen on 0.0.0.0 for external access (ngrok)
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
