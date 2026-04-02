from flask import Flask, request, jsonify
import os
import sys
import threading
import time
from dotenv import load_dotenv

# Environment Initialization
# Up 3 levels from 'rag_system/RAG/rag_server.py' to reach project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

print(f"[BOOT] Neural Environment loaded from {ENV_PATH}")

# RAG Neural Link Initialization
RAG_PATH = os.path.dirname(os.path.abspath(__file__))
if RAG_PATH not in sys.path:
    sys.path.append(RAG_PATH)

def log_boot(msg):
    print(msg)
    with open(os.path.join(BASE_DIR, "rag_server_boot.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {msg}\n")

log_boot("[BOOT] Initializing RAG Neural Link...")

generate_answer = None
pick_and_read_files = None
insert_document = None

try:
    log_boot("[BOOT] Linking logic modules...")
    import rag_answer
    import universal_reader
    import insert_pinecone
    
    generate_answer = rag_answer.generate_answer
    pick_and_read_files = universal_reader.pick_and_read_files
    insert_document = insert_pinecone.insert_document
    log_boot("[SUCCESS] RAG Neural Core synchronized and online.")
except Exception as e:
    import traceback
    err = f"[CRITICAL] RAG Neural Core failure: {e}\n{traceback.format_exc()}"
    log_boot(err)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    status = "online" if generate_answer else "offline"
    return jsonify({
        "status": status,
        "modules": {
            "rag_answer": generate_answer is not None,
            "reader": pick_and_read_files is not None,
            "inserter": insert_document is not None
        }
    })

@app.route('/ask', methods=['POST'])
def ask():
    if not generate_answer:
        return jsonify({"answer": "RAG Neural Core is offline."})
    
    data = request.json
    prompt = data.get('prompt')
    namespace = data.get('namespace')
    history = data.get('history', [])
    
    # Extract folder from namespace for history persistence
    try:
        folder = namespace.split('_')[-1]
        # Assuming folder structure: RAG/users/user_X/folderName/chat_history.txt
        # We need user_id which should be passed or extracted
        user_id_part = namespace.split('_')[1]
        history_file = os.path.join(RAG_PATH, "users", f"user_{user_id_part}", folder, "chat_history.txt")
    except:
        history_file = None

    try:
        print(f"[RAG-SERVER] Processing query for namespace: {namespace}")
        answer = generate_answer(prompt, namespace, history)
        
        if history_file:
            try:
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                with open(history_file, "a", encoding="utf-8") as f:
                    f.write(f"USER: {prompt}\nAI: {answer}\n---\n")
            except: pass
            
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Execution Error: {str(e)}"})

@app.route('/upload', methods=['POST'])
def upload():
    if not pick_and_read_files:
        return jsonify({"success": False, "message": "Neural uplink offline."})
    
    data = request.json
    user_id = data.get('user_id')
    folder = data.get('folder')
    is_media = data.get('media', False)
    namespace = f"user_{user_id}_{folder}"
    
    target_dir = os.path.join(RAG_PATH, "users", f"user_{user_id}", folder)
    os.makedirs(target_dir, exist_ok=True)

    def run_upload():
        results = pick_and_read_files(media_only=is_media)
        if results:
            for path, text in results:
                # 1. Save as .txt in the workspace folder
                base_name = os.path.splitext(os.path.basename(path))[0]
                dest_txt_path = os.path.join(target_dir, f"{base_name}.txt")
                
                try:
                    with open(dest_txt_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"[RAG-SERVER] Saved extracted text: {dest_txt_path}")
                    
                    # 2. Delete the original source file (PDF/Docs/Audio)
                    if os.path.exists(path):
                        os.remove(path)
                        print(f"[RAG-SERVER] Original file purged: {path}")
                except Exception as e:
                    print(f"[RAG-SERVER] File conversion/purge error: {e}")

                # 3. Process with Pinecone
                insert_document(base_name, text, namespace)
            print(f"[RAG-SERVER] Neural Uplink and Cleanup complete for {namespace}")

    threading.Thread(target=run_upload).start()
    return jsonify({"success": True, "message": "Neural selection initiated"})

if __name__ == "__main__":
    app.run(port=5060, debug=True, use_reloader=False)
