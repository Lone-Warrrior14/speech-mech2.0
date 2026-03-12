from pinecone import Pinecone
from embed import get_embedding
from RAG.chunk import chunk_text
import os
from dotenv import load_dotenv

load_dotenv()

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

    print("Inserted", len(vectors), "chunks into namespace:", namespace)


if __name__ == "__main__":
    pass