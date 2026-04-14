import os
from dotenv import load_dotenv
from pinecone import Pinecone
from embed import get_embedding
from groq import Groq

# Environment Initialization
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("rag-index")

# Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def retrieve_chunks(query, namespace, top_k=5):
    embedding = get_embedding(query)
    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )
    chunks = [match["metadata"]["text"] for match in results["matches"]]
    return chunks

def generate_answer(query, namespace, chat_history=None):
    if chat_history is None:
        chat_history = []
        
    # To help with queries like "what did he do?", include some history in the search query
    search_query = query
    if len(chat_history) > 0 and len(query.split()) < 6:
        last_turn = chat_history[-1]
        search_query = f"{last_turn.get('user', '')} {query}"
        
    chunks = retrieve_chunks(search_query, namespace)
    context = "\n\n".join(chunks)

    history_text = ""
    if chat_history:
        history_text = "Previous Conversation History:\n"
        for msg in chat_history[-3:]: # Keep last 3 turns
            history_text += f"User: {msg.get('user', '')}\nAssistant: {msg.get('ai', '')}\n"

    prompt = f"""
Use the following context to answer the question accurately.

Context:
{context}

{history_text}

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
    pass