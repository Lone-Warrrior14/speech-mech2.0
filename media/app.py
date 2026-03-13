from flask import Flask, render_template, send_from_directory
from media_library import get_movies
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
MEDIA_FOLDER = os.path.join(BASE_DIR, "media", "movies")


@app.route("/")
def index():

    movies = get_movies()

    return render_template("index.html", movies=movies)


@app.route("/play/<filename>")
def play(filename):

    return send_from_directory(MEDIA_FOLDER, filename)


if __name__ == "__main__":

    app.run(port=5050, debug=True)