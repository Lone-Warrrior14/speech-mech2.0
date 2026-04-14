import os
from dotenv import load_dotenv
from pinecone import Pinecone
from embed import get_embedding
from rag_chunker import chunk_text

# Environment Initialization
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("rag-index")

def insert_document(file_name, text, namespace):
    chunks = chunk_text(text)
    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        vectors.append({
            "id": f"{file_name}-{i}",
            "values": embedding,
            "metadata": {"text": chunk}
        })
    index.upsert(vectors, namespace=namespace)
    print(f"Inserted {len(vectors)} chunks into namespace: {namespace}")

if __name__ == "__main__":
    pass