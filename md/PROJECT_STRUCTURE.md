# 📂 Project Organizational Map v2.0

As of April 2026, the **SPEECH-MECH** project has undergone a complete reorganization into a **Task-Based Architecture** to improve maintainability, reduce filename collisions (e.g., `app.py`), and clarify module ownership.

---

## 🗃️ Folder Definitions

### 🔐 1. Authorization (`/authorization/`)
**Purpose**: Handles all user identity, authentication, and biometric security.
- **`identity.py`**: The core API for user data, password hashing (bcrypt), and face-matching logic.
- **`model/`**: Contains the liveness detection models (`anti_spoof_models`). 
- **`src/`**: Logic for anti-spoofing and face localization.

### 🎙️ 2. Speech Assistant (`/speech_assistant/`)
**Purpose**: The main AI logic and Voice UI components.
- **`assistant.py`**: Integration with LLMs (Groq) for conversational intelligence.
- **`intent_detector.py`**: Natural language understanding (NLU) for task routing.
- **`vosk-model/`**: Offline speech-to-text models.
- **`media/`**: Speech processing scripts (`speech_to_text.py`, `text_to_speech.py`).

### 🧠 3. RAG System (`/rag_system/`)
**Purpose**: Document intelligence and long-term memory retrieval.
- **`RAG/`**: The core retrieval logic, Pinecone integration, and document chunking.
- **`trace_rag.py`**: Debugging utility for neural retrieval.
- **`universal_reader.py`**: Cross-format (PDF, Docx, Audio) data extraction.

### 🌌 4. Image Generation (`/image gen/`)
**Purpose**: Unified backend for visual content creation.
- **`app.py`**: Flask backend providing the primary NVIDIA Flux and Cloudflare backup generation logic.
- **`templates/`**: Specialized UI for the image generation microservice.

### 🕸️ 5. Web System Infrastructure (`/launch_web_system/`)
**Purpose**: The central dashboard and server that links all modules.
- **`web_server.py`**: The main Flask entry point for the entire ecosystem.
- **`launch_web.py`**: The bootstrapper that starts RAG, Image Gen, and the Dashboard on separate ports.
- **`static/` & `templates/`**: Global assets and dashboard layouts.

---

## 🛠️ Unified Path Resolution

To allow cross-module imports (e.g., the Dashboard importing from Authorization), the `web_server.py` now uses **Dynamic Path Injection**:

```python
# From launch_web_system/web_server.py
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(base_dir)

sys.path.append(os.path.join(root_dir, 'authorization'))
sys.path.append(os.path.join(root_dir, 'speech_assistant'))
```

---

## 🗑️ Archive & Cleanup (`/unwanted/`)
Redundant files, legacy large binaries, and duplicate experiments have been moved here to keep the active production path clean. These are safe to delete once the system is fully verified.
