from fastapi import UploadFile
import numpy as np
import cv2
from keras.api.models import load_model
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
base_path = (BASE_DIR / "../ai_models").resolve()



class ImagePreprocessor:
    @staticmethod
    def preprocess(image: UploadFile):
        raw_data = np.frombuffer(image.file.read(), np.uint8)
        image = cv2.imdecode(raw_data, cv2.IMREAD_COLOR)
        image = cv2.resize(image, (224, 224))
        image = np.expand_dims(image, axis=0)
        return image



class BodyPartClassifier:
    def __init__(self):
        self.class_names = ['XR_ELBOW', 'XR_FINGER', 'XR_FOREARM', 'XR_HAND', 'XR_HUMERUS', 'XR_SHOULDER', 'XR_WRIST']

    @staticmethod
    @lru_cache(maxsize=2)
    def load_model_from_server():
        model = load_model( f"{base_path}/final_Mura_classification_model.h5")
        return model

    def predict(self, image):
        model = self.load_model_from_server()
        predictions = model.predict(image, verbose=0)
        class_index = int(np.argmax(predictions))
        confidence = float(predictions[0][class_index])
        body_part = self.class_names[class_index]
        return body_part, confidence

class FracturePredictor:
    @staticmethod
    @lru_cache(maxsize=10)
    def load_model_for_body_part(body_part: str):
        return load_model(f"{base_path}/ResNet50_{body_part}_frac.h5")

    def predict(self, image, body_part: str):
        model = self.load_model_for_body_part(body_part)
        prediction = model.predict(image, verbose=0)
        fracture_prob = float(prediction[0][0])
        label = "Fracture" if fracture_prob > 0.5 else "No Fracture"
        return label, fracture_prob