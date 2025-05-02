import imghdr
from os import path
import cv2
import numpy as np 
from keras.api.applications.resnet50 import preprocess_input

VALID_EXTENSIONS =['.jpg','.jpeg','.png']
IMAGE_LEN = 10 * 1024 * 1024
IMAGE_SIZE =(224,224)

class ImageValidationService:
    @staticmethod
    def validate_image(content: bytes, filename: str) -> bool:
        extension = path.splitext(filename)[1].lower()
        """Validate that the given content represents a valid image.

        Checks the first 512 bytes of the provided content to determine if it matches a known image header
        and Image not exceeded 10 mg byte 

        Args:
            content: The image content as bytes.
            filename: The name of the file (currently unused).

        Returns:
            True if the content appears to be a valid image, False otherwise.
        """
        return bool(imghdr.what(None, content[:512]) and extension in VALID_EXTENSIONS )
    @staticmethod
    def validate_image_length(content: bytes) -> bool:
        return len(content) <= IMAGE_LEN
class ImagePreprocessor:
    """Handles image preprocessing operations."""
    
    @staticmethod
    def preprocess(image_bytes: bytes) -> np.ndarray:
        """Decode, resize, and normalize image bytes."""
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        image = cv2.resize(image, IMAGE_SIZE)
        image = np.expand_dims(image, axis=0)   
        return preprocess_input(image.astype(np.float16)) 