from sentence_transformers import SentenceTransformer
import os

print("[EMBED] Loading SentenceTransformer (all-MiniLM-L6-v2)...")
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("[EMBED] Model loaded successfully.")
except Exception as e:
    print(f"[EMBED] CRITICAL: Model load failed: {e}")
    model = None

def get_embedding(text):
    if model is None:
        raise RuntimeError("Embedding model is not loaded. Neural Core is unstable.")
    return model.encode(text).tolist()