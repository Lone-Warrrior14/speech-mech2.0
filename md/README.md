# 🪐 SPEECH-MECH NEURAL ECOSYSTEM v2.0

![Speech Mech Banner](https://img.shields.io/badge/Status-Restructured-brightgreen?style=for-the-badge) ![Python Version](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge) ![Architecture](https://img.shields.io/badge/Architecture-Task--Based-blueviolet?style=for-the-badge)

A powerful, unified AI ecosystem featuring **Biometric Access**, **RAG Intelligence**, **Autonomous Image Generation**, and a **Neural Voice Assistant**.

---

## 🏗️ Neural Architecture (New Restructured v2.0)

The project has been reorganized into task-specialized modules to ensure scalability and cross-platform compatibility.

```bash
📂 SPEECH_MECH/
├── 📁 authorization/      # Biometric (Face ID) & Identity Management
├── 📁 speech_assistant/   # Core Voice UI & Autonomous Logic
├── 📁 rag_system/         # Long-term Memory & Document Intelligence (Pinecone)
├── 📁 image gen/          # Primary (NVIDIA Flux) & Backup Image Generation
├── 📁 launch_web_system/  # Central Web Dashboard & API Infrastructure
├── 📄 run.py              # Unified System Launcher (One-Click Start)
└── 📄 .env                # Global Environment Variables
```

---

## 🚀 Key Features

### 🔐 Biometric Neural Unlock
*   **Face-ID Integration**: Multi-epoch neural capturing for user registration.
*   **Anti-Spoofing Protocol**: Real-time liveness detection powered by MiniFASNet.
*   **Encrypted Identities**: Secure hashing for password fallbacks using bcrypt.

### 🧠 RAG Intelligence Core
*   **Pinecone Hybrid Search**: Vectorized document retrieval for contextual precision.
*   **Universal Reader**: Auto-extraction from PDF, Audio/Speech, and Text files.
*   **Persistent Context**: Per-user workspace memory.

### 🖼️ Integrated Image Generator
*   **Dual-Uplink System**: NVIDIA Flux (Primary) + Cloudflare Workers (Backup).
*   **Automatic Enhancement**: Prompt engineering layer for ultra-realistic rendering.
*   **Unified API**: Managed through the central dashboard.

---

## ⚡ Quick Start

### 1. Prerequisites 🛠️
Ensure you have **Python 3.10+** and **MySQL** installed.

### 2. Neural Environment (.env) 🌐
Create a `.env` file in the project root with the following keys:
- `GROQ_API_KEY`: For Conversational Intelligence.
- `NVIDIA_API_KEY`: For Primary High-End Image Generation.
- `PINECONE_API_KEY`: For RAG Vector Memory.
- `DB_USER`, `DB_PASSWORD`: Your local MySQL credentials.

### 3. Execution 🚀
Launch the entire system from the root folder:
```bash
python run.py
```
*The system will automatically clear ports, synchronize neural links, and open your browser to the Dashboard (Port 8000).*

---

## 📱 Mobile Access (Secure Context)
To use the Biometric/Microphone features on your phone, you must provide a secure context (HTTPS). 
Use **ngrok** to create a tunnel:
```bash
ngrok http 8000
```

---

## 🛠️ Developed by
**Lone-Warrior14** | Restructured and Unified by **Antigravity AI**.
