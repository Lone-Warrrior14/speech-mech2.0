from flask import Flask, render_template, request, jsonify
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

# Load env
load_dotenv()

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

if not AZURE_CONNECTION_STRING:
    raise ValueError("Missing Azure connection string in .env")

from media_library import get_movies

app = Flask(__name__)

# Azure client (needed for upload)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


# 🏠 Home
@app.route("/")
def index():
    role = request.args.get("role", "user")
    movies = get_movies()
    return render_template("index.html", movies=movies, role=role)


# 📤 Upload API (Admin only)
@app.route("/api/upload_media", methods=["POST"])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']

    blob_name = f"movies/{file.filename}"

    blob_client = container_client.get_blob_client(blob_name)

    blob_client.upload_blob(file, overwrite=True)

    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)