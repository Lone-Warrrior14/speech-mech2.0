from pinecone import Pinecone
from embed import get_embedding
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("rag-index")

# Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def retrieve_chunks(query, top_k=5):

    embedding = get_embedding(query)

    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )

    chunks = [match["metadata"]["text"] for match in results["matches"]]

    return chunks


def generate_answer(query):

    chunks = retrieve_chunks(query)

    context = "\n\n".join(chunks)

    prompt = f"""
Use the following context to answer the question.

Context:
{context}

Question:
{query}

Answer clearly and concisely.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":

    query = input("Ask a question: ")

    answer = generate_answer(query)

    print("\nAnswer:\n")
    print(answer)