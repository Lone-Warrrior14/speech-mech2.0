from flask import Flask, render_template, send_from_directory, request, jsonify
from media_library import get_movies
import os
import tkinter as tk
from tkinter import filedialog
import shutil
import threading

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
MEDIA_FOLDER = os.path.join(BASE_DIR, "media", "movies")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

@app.route("/")
def index():
    movies = get_movies()
    role = request.args.get('role', 'user')
    return render_template("index.html", movies=movies, role=role)

@app.route("/play/<filename>")
def play(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

@app.route("/api/upload_media", methods=['POST'])
def upload_media():
    def pick_media():
        try:
            root = tk.Tk()
            root.withdraw()
            root.update()
            root.lift()
            root.attributes('-topmost', True)
            root.focus_force()
            
            file_paths = filedialog.askopenfilenames(
                title="Select Media Files",
                filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.wmv")]
            )
            
            if file_paths:
                for path in file_paths:
                    dest = os.path.join(MEDIA_FOLDER, os.path.basename(path))
                    shutil.copy(path, dest)
                print(f"Uploaded {len(file_paths)} media files.")
            root.destroy()
        except Exception as e:
            print(f"Media Upload Error: {e}")

    threading.Thread(target=pick_media).start()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(port=5050, debug=True)