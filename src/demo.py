from pathlib import Path
from .receipt_parser import parse_receipt

def load_demo(store):
    root = Path(__file__).resolve().parents[1]/'data'/'demo'
    for index, path in enumerate(sorted(root.glob('*.txt')), 1):
        text = path.read_text(encoding='utf-8')
        store.save(path.name, f'2026-10-{19+index:02}', text, parse_receipt(text))
