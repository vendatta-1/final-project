
from src.database import get_db
from src.schemas import ReportCreate
from datetime import datetime
from src.models import Report
from src.logger import logger
from src.services import ImagePreprocessor, BodyPartClassifier, FracturePredictor
from fastapi import UploadFile

class Service:
    def __init__(self):
        self.body_part_classifier = BodyPartClassifier()
        self.fracture_predictor = FracturePredictor()

    def predict(self, image_file: UploadFile):
        report = ReportCreate(
            filename=image_file.filename,
            format=image_file.content_type,
            received_time=datetime.now(),
            model_time_seconds=0.0,
            body_part="",
            confidence=None,
            prediction="",
        )

        try:

            image = ImagePreprocessor.preprocess(image_file)

            body_part, confidence = self.body_part_classifier.predict(image)

            fracture_label, fracture_conf = self.fracture_predictor.predict(image, body_part)

            report.body_part = body_part
            report.confidence = confidence
            report.prediction = fracture_label
            report.fracture_confidence = fracture_conf
        except Exception as e:
            report.body_part = "Unknown"
            report.prediction = "Error"
            report.error = str(e)
            logger.error(f"Error processing image: {str(e)}")

        report.model_time_seconds = (datetime.now() - report.received_time).total_seconds()

        try:
            with get_db() as db_session:
                db_report = Report(**report.dict())
                db_session.add(db_report)
                db_session.commit()
                report.id = db_report.id
                logger.info(f"Report created: {db_report.id}")
        except Exception as e:
            report.error = str(e)
            logger.error(f"Error inserting report into DB: {str(e)}")

        return report
