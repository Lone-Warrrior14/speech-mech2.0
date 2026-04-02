import requests

try:
    res = requests.post("http://127.0.0.1:5000/generate-image", json={"prompt": "a test image"})
    if res.status_code == 200:
        print("Success: Generated image")
        with open("test_gen.png", "wb") as f:
            f.write(res.content)
    else:
        print(f"Error: {res.status_code} - {res.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
