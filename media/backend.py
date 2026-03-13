import subprocess
import webbrowser
import sys
import os
import time

from media_library import get_movies
from input_handler import get_input


BASE_DIR = os.path.dirname(__file__)


def launch_web_player():

    player_path = os.path.join(BASE_DIR, "app.py")

    subprocess.Popen([sys.executable, player_path])

    time.sleep(2)

    webbrowser.open("http://127.0.0.1:5050")


def list_movies():

    movies = get_movies()

    if not movies:
        print("No movies found.")
        return []

    print("\nAvailable Movies\n")

    for i, movie in enumerate(movies, start=1):

        name = os.path.splitext(movie)[0]

        print(f"{i}. {name}")

    return movies


def play_movie(movie):

    url = f"http://127.0.0.1:5050/play/{movie}"

    webbrowser.open(url)


def entertainment_mode():

    print("\nEntertainment mode activated\n")

    launch_web_player()

    movies = list_movies()

    while True:

        command = get_input()

        if not command:
            continue

        if "exit control" in command or "stop assistant" in command or "shutdown assistant" in command:
            print("Shutting down. Goodbye.")
            sys.exit()

        if "exit" in command or "back" in command:
            print("Leaving entertainment mode\n")
            break

        # number selection

        if command.isdigit():

            index = int(command) - 1

            if 0 <= index < len(movies):

                play_movie(movies[index])

                continue

        # name selection

        for movie in movies:

            clean = os.path.splitext(movie)[0].lower()

            if clean in command:

                play_movie(movie)

                break