# Project Synopsis: SPEECH-MECH 2.0

---

## 📄 Front Page Details (Template)

**Project Synopsis for:** SPEECH-MECH 2.0  
**Candidate Name:** [Your Name Here]  
**Register No:** [Your Register Number]  
**Course Name:** [e.g., BCA / B.Sc CS]  
**Institute Name:** Yenepoya Institute of Arts, Science, Commerce and Management  
**Place:** Balmatta, Mangalore  
**Date:** April 2026  

**Under the Guidance of:**  
[Internal Guide Name]  
[Designation, Department]  

---

## 1. Title of the Project
**SPEECH-MECH 2.0: A Task-Based AI Command Hub with Biometric Security and Retrieval intelligence**

*The project is titled SPEECH-MECH 2.0 to reflect its evolution into a modular, task-oriented architecture. It serves as a unified ecosystem for conversational AI, document retrieval (RAG), and generative media, all secured by a biometric authorization layer.*

## 2. Statement of the Problem
In the current landscape of AI tools, users often have to switch between multiple platforms for different tasks (e.g., searching documents, generating images, and voice assistance). Furthermore, security is frequently overlooked in personal AI assistants, leaving sensitive local data vulnerable. 

**SPEECH-MECH 2.0** addresses these issues by:
- Eliminating fragmented workflows through a unified dashboard.
- Implementing a "Security-First" approach using face-matching and anti-spoofing (liveness detection).
- Resolving the dependency on constant high-speed internet for basic voice commands by using offline speech-to-text models.

## 3. Why this particular topic chosen?
This topic was selected because it represents the cutting edge of **Personal AI Ecosystems**. As AI becomes more integrated into daily life, there is a critical need for systems that are:
1. **Secure**: Biometrics ensure that the personal "Memory" (RAG) is only accessible to the owner.
2. **Modular**: The task-based architecture allows for easy insertion of new modules (like Image Generation or Home Automation) without breaking core logic.
3. **Efficient**: Using NLU (Natural Language Understanding) to detect "Intent" allows the system to route commands to specialized micro-services, ensuring high accuracy and performance.

## 4. Objective and Scope
### Objectives:
- **Biometric Authorization**: Develop a robust face-recognition gateway with 99%+ accuracy and liveness verification to prevent photo-spoofing.
- **Offline Speech Interaction**: Implement Vosk-based Speech-to-Text for near-instant command recognition without cloud latency.
- **Personal Knowledge Management**: Integrate a RAG (Retrieval-Augmented Generation) system using vector databases (Pinecone) to allow the assistant to "remember" and query private documents.
- **Generative Synergy**: Provide a seamless interface for Image Generation (NVIDIA Flux) as a secondary microservice.

### Scope:
The scope is limited to a local/private server deployment suitable for individual users or small office environments. It focuses on the integration of Speech, Vision, and Text LLMs into a single Flask-driven dashboard.

## 5. Methodology
The project follows a **Task-Based Agile Methodology**. The development is divided into four main sprints:
1. **Security Module**: Building the bcrypt-hashed identity database and MediaPipe-based face authentication.
2. **Core Assistant**: Implementing the Vosk/Groq pipeline for intent detection.
3. **Intelligence Layer**: Developing the Universal Reader and Pinecone retrieval logic for RAG.
4. **Unified Dashboard**: Using Flask to bridge all modules with a premium, glassmorphic UI.

## 6. Process Description
The system operates through four primary modules:
- **Authorization (`identity.py`)**: Uses a Siamese network approach for face-matching and liveness verification.
- **Speech Assistant (`assistant.py`)**: Captures audio, converts it to text via Vosk, and uses a Groq-powered LLM to detect the user's intent.
- **RAG System (`trace_rag.py`)**: Chunks documents using the Universal Reader and stores embeddings in Pinecone for context-aware answering.
- **Image Generation Microservice**: A separate Flask backend that interfaces with NVIDIA Flux and Cloudflare for visual content creation.

*The information flow is managed via a Central Dashboard (Web Server) that uses dynamic path resolution to interact with sub-modules.*

## 7. Resources and Limitations
### Hardware Requirements:
- **Webcam**: For biometric authentication.
- **Processor**: Intel i5/AMD Ryzen 5 (Minimum) for smooth real-time STT.
- **RAM**: 8GB (Minimum), 16GB (Recommended) to support multiple microservices.

### Software Requirements:
- **Language**: Python 3.10+
- **Framework**: Flask (Backend), Vanilla CSS/JS (Frontend)
- **AI Libraries**: MediaPipe, OpenCV, Vosk, Groq API, Pinecone-client.
- **Database**: SQLite (Local Auth), Pinecone (Vector Retrieval).

### Limitations:
- The system currently requires an active API key for high-level LLM reasoning (Groq).
- Real-time video processing during Auth may experience slight lag on systems without dedicated GPUs.

## 8. Testing Technologies used
- **Unit Testing**: Each module (`identity.py`, `assistant.py`) is tested independently for logical correctness.
- **Black-Box Testing**: Testing the system interface by providing various voice and image prompts to verify the output without internal logic checks.
- **System Integration Testing**: Ensuring that the `launch_web.py` bootstrapper successfully starts all microservices on their respective ports.
- **Biometric Stress Test**: Attempting to spoof the authentication system using high-resolution photos to validate the anti-spoofing logic.

## 9. Conclusion
SPEECH-MECH 2.0 is more than just a voice assistant; it is a comprehensive AI Operating System designed for privacy and productivity. By combining biometric gatekeeping with document intelligence (RAG), it provides a secure environment for users to interact with their data. Its modular design ensures that as AI technology evolves, the system can be expanded with minimal refactoring, making it a sustainable solution for the future of human-AI interaction.
