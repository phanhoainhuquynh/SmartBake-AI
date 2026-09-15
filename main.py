from pathlib import Path

from src.image_preprocessing import (
    load_image,
    convert_to_grayscale,
    resize_image,
    otsu_threshold,
)
from src.ocr_reader import extract_text
from src.receipt_parser import parse_receipt
from src.product_normalizer import (
    load_product_mapping,
    normalize_records,
)


def main() -> None:
    # 1. Load receipt image
    image_path = Path("data/raw_receipts/IMG_4241.jpg")
    image = load_image(image_path)

    # 2. Preprocess image
    gray_image = convert_to_grayscale(image)
    resized_image = resize_image(gray_image)
    otsu_image = otsu_threshold(resized_image)

    # 3. OCR
    text = extract_text(otsu_image)

    # 4. Parse OCR text
    records = parse_receipt(text)

    # 5. Load product catalog
    mapping = load_product_mapping(
        "config/product_mapping.csv"
    )

    # 6. Normalize products
    clean_records = normalize_records(
        records,
        mapping
    )

    # 7. Display result
    print("\n===== NORMALIZED RECORDS =====")

    for record in clean_records:
        print(record)

    print("\nNumber of records:", len(clean_records))


if __name__ == "__main__":
    main()