import os
import numpy as np

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage

MODEL_DIR = "./model/anti_spoof_models"

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()


def is_real_face(frame, threshold=0.8):

    image_bbox = model_test.get_bbox(frame)

    if image_bbox is None:
        return False

    prediction = np.zeros((1,3))

    model_list = os.listdir(MODEL_DIR)

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

    # Average the logits and convert to probabilities
    prediction /= len(model_list)
    e_x = np.exp(prediction - np.max(prediction, axis=1, keepdims=True))
    probs = e_x / e_x.sum(axis=1, keepdims=True)
    
    # In Silent-Face-Anti-Spoofing, Class 1 is 'Real Face'
    real_prob = probs[0][1]
    label = np.argmax(prediction)

    # Require it to be the highest scoring class AND exceed a strict probability threshold
    return (label == 1) and (real_prob >= threshold)