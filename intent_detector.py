from assistant import client


def detect_intent(command):

    prompt = f"""
    Classify the user intent into one of these categories:
    - ask_time
    - ask_date
    - general

    Only respond with the category name.
    User input: "{command}"
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip().lower()