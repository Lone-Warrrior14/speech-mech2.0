import os
import requests
import io
import base64
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"

print(f"Testing NVIDIA API Key: {NVIDIA_API_KEY[:10]}...")

prompt = "A futuristic city at night"
headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Accept": "application/json"}
payload = {"prompt": prompt, "width": 1024, "height": 1024, "seed": 0, "steps": 4}

try:
    res = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text[:500]}")
    if res.status_code == 200:
        print("Success!")
    else:
        print("Failed.")
except Exception as e:
    print(f"Error: {e}")
