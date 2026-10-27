"""Batch image/text extraction with review flags. Does not auto-approve imports."""
import argparse
from pathlib import Path
from src.product_normalizer import load_product_mapping, normalize_records
from src.receipt_parser import parse_receipt
from src.csv_exporter import export_records_to_csv

ROOT = Path(__file__).resolve().parent

def process_receipt(image_path, mapping):
    from src.image_preprocessing import load_image, convert_to_grayscale, resize_image, otsu_threshold
    from src.ocr_reader import extract_text
    image = otsu_threshold(resize_image(convert_to_grayscale(load_image(image_path))))
    return normalize_records(parse_receipt(extract_text(image)),mapping)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'data'/'raw_receipts')
    parser.add_argument('--output',type=Path,default=ROOT/'data'/'output')
    args=parser.parse_args()
    mapping=load_product_mapping(ROOT/'config'/'product_mapping.csv')
    files=[args.input] if args.input.is_file() else sorted(p for p in args.input.glob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.txt'})
    if not files: parser.error('No supported receipt files found')
    failed=False
    for path in files:
        try:
            records=normalize_records(parse_receipt(path.read_text(encoding='utf-8-sig')),mapping) if path.suffix.lower()=='.txt' else process_receipt(path,mapping)
            export_records_to_csv(records,args.output/(path.name+'.csv'))
            print(f'{path.name}: {len(records)} rows, {sum(not r["valid"] or bool(r["issue"]) for r in records)} requiring review')
            if not records: failed=True
        except Exception as exc:
            failed=True
            print(f'{path.name}: ERROR: {exc}')
    return int(failed)

if __name__=='__main__':
    raise SystemExit(main())
