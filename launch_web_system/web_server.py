from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, send_file, send_from_directory
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
sys.path.extend([
    os.path.join(root_dir, 'authorization'),
    os.path.join(root_dir, 'speech_assistant'),
    os.path.join(root_dir, 'rag_system'),
    os.path.join(root_dir, 'rag_system', 'RAG'),
    os.path.join(root_dir, 'speech_assistant', 'media'),
    os.path.join(root_dir, 'image_gen')
])

from azure.storage.blob import BlobServiceClient
# ------------------------------------

# Import project modules from task folders
# --- CORE UTILITIES ---
try:
    import requests
    import io
    import base64
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root_dir, ".env"))
except ImportError as e:
    print(f"[CRITICAL] Core requirements missing (requests/dotenv): {e}")

# --- NEURAL MODULES ---
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
    import coder 
except ImportError as e:
    print(f"[WARN] Identification or Voice modules failed to link: {e}")

# --- MEDIA SYSTEM ---
try:
    from media_library import get_movies
except ImportError as e:
    print(f"[WARN] Media Library failed to link: {e}")
    def get_movies():
        print("[ERROR] get_movies is using empty fallback due to import failure.")
        return []

# --- RAG INTELLIGENCE ---
rag_answer = None
universal_reader = None
insert_pinecone = None

try: import rag_answer
except Exception as e: print(f"[WARN] RAG: rag_answer failed: {e}")

try: import universal_reader
except Exception as e: print(f"[WARN] RAG: universal_reader failed: {e}")

try: import insert_pinecone
except Exception as e: print(f"[WARN] RAG: insert_pinecone failed: {e}")

if not all([rag_answer, universal_reader, insert_pinecone]):
    print("[WARN] RAG Intelligence modules are incomplete. Neural links may be unstable.")


# Consolidated Configuration
RAG_PATH = os.path.join(root_dir, 'rag_system', 'RAG')
MEDIA_FOLDER = os.path.join(root_dir, "speech_assistant", "media", "media", "movies")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"
CLOUDFLARE_URL = "https://image.nehanabdullah540.workers.dev"

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

if AZURE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
else:
    print("[WARN] Azure Connection String missing in Neural Environment.")

print(f"[BOOT] Neural Core Unified. Port 8000 is now the primary nexus.")

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

@app.route('/entertainment')
def entertainment_route():
    if 'user' not in session: return redirect(url_for('index'))
    movies = get_movies()
    role = session.get('user_role', 'user')
    return render_template('media_box.html', user=session['user'], movies=movies, role=role)

@app.route('/image_gen')
def image_gen_route():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('image_gen.html', user=session['user'])

@app.route('/play/<filename>')
def play_media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

