from pathlib import Path

import cv2

from src.image_preprocessing import (
    convert_to_grayscale,
    load_image,
)

def main() -> None:
    image_path = Path("data/raw_receipts/IMG_4241.jpg")
    output_path = Path("data/processed/IMG_4241_gray.jpg")

    image =load_image(image_path)
    gray_image = convert_to_grayscale(image)

    print("Original image shape:", image.shape)
    print("Grayscale image shape:", gray_image.shape)
    print("Grayscale image shape:", type(gray_image))
    print("GrayScale data type:", gray_image.dtype)

    print("Minimum pixel value:", gray_image.min())
    print("Maximum pixel value:", gray_image.max())
    print("Average brightness:", gray_image.mean())

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sucess = cv2.imwrite(str(output_path), gray_image)

    if not sucess:
        raise RuntimeError(f"Cannot save image to: {output_path}")

    print (f"Saved grayscale image to: {output_path}")


if __name__ == "__main__":
    main()