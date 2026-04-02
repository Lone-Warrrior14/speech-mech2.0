from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import requests
import io
import os

app = Flask(__name__)
CORS(app)

CLOUDFLARE_URL = "https://image.nehanabdullah540.workers.dev"

# Read the template file or use a string
def get_template():
    # Ensure we look in the correct directory relative to the script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "index.html")
    
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"[IMAGE GEN] Template not found at: {template_path}")
    return "<h1>UI Template Missing</h1>"

@app.route("/")
def home():
    return get_template()

@app.route("/generate-image", methods=["POST"])
def generate_image():
    try:
        data = request.json
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "Prompt required"}), 400

        print(f"[IMAGE GEN] Generating for prompt: {prompt}")

        # Improve prompt quality automatically
        enhanced_prompt = prompt + ", ultra realistic, 4k, detailed, cinematic lighting"

        try:
            res = requests.post(CLOUDFLARE_URL, json={
                "prompt": enhanced_prompt
            }, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }, timeout=30)
            
            if res.status_code != 200:
                print(f"[IMAGE GEN] Worker Error: Status {res.status_code}")
                print(f"[IMAGE GEN] Worker Response: {res.text}")
                return jsonify({"error": f"Worker returned status {res.status_code}"}), 500

            print(f"[IMAGE GEN] Success: Generated {len(res.content)} bytes")
            return send_file(
                io.BytesIO(res.content),
                mimetype='image/png'
            )
        except requests.exceptions.Timeout:
            print("[IMAGE GEN] Error: Worker selection timed out.")
            return jsonify({"error": "Request to neural worker timed out."}), 504
        except Exception as e:
            print(f"[IMAGE GEN] Request Exception: {e}")
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"[IMAGE GEN] Core Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("[IMAGE GEN] Neural Visualizer starting on Port 5000...")
    app.run(host="0.0.0.0", port=5000)