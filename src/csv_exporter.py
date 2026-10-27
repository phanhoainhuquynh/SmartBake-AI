import csv
import io
from pathlib import Path

FIELDS = ['product_id', 'product_name', 'total_price', 'quantity', 'unit_price', 'valid', 'issue']

def records_to_csv(records):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, extrasaction='ignore')
    writer.writeheader()
    for record in records:
        row = dict(record)
        for key in ('product_id', 'product_name', 'issue'):
            value = str(row.get(key, ''))
            if value.lstrip().startswith(('=', '+', '-', '@')):
                row[key] = "'" + value
        writer.writerow(row)
    return output.getvalue()

def export_records_to_csv(records, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(records_to_csv(records), encoding='utf-8-sig')
