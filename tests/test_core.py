import json
import tempfile
import unittest
from pathlib import Path
from src.receipt_parser import parse_receipt, recover_quantity, validate_record
from src.storage import Store
from src.demo import load_demo
from src.agent import run_agent
from src.csv_exporter import records_to_csv

class ParserTests(unittest.TestCase):
    def test_missing_is_not_one(self):
        row=parse_receipt('002601 W Croissant 3,18 EUR')[0]
        self.assertIsNone(row['quantity'])
        self.assertFalse(row['valid'])
    def test_recovery_requires_exact_nonzero_division(self):
        self.assertEqual(recover_quantity(.91,.13),7)
        self.assertIsNone(recover_quantity(1,0))
        self.assertIsNone(recover_quantity(1,.3))
    def test_inferred_requires_review(self):
        row=parse_receipt('002601 W Croissant 3,18 EUR\nSt 0,53 EUR/St')[0]
        self.assertTrue(row['valid'])
        self.assertTrue(row['issue'])
    def test_cents_exact(self):
        self.assertTrue(validate_record(dict(quantity=3,unit_price=.1,total_price=.3)))
        self.assertFalse(validate_record(dict(quantity=3,unit_price=.1,total_price=.31)))
    def test_ocr_correction_flagged(self):
        row=parse_receipt('002601 W Croissant 3,18 EUR\nb St 0,53 EUR/St')[0]
        self.assertEqual(row['quantity'],6)
        self.assertTrue(row['issue'])
    def test_mismatch_and_product_boundary(self):
        rows=parse_receipt('002601 W Croissant 3,18 EUR\n002605 W Cake 2,00 EUR\n3 St 1,00 EUR/St')
        self.assertEqual(len(rows),2)
        self.assertTrue(all(not r['valid'] for r in rows))
    def test_csv_headers_and_formula_escape(self):
        self.assertIn('product_id',records_to_csv([]))
        self.assertIn("'=HYPERLINK",records_to_csv([{'product_name':'=HYPERLINK'}]))

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.temp.name)/'test.db')
        load_demo(self.store)
    def tearDown(self): self.temp.cleanup()
    def test_demo_and_duplicates(self):
        load_demo(self.store)
        result=self.store.summarize_purchases('Croissant')
        self.assertEqual((result['quantity'],result['total_cents']),(10,530))
        self.assertEqual(len(result['sources']),2)
        self.assertEqual(len(self.store.rows()),4)
    def test_excludes_review(self):
        result=self.store.summarize_purchases()
        self.assertEqual(result['total_cents'],930)
        self.assertEqual(result['excluded_review_rows'],1)
    def test_plural_product_lookup(self):
        self.assertEqual(self.store.summarize_purchases('Croissants')['total_cents'],530)
    def test_date_filter(self):
        self.assertEqual(self.store.summarize_purchases('Croissant','2026-10-21','2026-10-21')['quantity'],4)
        with self.assertRaises(ValueError): self.store.rows(start_date='2026-02-30')
        with self.assertRaises(ValueError): self.store.rows(start_date='2026-11-01',end_date='2026-01-01')
    def test_sql_input_is_literal(self):
        self.assertEqual(self.store.rows("' OR 1=1 --"),[])
        self.assertEqual(len(self.store.rows()),4)
    def test_invalid_import_atomic(self):
        with self.assertRaises(ValueError):
            self.store.save('x','2026-10-22','x',[dict(product_id='1',product_name='X',quantity=1.5,unit_price=1,total_price=1.5)])
        self.assertEqual(len(self.store.rows()),4)
    def test_forged_valid_recomputed(self):
        self.store.save('x','2026-10-22','x',[dict(product_id='1',product_name='X',quantity=2,unit_price=1,total_price=3,valid=True,issue='')])
        self.assertEqual(self.store.check_receipt_errors()['review_count'],2)
    def test_agent_multitool(self):
        messages_seen=[]
        def client(messages):
            messages_seen.append(list(messages))
            if len(messages_seen)==1:
                return {'tool_calls':[{'function':{'name':'summarize_purchases','arguments':{'product':'Croissant'}}},{'function':{'name':'check_receipt_errors','arguments':{}}}]}
            return {'content':'10 croissants, EUR 5.30; see sources.'}
        result=run_agent('How many?',self.store,client)
        self.assertEqual(len(result['trace']),2)
        self.assertEqual(result['trace'][0]['result']['total_cents'],530)
        self.assertIn('EUR 5.30',result['answer'])
        self.assertIn('R-',result['answer'])
        self.assertEqual(messages_seen[1][-1]['role'],'tool')
    def test_agent_rejects_tools_and_arguments(self):
        for name,args in [('delete_receipts',{}),('search_receipts',{'sql':'DROP TABLE receipts'}),('search_receipts',{'product':42})]:
            responses=iter([{'tool_calls':[{'function':{'name':name,'arguments':args}}]},{'content':'error'}])
            result=run_agent('x',self.store,lambda _:next(responses))
            self.assertIn('error',result['trace'][0]['result'])
    def test_agent_bounded(self):
        result=run_agent('x',self.store,lambda _: {'tool_calls':[{'function':{'name':'search_receipts','arguments':{}}}]},max_rounds=2)
        self.assertEqual(len(result['trace']),2)
        self.assertIn('limit',result['answer'])

if __name__=='__main__': unittest.main()
