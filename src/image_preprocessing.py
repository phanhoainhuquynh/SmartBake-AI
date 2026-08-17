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

def binary_threshold(
        image: np.ndarray,
        threshold_value: int = 168
) -> np.ndarray:

    _, thresholded = cv2.threshold(
        image,
        threshold_value,
        255,
        cv2.THRESH_BINARY
    )

    return thresholded

def otsu_threshold(image: np.ndarray) -> np.ndarray:

    threshold_value, thresholded = cv2.threshold(
        image,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    print(
        "Otsu selected threshold",
        threshold_value
    )

    return thresholded

def adaptive_threshold(image: np.ndarray) -> np.ndarray:

    thresholded = cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10
    )

    return thresholded