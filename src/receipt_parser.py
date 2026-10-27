"""Parser for German bakery receipts. Uncertain quantities require review."""
import re
from decimal import Decimal, InvalidOperation

PRODUCT_PATTERN = re.compile(r"^(\d{6})\s+W\s*(.+?)\s+(\d+[,.]\d{2})\s+EUR$", re.I)
QUANTITY_PATTERN = re.compile(r"^(\d+)\s+St\s+(\d+[,.]\d{2})\s+EUR/St$", re.I)
MISSING_QUANTITY_PATTERN = re.compile(r"^St\s+(\d+[,.]\d{2})\s+EUR/St$", re.I)

def money(value):
    d = Decimal(str(value).replace(',', '.'))
    if not d.is_finite() or d < 0 or d != d.quantize(Decimal('0.01')):
        raise ValueError('Prices must be finite, nonnegative amounts with at most two decimals')
    return int(d * 100)

def parse_product_line(line):
    m = PRODUCT_PATTERN.match(line.strip())
    return dict(product_id=m[1], product_name=m[2], total_price=float(m[3].replace(',', '.'))) if m else None

def normalize_quantity_line(line):
    return re.sub(r'^b(?=\s+St)', '6', line.strip().replace('$', 'St'))

def parse_quantity_line(line):
    m = QUANTITY_PATTERN.match(normalize_quantity_line(line))
    return dict(quantity=int(m[1]), unit_price=float(m[2].replace(',', '.'))) if m else None

def parse_missing_quantity_line(line):
    m = MISSING_QUANTITY_PATTERN.match(line.strip())
    return dict(unit_price=float(m[1].replace(',', '.'))) if m else None

def recover_quantity(total_price, unit_price):
    total, unit = money(total_price), money(unit_price)
    return total // unit if unit > 0 and total > 0 and total % unit == 0 else None

def validate_record(record):
    try:
        q = record.get('quantity')
        return isinstance(q, int) and not isinstance(q, bool) and q > 0 and q * money(record['unit_price']) == money(record['total_price'])
    except (ValueError, TypeError, KeyError, InvalidOperation):
        return False

def parse_receipt(text):
    records, current = [], None
    def finish(quantity=None, unit_price=None, issue='Missing quantity; review required'):
        nonlocal current
        if current is not None:
            row = dict(current, quantity=quantity, unit_price=unit_price, issue=issue)
            row['valid'] = validate_record(row)
            if not row['valid'] and not row['issue']:
                row['issue'] = 'Quantity × unit price does not equal total'
            records.append(row)
            current = None
    for line in text.splitlines():
        product = parse_product_line(line)
        if product:
            finish()
            current = product
        elif current:
            quantity = parse_quantity_line(line)
            missing = parse_missing_quantity_line(line)
            if quantity:
                issue = 'OCR quantity corrected; review required' if normalize_quantity_line(line) != line.strip() else ''
                finish(**quantity, issue=issue)
            elif missing:
                finish(recover_quantity(current['total_price'], missing['unit_price']), missing['unit_price'], 'Quantity inferred; review required')
    finish()
    return records
