import os
import sys

RAG_PATH = os.path.join(os.path.dirname(__file__), 'RAG')
if RAG_PATH not in sys.path:
    sys.path.append(RAG_PATH)

print(f"RAG_PATH: {RAG_PATH}")
print(f"sys.path: {sys.path}")

try:
    import rag_answer
    print("rag_answer import success")
    import universal_reader
    print("universal_reader import success")
    import insert_pinecone
    print("insert_pinecone import success")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
