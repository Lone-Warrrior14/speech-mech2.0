import requests
import os

def download_file(url, filename):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024): 
                    file.write(chunk)
            print(f"File {filename} downloaded successfully")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    url = input("Enter the URL of the file to download: ")
    filename = input("Enter the filename to save as: ")
    if not filename:
        filename = url.split("/")[-1]
    download_file(url, filename)

if __name__ == "__main__":
    main()