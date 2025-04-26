from fastapi import UploadFile
import numpy as np
import cv2
import asyncio
from keras.api.models import load_model
from functools import lru_cache
from pathlib import Path

# Define base directory for models
BASE_DIR = Path(__file__).resolve().parent
base_path = (BASE_DIR / "../ai_models").resolve()



class ImagePreprocessor:
    @staticmethod
    async def preprocess(image_bytes: bytes):
        """Simplified image preprocessing - just needs bytes"""
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        img = cv2.resize(img,(224,224))
        img = np.expand_dims(img,axis=0)
        return img
        
class BodyPartClassifier:
    def __init__(self):
        self.class_names = ['ELBOW', 'FINGER', 'FOREARM', 'HAND', 'HUMERUS', 'SHOULDER', 'WRIST']

    @staticmethod
    @lru_cache(maxsize=2)
    def load_model_from_server():
        return load_model(f"{base_path}/final_Mura_classification_model.h5")

    async def predict(self, image):
        model = self.load_model_from_server()
        predictions = await asyncio.to_thread(model.predict, image, verbose=0)   
        class_index = int(np.argmax(predictions))
        confidence = float(predictions[0][class_index])
        body_part = self.class_names[class_index]
        return body_part, confidence


class FracturePredictor:
    @staticmethod
    @lru_cache(maxsize=10)
    def load_model_for_body_part(body_part: str):
        return load_model(f"{base_path}/ResNet50_XR_{body_part}_frac.h5")

    async def predict(self, image, body_part: str):
        model = self.load_model_for_body_part(body_part)
        prediction = await asyncio.to_thread(model.predict, image, verbose=0)  
        fracture_prob = float(prediction[0][0])
        label = "Fracture" if fracture_prob > 0.5 else "No Fracture"
        return label, fracture_prob
