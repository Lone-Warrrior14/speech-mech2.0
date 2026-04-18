from assistant import client

def detect_intent(command):
    prompt = f"""
    Classify the user intent into one of these categories:
    - ask_time
    - ask_date
    - identification (if the user says their name or who they are, e.g., "I am John", "My name is Alice")
    - navigation (if the user wants to navigate, open a module, select/create folders, or play media. e.g., "open rag", "select folder documents", "create folder research", "play Transformers", "go to dashboard")

    - image_gen (if the user wants to generate an image, e.g., "generate a cat", "create a picture of a dog", "make an image of ...")
    - general (if it's just a question or chat)

    Only respond with the category name.
    User input: "{command}"
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip().lower()