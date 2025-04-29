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
    def preprocess(image_bytes: bytes):
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        img = cv2.resize(img, (224, 224))
        img = np.expand_dims(img, axis=0)
        return img


class BodyPartClassifier:
    def __init__(self):
        self.class_names = ['ELBOW', 'FINGER', 'FOREARM', 'HAND', 'HUMERUS', 'SHOULDER', 'WRIST']
        self.model = self._load_model()

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model():
        return load_model(f"{base_path}/final_Mura_classification_model.h5")

    def predict(self, image):
        preds = self.model.predict(image, verbose=0)[0]
        idx = int(np.argmax(preds))
        return self.class_names[idx], float(preds[idx])


class FracturePredictor:
    @staticmethod
    @lru_cache(maxsize=7)
    def _load_model(body_part: str):
        return load_model(f"{base_path}/ResNet50_XR_{body_part}_frac.h5")

    def predict(self, image, body_part: str):
        model = self._load_model(body_part)
        prob = float(model.predict(image, verbose=0)[0][0])
        return ("Fracture" if prob > 0.5 else "No Fracture", prob)
