import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov")

def get_azure_client():
    if not AZURE_CONNECTION_STRING:
        return None
    return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

def get_movies():
    """Fetches movies from Azure Blob Storage."""
    movies = []
    
    try:
        blob_service_client = get_azure_client()

        if blob_service_client and CONTAINER_NAME:
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            blobs = container_client.list_blobs(name_starts_with="movies/")
            for blob in blobs:
                if blob.name.lower().endswith(VIDEO_EXT):
                    url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob.name}"
                    movies.append({
                        "name": os.path.basename(blob.name),
                        "url": url,
                        "source": "cloud"
                    })
    except Exception as e:
        print(f"Cloud Link Stability Warning: {e}")
            
    return movies