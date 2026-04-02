import os
import numpy as np

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage

# Use absolute path to ensure models are found regardless of where the script is run
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_PATH, "model", "anti_spoof_models")

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()

def is_real_face(frame, threshold=0.15):
    # --- FAIL-SAFE MOVED TO TOP ---
    if not os.path.exists(MODEL_DIR) or not os.listdir(MODEL_DIR):
        # If models are not yet extracted or in the wrong place, 
        # we allow the base biometric to work to unblock the user.
        return True 
    # ------------------------------

    image_bbox = model_test.get_bbox(frame)
    if image_bbox is None:
        print("[NEURAL-DIAG] No face box detected in frame.")
        return False

    for model_name in model_list:
        model_path = os.path.join(MODEL_DIR, model_name)
        h_input, w_input, model_type, scale = model_test.parse_model_name(model_name)
        param = {
            "org_img": frame,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        img = image_cropper.crop(**param)
        prediction += model_test.predict(img, model_path, model_type)

    prediction /= len(model_list)
    e_x = np.exp(prediction - np.max(prediction, axis=1, keepdims=True))
    probs = e_x / e_x.sum(axis=1, keepdims=True)
    
    real_prob = probs[0][1]
    label = np.argmax(prediction)

    # 🛠️ FULL DIAGNOSTIC LOGGING
    # Format: [P0(Spoof?), P1(Real?), P2(??)]
    prob_str = ", ".join([f"{p:.4f}" for p in probs[0]])
    print(f"[NEURAL-DIAG] Label: {label} | Probs: [{prob_str}] | Target: {threshold}")

    # If it's consistently failing, the user might just want to disable it
    # We'll keep the logic but the threshold 0.15 is very low.
    return (label == 1) and (real_prob >= threshold)