"""Optional real Ollama evaluation on synthetic receipts."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.storage import Store
from src.demo import load_demo
from src.agent import OllamaClient, run_agent

CASES = [
    ('How many Croissants did I buy in October 2026 and what was their total cost?', 'summarize_purchases', 'total_cents', 530),
    ('Check all my receipt rows for errors or data needing review.', 'check_receipt_errors', 'review_count', 1),
    ('What was the total purchase cost of Unicorn Cake in October 2026?', 'summarize_purchases', 'total_cents', 0),
]

def main():
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp)/'eval.db')
        load_demo(store)
        for question, tool, key, value in CASES:
            try:
                result = run_agent(question, store, OllamaClient())
                passed = any(t['tool'] == tool and t['result'].get(key) == value for t in result['trace'])
                if 'October 2026' in question:
                    passed = passed and any(t['tool'] == tool and t['arguments'].get('start_date') == '2026-10-01'
                                            and t['arguments'].get('end_date') == '2026-10-31' for t in result['trace'])
                if value == 530:
                    passed = passed and 'EUR 5.30' in result['answer'] and 'R-' in result['answer']
                if tool == 'summarize_purchases' and value == 0:
                    passed = passed and 'No verified purchase rows' in result['answer']
                results.append(dict(question=question, passed=passed, **result))
            except Exception as exc:
                results.append(dict(question=question, passed=False, error=str(exc)))
            print(f"{'PASS' if results[-1]['passed'] else 'FAIL'}: {question}", flush=True)
    path = Path(__file__).resolve().parents[1]/'data/output/agent-evaluation.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(r['passed'] for r in results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
