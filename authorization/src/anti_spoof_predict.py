import torch
import cv2
import numpy as np


class AntiSpoofPredict:

    def __init__(self, device_id=0):

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        print("Anti-spoof running on:", self.device)

        self.models = {}

    def get_bbox(self, img):

        if img is None:
            return None

        import face_recognition
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_img)

        if not locations:
            return None

        # Return just the first face bounding box as [x, y, w, h]
        top, right, bottom, left = locations[0]
        return [left, top, right - left, bottom - top]

    def parse_model_name(self, model_name):

        name = model_name.replace(".pth", "")
        parts = name.split("_")

        scale = 1.0
        size = "80x80"

        try:
            scale = float(parts[0] + "." + parts[1])
        except:
            pass

        for p in parts:
            if "x" in p:
                size = p
                break

        h_input = int(size.split("x")[0])
        w_input = int(size.split("x")[1])

        model_type = "TorchScript"

        return h_input, w_input, model_type, scale

    def load_model(self, model_path):

        if model_path in self.models:
            return self.models[model_path]

        import os
        from src.model_lib.MiniFASNet import MiniFASNetV1SE, MiniFASNetV2

        model_name = os.path.basename(model_path)
        h_input, w_input, model_type, scale = self.parse_model_name(model_name)
        conv6_kernel = ((h_input + 15) // 16, (w_input + 15) // 16)
        
        if "MiniFASNetV1SE" in model_name:
            model = MiniFASNetV1SE(conv6_kernel=conv6_kernel)
        elif "MiniFASNetV2" in model_name:
            model = MiniFASNetV2(conv6_kernel=conv6_kernel)
        else:
            raise ValueError(f"Unknown architecture for model: {model_name}")

        state_dict = torch.load(model_path, map_location=self.device)
        stripped_state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
        model.load_state_dict(stripped_state_dict, strict=False)
        model = model.to(self.device)

        model.eval()

        self.models[model_path] = model

        return model

    def preprocess(self, img):

        img = cv2.resize(img, (80, 80))

        img = img.astype(np.float32)

        img = np.transpose(img, (2, 0, 1))

        img = np.expand_dims(img, axis=0)

        img = torch.from_numpy(img).float().to(self.device)

        return img

    def predict(self, img, model_path, model_type):

        img_tensor = self.preprocess(img)

        model = self.load_model(model_path)

        with torch.no_grad():

            result = model(img_tensor)

        return result.cpu().numpy()