import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def extract_text(image: np.ndarray) -> str:
    """Extract text from a preprocessed image using Tesseract OCR."""

    text = pytesseract.image_to_string(
        image,
        lang="deu",
    )

    return text