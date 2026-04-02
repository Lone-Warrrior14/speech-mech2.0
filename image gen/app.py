from flask import Flask, render_template, request, jsonify, send_file
import requests
import base64
import os
import io

from dotenv import load_dotenv

# Load environment from root .env
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

app = Flask(__name__)

# Primary: NVIDIA API Configuration (FLUX.2-KLEIN)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"

# Backup: Cloudflare Configuration
CLOUDFLARE_URL = "https://image.nehanabdullah540.workers.dev"

@app.route('/')
def index():
    # Renders the modern UI
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', "A beautiful landscape")
    
    # --- PRIMARY ATTEMPT (NVIDIA FLUX) ---
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }
    payload = {
        "prompt": prompt,
        "width": 1024,
        "height": 1024,
        "seed": 0,
        "steps": 4
    }

    try:
        print(f"[IMAGE GEN] Attempting NVIDIA generation for: {prompt}")
        response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_body = response.json()
        
        # Extract items from common NVIDIA response formats
        items = response_body.get("data") or response_body.get("artifacts") or []
        
        if items:
            b64_data = items[0].get("b64_json") or items[0].get("base64")
            if b64_data:
                print("[IMAGE GEN] NVIDIA generation success.")
                return jsonify({
                    "status": "success", 
                    "image_b64": b64_data, 
                    "source": "nvidia_flux"
                })
        print("[IMAGE GEN] NVIDIA returned no image data.")
    except Exception as e:
        print(f"[IMAGE GEN] NVIDIA generation failed/errored: {e}")

    # --- BACKUP ATTEMPT (CLOUDFLARE WORKER) ---
    try:
        print(f"[IMAGE GEN] Falling back to Cloudflare Backup for: {prompt}")
        # Automatically enhance the prompt for the backup generator
        enhanced_prompt = prompt + ", ultra realistic, 4k, detailed, cinematic lighting"
        
        res = requests.post(CLOUDFLARE_URL, json={
            "prompt": enhanced_prompt
        }, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Integrator/1.0"
        }, timeout=30)
        
        if res.status_code == 200:
            # Convert binary content to base64 for the frontend
            b64_data = base64.b64encode(res.content).decode('utf-8')
            print("[IMAGE GEN] Cloudflare backup generation success.")
            return jsonify({
                "status": "success", 
                "image_b64": b64_data, 
                "source": "cloudflare_backup"
            })
        else:
            print(f"[IMAGE GEN] Cloudflare backup failed with status {res.status_code}")
    except Exception as e:
        print(f"[IMAGE GEN] Cloudflare backup generation failed: {e}")

    # --- FINAL FAILURE ---
    return jsonify({
        "status": "error", 
        "message": "Both primary and backup image generation services are currently unavailable. Please try again later."
    }), 500

if __name__ == '__main__':
    print("[IMAGE GEN] Integrated System starting on Port 5000...")
    # Using 0.0.0.0 for accessibility, though local is usually fine
    app.run(debug=True, host="0.0.0.0", port=5000)