@app.route('/api/upload_media', methods=['POST'])
def upload_media_api():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        blob_name = f"movies/{file.filename}"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file, overwrite=True)
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Azure Upload Failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate-image', methods=['POST'])
def generate_image_api():
    data = request.json
    prompt = data.get('prompt', "A beautiful landscape")
    headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Accept": "application/json"}
    payload = {"prompt": prompt, "width": 1024, "height": 1024, "seed": 0, "steps": 4}
    try:
        res = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        items = res.json().get("data") or res.json().get("artifacts") or []
        if items:
            b64_data = items[0].get("b64_json") or items[0].get("base64")
            if b64_data:
                return send_file(io.BytesIO(base64.b64decode(b64_data)), mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] NVIDIA Gen-Image failed: {e}")
    try:
        print(f"[IMAGE GEN] Falling back to Cloudflare Backup for: {prompt}")
        enhanced_prompt = prompt + ", ultra realistic, 4k, detailed, cinematic lighting"
        res = requests.post(CLOUDFLARE_URL, json={"prompt": enhanced_prompt}, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Integrator/1.0"}, timeout=30)
        if res.status_code == 200:
            return send_file(io.BytesIO(res.content), mimetype='image/png')
        else:
            print(f"[ERROR] Cloudflare Gen-Image failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERROR] Cloudflare Gen-Image failed: {e}")
    return jsonify({"error": "Neural generation failed."}), 500

@app.route('/code_assist')
def code_assist():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('code_assist.html', user=session['user'])

@app.route('/api/ask_coder', methods=['POST'])
def api_ask_coder():
    if 'user' not in session: return jsonify({"answer": "Neural Authorization Required."})
    try:
        data = request.json
        user_prompt = data.get("prompt", "")
        if not user_prompt:
            return jsonify({"answer": "Neural signal void."})

        files, explanation, pip, note = coder.generate_code_solution(user_prompt)
        
        # Format the response for the UI
        response_text = f"**Neural Synthesis Complete.**\n\n{explanation}\n\n"
        if pip:
            response_text += f"\n**Requirements:** `pip install {pip}`\n"
        if note:
            response_text += f"\n**Setup Note:** {note}\n"
        
        return jsonify({
            "answer": response_text,
            "files": files,
            "success": True
        })
    except Exception as e:
        return jsonify({"answer": f"Core Fault: {str(e)}", "success": False})

@app.route('/download_coder_project')
def download_coder_project():
    if 'user' not in session: return redirect(url_for('index'))
    zip_path = coder.create_project_zip()
    return send_file(zip_path, as_attachment=True)

# Standard Service Proxy with Base Tag Injection (Sync with Mech 2)
@app.route('/proxy/<int:port>/')
@app.route('/proxy/<int:port>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def service_proxy(port, path=""):
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
                cursor.execute("UPDATE users SET face_encoding = ? WHERE username = ?", (serialized, username))
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
        cursor.execute("UPDATE users SET face_encoding = ? WHERE username = ?", (serialized, username))
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
    prefix = f"rag/user_{user_id}/"
    
    try:
        blobs = container_client.list_blobs(name_starts_with=prefix)
        folders = set()
        for blob in blobs:
            # rag/user_1/my_folder/file.txt -> my_folder
            parts = blob.name[len(prefix):].split('/')
            if len(parts) > 0 and parts[0]:
                folders.add(parts[0])
        return jsonify(list(folders))
    except Exception as e:
        print(f"[ERROR] Azure RAG List Folders Failed: {e}")
        return jsonify([])

@app.route('/get_rag_files', methods=['POST'])
def get_rag_files_route():
    if 'user' not in session: return jsonify([])
    user_id = session['user_id']
    folder = request.json.get('folder')
    prefix = f"rag/user_{user_id}/{folder}/"
    
    try:
        blobs = container_client.list_blobs(name_starts_with=prefix)
        files = []
        for blob in blobs:
            filename = os.path.basename(blob.name)
            if filename:
                files.append(filename)
        return jsonify(files)
    except Exception as e:
        print(f"[ERROR] Azure RAG List Files Failed: {e}")
        return jsonify([])

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    if 'user' not in session: return jsonify({"success": False})
    user_id = session['user_id']
    name = request.json.get('name')
    # Create a dummy blob to simulate folder creation in Azure
    blob_name = f"rag/user_{user_id}/{name}/.keep"
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(b"", overwrite=True)
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Azure RAG Create Folder Failed: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/upload_docs', methods=['POST'])
def upload_docs():
    if 'user' not in session: return jsonify({"success": False})
    user_id = session['user_id']
    
    # Get metadata from form instead of json since we use FormData
    folder = request.form.get('folder')
    is_media = request.form.get('media') == 'true'
    
    if 'files' not in request.files:
        return jsonify({"success": False, "error": "No files"}), 400

    files = request.files.getlist('files')
    temp_dir = os.path.join(root_dir, "temp_rag", f"user_{user_id}")
    os.makedirs(temp_dir, exist_ok=True)

    # Save files locally BEFORE starting the thread to avoid 'read of closed file'
    local_paths = []
    for file in files:
        if not file.filename: continue
        lp = os.path.join(temp_dir, file.filename)
        file.save(lp)
        local_paths.append(lp)

    # Process synchronously to keep the UI loading screen active as requested
    def run_process(paths):
        namespace = f"user_{user_id}_{folder}"
        results_summary = []
        for local_path in paths:
            filename = os.path.basename(local_path)
            try:
                if not insert_pinecone:
                    print(f"[RAG-ERROR] insert_pinecone module is offline. Cannot process {filename}.")
                    results_summary.append({"file": filename, "success": False, "error": "Module Offline"})
                    continue

                # 1. Upload to Azure
                blob_name = f"rag/user_{user_id}/{folder}/{filename}"
                blob_client = container_client.get_blob_client(blob_name)
                with open(local_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)

                # 2. Process for RAG
                print(f"[RAG] Extracting intelligence from: {filename}")
                text = universal_reader.read_file(local_path)
                if text:
                    insert_pinecone.insert_document(filename, text, namespace)
                    print(f"[RAG] Neural Link Successful: {filename}")
                    results_summary.append({"file": filename, "success": True})
                else:
                    results_summary.append({"file": filename, "success": False, "error": "No text extracted"})
                
            except Exception as e:
                print(f"[RAG-ERROR] Failed to process {filename}: {e}")
                results_summary.append({"file": filename, "success": False, "error": str(e)})
            finally:
                # 3. Cleanup
                if os.path.exists(local_path):
                    os.remove(local_path)
        return results_summary

    status_report = run_process(local_paths)
    return jsonify({"success": True, "message": "Neural synchronization complete", "report": status_report})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    if 'user' not in session: return jsonify({"answer": "Authorization required."})
    data = request.json
    prompt = data.get('prompt')
    folder = data.get('folder') # Unified: Frontend sends folder
    user_id = session['user_id']
    namespace = f"user_{user_id}_{folder}"
    history = data.get('history', [])
    
    try:
        answer = rag_answer.generate_answer(prompt, namespace, history)
        
        # Stateless History Persistence (Azure)
        try:
            history_blob = f"rag/user_{user_id}/{folder}/chat_history.json"
            
            # Read current history
            current_history = []
            try:
                hb_client = container_client.get_blob_client(history_blob)
                if hb_client.exists():
                    data = hb_client.download_blob().readall()
                    current_history = json.loads(data)
            except: pass
            
            # Append new turn
            current_history.append({"user": prompt, "ai": answer})
            # Keep last 10 for storage efficiency if needed, but for now just save
            hb_client = container_client.get_blob_client(history_blob)
            hb_client.upload_blob(json.dumps(current_history), overwrite=True)
        except Exception as he:
            print(f"[ERROR] Syncing chat history to Azure failed: {he}")

        return jsonify({"answer": answer})
    except Exception as e:
        print(f"[ERROR] API Ask Failed: {e}")
        return jsonify({"answer": f"Neural Core Fault: {str(e)}"})

@app.route('/api/get_chat_history', methods=['POST'])
def get_chat_history_route():
    if 'user' not in session: return jsonify([])
    folder = request.json.get('folder')
    user_id = session['user_id']
    
    history_blob = f"rag/user_{user_id}/{folder}/chat_history.json"
    
    try:
        hb_client = container_client.get_blob_client(history_blob)
        if hb_client.exists():
            data = hb_client.download_blob().readall()
            chats = json.loads(data)
            return jsonify(chats)
    except Exception as e:
        print(f"[ERROR] Getting chat history from Azure: {e}")
    
    return jsonify([])

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

    # 📁 RAG Folder Creation (+folder or "create new")
    if low_cmd.startswith("+folder") or low_cmd.startswith("create new"):
        folder_name = low_cmd.replace("+folder", "").replace("create new", "").strip()
        if 'user' in session and folder_name:
            user_id = session['user_id']
            # We already have a create_folder function logic, but here we do it via command
            blob_name = f"rag/user_{user_id}/{folder_name}/.keep"
            try:
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(b"", overwrite=True)
                return jsonify({"response": f"Neural Link: Folder '{folder_name}' created successfully."})
            except Exception as e:
                return jsonify({"response": f"Neural Core Fault: {str(e)}"})

    # 📁 RAG Folder Selection (select folder [name] OR select [name])
    if "select folder" in low_cmd or low_cmd.startswith("select "):
        folder_target = low_cmd.replace("select folder", "").replace("select", "").strip()
        if 'user' in session and folder_target:
            import difflib
            user_id = session['user_id']
            # Fetch existing folders from Azure to match
            prefix = f"rag/user_{user_id}/"
            try:
                blobs = container_client.list_blobs(name_starts_with=prefix)
                folders = set()
                for b in blobs:
                    parts = b.name[len(prefix):].split('/')
                    if len(parts) > 0 and parts[0]: folders.add(parts[0])
                
                if folders:
                    matches = difflib.get_close_matches(folder_target, list(folders), n=1, cutoff=0.3)
                    if matches:
                        return jsonify({"response": f"FOLDER_SELECT:{matches[0]}"})
            except: pass
            return jsonify({"response": f"Neural Link: Folder '{folder_target}' not found."})

    # 📁 RAG Folder Creation (+folder)
    
    # 📚 RAG Subject Creation (+subject)
    if command.startswith("+subject"):
        parts = command.replace("+subject", "").strip().split(None, 1)
        if len(parts) == 2 and 'user' in session:
            folder, subject = parts
            user_id = session['user_id']
            path = os.path.join(RAG_PATH, "users", f"user_{user_id}", folder, subject)
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
