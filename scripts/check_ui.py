"""Optional Streamlit smoke test; run after installing requirements."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
assert not app.exception, app.exception
assert app.metric[0].value == '€9.30'
app.text_input[0].set_value('Croissant').run()
assert not app.exception, app.exception
app.sidebar.radio[0].set_value('My receipts').run()
assert not app.exception, app.exception
print('PASS: demo totals, product filter, My receipts workspace')
