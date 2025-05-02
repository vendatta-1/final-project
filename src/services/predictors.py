from keras.api.models import load_model,Model 
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = (BASE_DIR / "../ai_models").resolve()
IMAGE_SIZE = (224, 224)
SUPPORTED_BODY_PARTS = ['ELBOW', 'FINGER', 'FOREARM', 'HAND', 'HUMERUS', 'SHOULDER', 'WRIST']


    
class ModelLoader:
    """Centralized model loader with caching."""

    @staticmethod
    @lru_cache(maxsize=1)
    def load_body_part_classifier() -> Model:
        return load_model(MODEL_DIR / "final_Mura_classification_model.h5")

    @staticmethod
    @lru_cache(maxsize=7)
    def load_fracture_model(body_part: str) -> Model:
        model_path = MODEL_DIR / f"ResNet50_XR_{body_part.upper()}_frac.h5"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found for body part: {body_part}")
        return load_model(model_path)

class BodyPartClassifier:
    """Predicts the body part from an X-ray image."""

    @staticmethod
    @lru_cache(maxsize=1)
    def load_body_part_classifier()->Model:
        return load_model(MODEL_DIR / "final_Mura_classification_model.h5")
    def __init__(self):
        self.model = self.load_body_part_classifier()
        self.class_names = SUPPORTED_BODY_PARTS

    def predict(self, image: np.ndarray) -> Tuple[str, float]:
        """Return predicted body part and confidence."""
        preds = self.model.predict(image, verbose=0)[0]
        idx = int(np.argmax(preds))
        class_name = self.class_names[idx]
        confidence = float(preds[idx])
        return class_name, confidence
class FracturePredictor:
    """Predicts fracture presence for a specific body part."""
    def __init__(self):
        self.supported_parts = set(SUPPORTED_BODY_PARTS)
    @staticmethod
    @lru_cache(maxsize=7)
    def load_fracture_model(body_part:str)->Model:
        model_path = MODEL_DIR / f"ResNet50_XR_{body_part.upper()}_frac.h5"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found for body part: {body_part}")
        return load_model(model_path)
    
    def predict(self, image: np.ndarray, body_part: str) -> Tuple[str, float]:
        """Predict fracture status for a given body part image."""
        body_part = body_part.upper()
        if body_part not in self.supported_parts:
            raise ValueError(f"Unsupported body part: {body_part}")

        model = ModelLoader.load_fracture_model(body_part)
        prob = float(model.predict(image, verbose=0)[0][0])
        label = "Fracture" if prob > 0.5 else "No Fracture"
        return label, prob

    def predict_with_body_part(self, body_part: str, image: np.ndarray) -> Optional[Tuple[str, float]]:
        """Safe wrapper that returns None if invalid body part is given."""
        try:
            return self.predict(image, body_part)
        except (ValueError, FileNotFoundError):
            return None