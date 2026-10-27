# Validation — 27 October 2026

Environment: Windows, Python 3.13, local Ollama `llama3.2:latest` (model ID `a80c4f17acd5`), Streamlit 1.64.0, pandas 2.3.3, pytesseract 0.3.13, OpenCV 5.0.0.

- 17 standard-library unit/integration tests passed.
- Streamlit AppTest passed: initial demo totals, product filter and workspace switching.
- Local HTTP health endpoint returned `ok`.
- Batch text demo parsed four rows; one inferred-quantity row requires review.
- Local OCR smoke test processed four existing receipt images without runtime errors. OCR accuracy was not measured against labelled ground truth; substantial manual review was required. No real receipt content is included in this report.
- Three real Ollama scenarios returned the expected tool outputs: Croissant quantity/cost, review issues and an absent product. The month bounds, EUR formatting and source IDs were inspected. This is a small smoke evaluation, not a general model-quality benchmark.

The initial model trial revealed two defects: English plural search missed a catalogue name, and generated prose confused cents with euros. Literal-search fallback handles the first; evidence-based summary rendering handles the second. The final observed answer was:

> Croissants (2026-10-01 to 2026-10-31): 10 units; EUR 5.30. Excluded review rows: 0. Sources: R-0c2457644fa1, R-f56df689d6eb.

Reproduce:

```bash
python -m unittest discover -s tests -v
python scripts/check_ui.py
python scripts/evaluate_agent.py
```

The core CI suite needs only Python. UI checks need installed requirements; real agent checks also need Ollama and the model. OCR additionally needs Tesseract with German language data. Results may differ across models and hardware. Review the selected date/product scope in each answer.
