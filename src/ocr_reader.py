import os
import shutil
from pathlib import Path
import pytesseract

def extract_text(image):
    command = os.getenv('TESSERACT_CMD') or shutil.which('tesseract')
    fallback = Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    if not command and fallback.exists():
        command = str(fallback)
    if not command:
        raise RuntimeError('Install Tesseract with German language data or set TESSERACT_CMD.')
    pytesseract.pytesseract.tesseract_cmd = command
    try:
        return pytesseract.image_to_string(image, lang='deu', timeout=60)
    except pytesseract.TesseractError as exc:
        raise RuntimeError('OCR failed. Check Tesseract and the German (deu) language pack.') from exc
