from downloader import download_file
from utils import get_filename_from_url
from logger import log, log_error

def main():
    url = input("Enter the URL of the file to download: ")
    filename = input("Enter the filename to save as: ")
    if not filename:
        filename = get_filename_from_url(url)
    try:
        download_file(url, filename)
        log(f"File {filename} downloaded successfully")
    except Exception as e:
        log_error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()