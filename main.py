from pathlib import Path
from src.ocr_reader import extract_text

import cv2

from src.image_preprocessing import (
    convert_to_grayscale,
    load_image,
    resize_image,
    binary_threshold,
    otsu_threshold,
    adaptive_threshold,
)

def main() -> None:
    image_path = Path("data/raw_receipts/IMG_4241.jpg")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    image = load_image(image_path)
    gray_image = convert_to_grayscale(image)
    resized_image = resize_image(gray_image)

    nearest_image = cv2.resize(
        gray_image,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_NEAREST,
    )

    linear_image = cv2.resize(
        gray_image,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_LINEAR,
    )

    cubic_image = cv2.resize(
        gray_image,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC,
    )

    binary_image = binary_threshold(resized_image)
    otsu_image = otsu_threshold(resized_image)
    adaptive_image = adaptive_threshold(resized_image)

    text = extract_text(otsu_image)

    print("/===== OCR RESULT =====")
    print(text)
    print("======================")

    print("Original image shape:", image.shape)
    print("Grayscale image shape:", gray_image.shape)
    print("Grayscale image shape:", type(gray_image))
    print("GrayScale data type:", gray_image.dtype)
    print("Resized:", resized_image.shape)

    print("Minimum pixel value:", gray_image.min())
    print("Maximum pixel value:", gray_image.max())
    print("Average brightness:", gray_image.mean())

    
    cv2.imwrite(
        str(output_dir / "IMG_4241_gray.jpg"),
        gray_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_resized.jpg"),
        resized_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_nearest.jpg"),
        nearest_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_linear.jpg"),
        linear_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_cubic.jpg"),
        cubic_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_binary.jpg"),
        binary_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_otsu.jpg"),
        otsu_image,
    )

    cv2.imwrite(
        str(output_dir / "IMG_4241_adaptive.jpg"),
        adaptive_image,
    )


if __name__ == "__main__":
    main()