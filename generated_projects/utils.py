import os

def get_filename_from_url(url):
    return url.split("/")[-1]

def get_file_size(filename):
    return os.path.getsize(filename)

def get_file_type(filename):
    return filename.split(".")[-1]