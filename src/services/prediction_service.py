from datetime import datetime
from src.services.predictors import BodyPartClassifier, FracturePredictor
from src.models import Report
from typing import Optional
SUPPORTED_BODY_PARTS = ['ELBOW', 'FINGER', 'FOREARM', 'HAND', 'HUMERUS', 'SHOULDER', 'WRIST']

class PredictionService:
    def __init__(self):
        self.body_part_classifier = BodyPartClassifier()
        self.fracture_predictor = FracturePredictor()

    async def classify_body_part(self, report: Report, image: bytes) -> Report:
        report.status = "Classifying"
        body_part, confidence = self.body_part_classifier.predict(image)
        report.body_part = body_part
        report.confidence = confidence
        return report

    async def predict_fracture(self, report: Report, image: bytes, start_time: datetime,body_part:Optional[str]=None) -> Report:
        report.status = "Predicting"
        if body_part.upper() and body_part.upper() in SUPPORTED_BODY_PARTS:
            label, frac_conf = self.fracture_predictor.predict(image, body_part)
        else:
            if body_part:
                report.error ='body part u provide is not valid'
            label, frac_conf = self.fracture_predictor.predict(image, report.body_part)
        report.prediction = label
        report.fracture_confidence = frac_conf

        report.status = "Completed"
        report.model_time_seconds = (datetime.now() - start_time).total_seconds()
        return report
