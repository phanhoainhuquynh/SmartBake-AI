"""SQLite storage with integer cents and human-approved imports."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path
from .receipt_parser import money, validate_record

class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, receipt_date TEXT NOT NULL,
                digest TEXT NOT NULL UNIQUE, text TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS items (
                receipt_id TEXT NOT NULL REFERENCES receipts(id), product_id TEXT NOT NULL,
                product_name TEXT NOT NULL, quantity INTEGER, unit_cents INTEGER,
                total_cents INTEGER NOT NULL, valid INTEGER NOT NULL, issue TEXT NOT NULL);
            """)
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()
    def save(self, source, receipt_date, text, records, fingerprint=None):
        date.fromisoformat(receipt_date)
        if not records:
            raise ValueError('No product rows to save')
        digest = fingerprint or hashlib.sha256(text.strip().encode()).hexdigest()
        receipt_id = 'R-' + digest[:12]
        rows = []
        for r in records:
            q = r.get('quantity')
            if q is not None:
                if isinstance(q, bool) or int(q) != q or q <= 0:
                    raise ValueError('Quantity must be a positive integer or empty')
                q = int(q)
            record = dict(r, quantity=q)
            valid = validate_record(record)
            issue = str(r.get('issue') or '')
            if not valid and not issue:
                issue = 'Missing values or price mismatch'
            if not str(r.get('product_id', '')).strip() or not str(r.get('product_name', '')).strip():
                raise ValueError('Product ID and name are required')
            rows.append((receipt_id, str(r['product_id']), str(r['product_name']), q,
                         money(r['unit_price']) if r.get('unit_price') is not None else None,
                         money(r['total_price']), int(valid), issue))
        with self.connect() as db:
            existing = db.execute('SELECT id FROM receipts WHERE digest=?', (digest,)).fetchone()
            if existing:
                return existing['id'], False
            db.execute('INSERT INTO receipts VALUES (?,?,?,?,?)', (receipt_id, Path(source).name, receipt_date, digest, text))
            db.executemany('INSERT INTO items VALUES (?,?,?,?,?,?,?,?)', rows)
        return receipt_id, True
    def rows(self, product='', start_date='', end_date=''):
        for d in (start_date, end_date):
            if d: date.fromisoformat(d)
        if start_date and end_date and start_date > end_date:
            raise ValueError('start_date must not be after end_date')
        sql = """SELECT r.id AS receipt_id, r.source, r.receipt_date, i.*
                 FROM items i JOIN receipts r ON r.id=i.receipt_id
                 WHERE (instr(lower(i.product_name),lower(?))>0 OR i.product_id=?)"""
        args = [product, product]
        if start_date:
            sql += ' AND r.receipt_date>=?'; args.append(start_date)
        if end_date:
            sql += ' AND r.receipt_date<=?'; args.append(end_date)
        sql += ' ORDER BY r.receipt_date,r.id,i.rowid'
        with self.connect() as db:
            rows = [dict(r) for r in db.execute(sql, args)]
        # Conservative English plural fallback, only when the literal query has no matches.
        if not rows and len(product) > 3 and product.lower().endswith('s'):
            return self.rows(product[:-1], start_date, end_date)
        return rows
    def search_receipts(self, product='', start_date='', end_date=''):
        rows = self.rows(product, start_date, end_date)
        return {'rows': rows[:100], 'matched_rows': len(rows), 'truncated': len(rows)>100}
    def summarize_purchases(self, product='', start_date='', end_date=''):
        rows = self.rows(product, start_date, end_date)
        accepted = [r for r in rows if r['valid'] and not r['issue']]
        return {'currency':'EUR', 'total_cents':sum(r['total_cents'] for r in accepted),
                'total_eur':f"{sum(r['total_cents'] for r in accepted)/100:.2f}",
                'quantity':sum(r['quantity'] for r in accepted), 'accepted_rows':len(accepted),
                'excluded_review_rows':len(rows)-len(accepted),
                'sources':sorted({r['receipt_id'] for r in accepted}),
                'scope': {'product':product,'start_date':start_date,'end_date':end_date}}
    def check_receipt_errors(self, product='', start_date='', end_date=''):
        rows = [r for r in self.rows(product,start_date,end_date) if not r['valid'] or r['issue']]
        return {'rows':rows[:100], 'review_count':len(rows), 'truncated':len(rows)>100}
    def export_report(self, product='', start_date='', end_date=''):
        # No model-controlled filesystem paths: the UI offers the returned report for download.
        return {'summary':self.summarize_purchases(product,start_date,end_date),
                'review':self.check_receipt_errors(product,start_date,end_date)}
