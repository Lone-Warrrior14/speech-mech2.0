import os
import zipfile
from flask import Flask, request, render_template, send_file
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROJECT_FOLDER = "generated_projects"

if not os.path.exists(PROJECT_FOLDER):
    os.makedirs(PROJECT_FOLDER)


def clean_code(code):

    code = code.replace("```python", "")
    code = code.replace("```", "")

    lines = code.split("\n")

    if len(lines) > 0 and lines[0].strip().lower() == "python":
        lines = lines[1:]

    return "\n".join(lines).strip()


def looks_like_code(text):

    keywords = ["import", "def", "class", "print(", "{", "}", ";"]

    for word in keywords:
        if word in text:
            return True

    return False


@app.route("/", methods=["GET", "POST"])
def home():

    files = []
    explanation = ""
    pip_commands = ""
    note = ""

    if request.method == "POST":

        user_input = request.form["code"]

        is_code = looks_like_code(user_input)

        if is_code:

            prompt = f"""
User pasted code that may contain errors.

Fix the code and return ONLY one corrected version.

Format

Corrected Code
<code>

Explanation
<simple explanation>

Debug Tips
<tips>

Rules
No markdown
No ``` symbols
Return only one corrected code

User Code
{user_input}
"""

        else:

            prompt = f"""
User asked for a programming solution.

If the user asks for a single file program, create only ONE file.
If the user asks for a project, create multiple files.

Return output EXACTLY in this format:

File: filename.py
<code>

File: another_file.py
<code>

Explanation
<short explanation>

Pip
<required pip packages only>

Note
<any additional instructions>

Rules
Code must appear only under File sections
Explanation must contain no code
Pip must contain only package names
Note must contain instructions only
Do not mix sections
Do not use markdown or ``` symbols

User Request
{user_input}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content

        try:

            if is_code:

                parts = result.split("Explanation")

                code_part = parts[0].replace("Corrected Code", "").strip()

                code = clean_code(code_part)

                if len(parts) > 1:
                    explanation = parts[1].split("Debug Tips")[0].strip()

                files.append(("corrected_code.py", code))

            else:

                file_section = result
                explanation = ""
                pip_commands = ""
                note = ""

                if "Explanation" in result:

                    parts = result.split("Explanation", 1)
                    file_section = parts[0]
                    remaining = parts[1]

                    if "Pip" in remaining:

                        parts2 = remaining.split("Pip", 1)
                        explanation = parts2[0].strip()
                        remaining2 = parts2[1]

                        if "Note" in remaining2:

                            parts3 = remaining2.split("Note", 1)
                            pip_commands = parts3[0].strip()
                            note = parts3[1].strip()

                        else:

                            pip_commands = remaining2.strip()

                    else:

                        explanation = remaining.strip()

                blocks = file_section.split("File:")

                for block in blocks:

                    block = block.strip()

                    if block == "":
                        continue

                    lines = block.split("\n", 1)

                    filename = lines[0].strip()

                    code = ""

                    if len(lines) > 1:
                        code = clean_code(lines[1])

                    filepath = os.path.join(PROJECT_FOLDER, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(code)

                    files.append((filename, code))

        except Exception as e:

            explanation = "Processing error: " + str(e)
            files = []

    return render_template(
        "index.html",
        files=files,
        explanation=explanation,
        pip_commands=pip_commands,
        note=note
    )


@app.route("/download")
def download():

    zip_path = os.path.join(PROJECT_FOLDER, "project.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:

        for file in os.listdir(PROJECT_FOLDER):

            if file.endswith(".zip"):
                continue

            full_path = os.path.join(PROJECT_FOLDER, file)

            zipf.write(full_path, file)

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)