import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

conversation_history = []
MAX_HISTORY = 6
last_full_response = ""


def ask_ai(user_input):
    global conversation_history, last_full_response

    conversation_history.append({"role": "user", "content": user_input})

    if len(conversation_history) > MAX_HISTORY * 2:
        conversation_history = conversation_history[-MAX_HISTORY * 2:]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history
    )

    full_reply = response.choices[0].message.content
    last_full_response = full_reply

    conversation_history.append(
        {"role": "assistant", "content": full_reply}
    )

    try:
        summary_prompt = f"Summarize the following in 1-2 short sentences: {full_reply}"
        summary = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        short_reply = summary.choices[0].message.content
        return short_reply
    except Exception:
        # Fallback to full reply if summary fails
        return full_reply[:200] + "..." if len(full_reply) > 200 else full_reply



def get_full_response():
    return last_full_response


def reset_memory():
    global conversation_history, last_full_response
    conversation_history = []
    last_full_response = ""