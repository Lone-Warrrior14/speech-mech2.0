from pinecone import Pinecone
from embed import get_embedding
import os
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("rag-index")


def search(query, top_k=5):

    embedding = get_embedding(query)

    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )

    matches = []

    for match in results["matches"]:
        matches.append(match["metadata"]["text"])

    return matches


if __name__ == "__main__":

    query = input("Ask a question: ")

    results = search(query)

    print("\nTop Results:\n")

    for i, r in enumerate(results):
        print(f"{i+1}. {r}\n")