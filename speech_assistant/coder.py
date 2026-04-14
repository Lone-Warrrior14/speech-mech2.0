import os
import zipfile
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROJECT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated_projects")

if not os.path.exists(PROJECT_FOLDER):
    os.makedirs(PROJECT_FOLDER)

def clean_code(code):
    """Removes markdown markers and extra whitespace."""
    code = code.replace("```python", "")
    code = code.replace("```", "")
    lines = code.split("\n")
    if len(lines) > 0 and lines[0].strip().lower() == "python":
        lines = lines[1:]
    return "\n".join(lines).strip()

def looks_like_code(text):
    """Heuristic to check if input is code."""
    keywords = ["import", "def", "class", "print(", "{", "}", ";"]
    for word in keywords:
        if word in text:
            return True
    return False

def generate_code_solution(user_input):
    """
    Core logic for generating or fixing code using Groq.
    Returns (files, explanation, pip_commands, note)
    """
    is_code = looks_like_code(user_input)
    
    if is_code:
        prompt = f"""
User pasted code that may contain errors. Fix the code.
Return output in this format:

File: corrected_code.py
<code>

Rules:
1. Return ONLY the code. 
2. NO explanation, NO talk, NO markdown code blocks (```).
3. Ensure the code is complete and functional.

User Code:
{user_input}
"""
    else:
        prompt = f"""
You are an expert developer. Create a complete, high-quality solution for the user request.
Return output EXACTLY in this format for every file:

File: filename.py
<code>

Rules:
1. Provide ONLY the files and their code.
2. DO NOT provide any Explanation, Note, or Pip commands.
3. DO NOT use markdown or ``` markers.
4. Ensure all files mentioned are complete.

User Request:
{user_input}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content
    files = []
    explanation = ""
    pip_commands = ""
    note = ""

    try:
        # Split by "File:" to find all file blocks
        blocks = result.split("File:")
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            # First line is the filename, rest is code
            lines = block.split("\n", 1)
            filename = lines[0].strip()
            code = ""
            if len(lines) > 1:
                code = clean_code(lines[1])
            
            if filename:
                save_file(filename, code)
                files.append((filename, code))
    except Exception as e:
        files = []

    return files, "Synthesis Complete", "", ""

def save_file(filename, content):
    filepath = os.path.join(PROJECT_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def create_project_zip():
    zip_path = os.path.join(PROJECT_FOLDER, "project.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(PROJECT_FOLDER):
            if file.endswith(".zip"): continue
            full_path = os.path.join(PROJECT_FOLDER, file)
            zipf.write(full_path, file)
    return zip_path
