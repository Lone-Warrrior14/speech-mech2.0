import os
import cv2
from dotenv import load_dotenv
from azure.ai.vision.face import FaceClient
from azure.core.credentials import AzureKeyCredential

load_dotenv(dotenv_path=".env")

ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT")
KEY = os.getenv("AZURE_FACE_KEY")

face_client = FaceClient(
    ENDPOINT,
    AzureKeyCredential(KEY)
)

camera = cv2.VideoCapture(0)

print("Look at the camera...")

ret, frame = camera.read()
camera.release()

if not ret:
    print("Camera error")
    exit()

_, img_encoded = cv2.imencode(".jpg", frame)
image_bytes = img_encoded.tobytes()

faces = face_client.detect(
    image_bytes,
    detection_model="detection_03",
    recognition_model="recognition_04",
    return_face_id=True
)

if faces:
    print("Face detected ✔")
    print("Face ID:", faces[0].face_id)
else:
    print("No face detected ❌")