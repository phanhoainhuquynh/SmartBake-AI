from pathlib import Path
import csv


def load_product_mapping(csv_path: str | Path) -> dict[str, str]:
    mapping = {}

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            product_id = row["product_id"].strip()
            product_name = row["product_name"].strip()

            mapping[product_id] = product_name

    return mapping


def id_distance(id1: str, id2: str) -> int:
    if len(id1) != len(id2):
        return 999

    differences = 0

    for char1, char2 in zip(id1, id2):
        if char1 != char2:
            differences += 1

    return differences


def find_closest_product_id(
    product_id: str,
    mapping: dict[str, str]
) -> tuple[str | None, int]:

    closest_id = None
    smallest_distance = 999

    for catalog_id in mapping:
        distance = id_distance(product_id, catalog_id)

        if distance < smallest_distance:
            smallest_distance = distance
            closest_id = catalog_id

    return closest_id, smallest_distance


def normalize_product(
    product: dict,
    mapping: dict[str, str]
) -> dict:

    product_id = product["product_id"]

    # Case 1: ID is correct
    if product_id in mapping:
        product["product_name"] = mapping[product_id]
        return product

    # Case 2: ID does not exist
    closest_id, distance = find_closest_product_id(
        product_id,
        mapping
    )

    if closest_id is not None and distance <= 1:
        product["product_id"] = closest_id
        product["product_name"] = mapping[closest_id]

    return product


def normalize_records(
    records: list[dict],
    mapping: dict[str, str]
) -> list[dict]:

    normalized_records = []

    for record in records:
        clean_record = normalize_product(record, mapping)
        normalized_records.append(clean_record)

    return normalized_records