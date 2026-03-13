import os

BASE_DIR = os.path.dirname(__file__)
MEDIA_FOLDER = os.path.join(BASE_DIR, "media", "movies")

VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov")


def get_movies():

    if not os.path.exists(MEDIA_FOLDER):
        os.makedirs(MEDIA_FOLDER)

    movies = []

    for file in os.listdir(MEDIA_FOLDER):

        if file.lower().endswith(VIDEO_EXT):

            movies.append(file)

    return movies