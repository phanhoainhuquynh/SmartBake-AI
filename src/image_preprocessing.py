from pathlib import Path

import cv2
import numpy as np

def load_image(image_path: str | Path) -> np.ndarray:
    """Load an image from dick"""
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    return image

def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR image into a grayscale image"""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def resize_image(
        image: np.ndarray,
        scale: float = 2.0
) -> np.ndarray:
    """Enlarge an image using cubic interpolation."""

    resized_image = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    return resized_image
