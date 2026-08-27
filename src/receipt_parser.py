import re

PRODUCT_PATTERN = re.compile(
    r"^(\d{6})\s+W\s*(.*?)\s+(\d+,\d{2})\s+EUR$"
)

MISSING_QUANTITY_PATTERN = re.compile(
    r"^St\s+(\d+,\d{2})\s+EUR/St$",
    re.IGNORECASE,
)

def parse_product_line(line: str):
    match = PRODUCT_PATTERN.match(line.strip())

    if not match:
        return None

    product_id = match.group(1)
    product_name = match.group(2)
    total_price = float(
        match.group(3).replace(",", ".")
    )

    return {
        "product_id": product_id,
        "product_name": product_name,
        "total_price": total_price,
    }

line = "002601 W Croissant Butte 3,18 EUR"

print(parse_product_line(line))

QUANTITY_PATTERN = re.compile(
    r"^(\d+)\s+St\s+(\d+,\d{2})\s+EUR/St$",
    re.IGNORECASE,
)

def normalize_quantity_line(line: str) -> str:
    line = line.strip()

    line = line.replace("$", "St")

    if line.startswith ("b St"):
        line = "6 St" + line[4:]

    return line

print(normalize_quantity_line("6 St 0,53 EUR/St"))
print(normalize_quantity_line("b St 0,53 EUR/St"))
print(normalize_quantity_line("3 $ 0,43 EUR/St"))

def parse_quantity_line (line:str):
    line = normalize_quantity_line(line)

    match = QUANTITY_PATTERN.match(line)

    if not match: 
        return None

    quantity = int(match.group(1))
    unit_price = float(
        match.group(2).replace(",", ".")
    )

    return {
        "quantity": quantity,
        "unit_price": unit_price,
    }

line = "6 St 0,53 EUR/St"

print(parse_quantity_line(line))

def validate_record(record: dict) -> bool:

    expected_total = (
        record["quantity"]
        * record["unit_price"]
    )

    return abs(
        expected_total - record["total_price"]
    ) < 0.01

product = parse_product_line (
    "002601 W Croissant Butte 3,18 EUR"
)

quantity = parse_quantity_line(
    "6 St 0,53 EUR/St"
)

record = {
    **product,
    **quantity,
}

print(record)
print("Valid", validate_record(record))

def parse_receipt(text: str) -> list[dict]:
    records = []
    current_product = None

    product_lines = 0
    quantity_lines = 0

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        product = parse_product_line(line)

        if product:
            product_lines += 1

            if current_product is not None:
                record = {
                    **current_product,
                    "quantity": 1,
                    "unit_price": current_product["total_price"],
                }

                record["valid"] = validate_record(record)
                records.append(record)

            current_product = product
            continue

        # 1. Testing with a normal quantity line 
        quantity = parse_quantity_line(line)

        if quantity and current_product:
            quantity_lines += 1

            record = {
                **current_product,
                **quantity,
            }

            record["valid"] = validate_record(record)
            records.append(record)

            current_product = None
            continue

        # 2. When OCR miss quantity
        missing_quantity = parse_missing_quantity_line(line)

        if missing_quantity and current_product:
            unit_price = missing_quantity["unit_price"]

            quantity = recover_quantity(
                current_product["total_price"],
                unit_price,
            )

            record = {
                **current_product,
                "quantity": quantity,
                "unit_price": unit_price,
            }

            record["valid"] = validate_record(record)
            records.append(record)

            current_product = None
            quantity_lines += 1
            continue

    # Final product without quantity line
    if current_product is not None:
        record = {
            **current_product,
            "quantity": 1,
            "unit_price": current_product["total_price"],
        }

        record["valid"] = validate_record(record)
        records.append(record)

    print("Detected product lines:", product_lines)
    print("Detected quantity lines:", quantity_lines)
    print("Completed records:", len(records))

    return records

def parse_missing_quantity_line(line: str):
    match = MISSING_QUANTITY_PATTERN.match(line.strip())

    if not match:
        return None

    unit_price = float(
        match.group(1).replace(",",".")
    )
    return {
        "unit_price": unit_price
    }

def recover_quantity(total_price: float, unit_price: float) -> int:
    quantity = round(total_price / unit_price)
    return quantity
        


print(
    parse_missing_quantity_line(
        "St 0,13 EUR/St"
    )
)

print(recover_quantity(0.91,0.13))

sample_text = """
002601 W Croissant Butte 3,18 EUR
6 St 0,53 EUR/St

002605 W Croissant Marzi 1,50 EUR
3 St 0,50 EUR/St
"""

records = parse_receipt(sample_text)

for record in records:
    print(record)

