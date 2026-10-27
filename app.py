"""Run with: python -m streamlit run app.py"""
import hashlib
import json
from datetime import date
from pathlib import Path
import tempfile
import pandas as pd
import streamlit as st
from src.agent import OllamaClient, run_agent
from src.demo import load_demo
from src.storage import Store
from src.receipt_parser import parse_receipt
from src.product_normalizer import load_product_mapping, normalize_records
from src.csv_exporter import records_to_csv

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='SmartBake AI', page_icon='🥐', layout='wide')
st.title('🥐 SmartBake AI')
st.caption('Receipt Analysis Agent · German receipt OCR · Local tools · Traceable answers')
mode = st.sidebar.radio('Workspace', ['Demo', 'My receipts'])
store = Store(ROOT/'data'/'local'/('demo.sqlite3' if mode=='Demo' else 'receipts.sqlite3'))
if mode=='Demo':
    load_demo(store)
    st.sidebar.info('Synthetic data: 20–21 October 2026. No real customer information.')
model = st.sidebar.text_input('Ollama model', 'llama3.2')
st.sidebar.caption('Chat requires a running Ollama server and a model supporting tools. Receipt tools work without a model.')
summary = store.summarize_purchases()
a,b,c = st.columns(3)
a.metric('Verified purchases', f"€{summary['total_cents']/100:.2f}")
b.metric('Verified units', summary['quantity'])
c.metric('Rows needing review', summary['excluded_review_rows'])
tabs = st.tabs(['Overview & reports', 'Import & review', 'Ask the agent'])
with tabs[0]:
    st.subheader('Explore purchase records')
    product = st.text_input('Filter by product name or ID')
    dates = st.columns(2)
    start = dates[0].text_input('From date (YYYY-MM-DD)', '')
    end = dates[1].text_input('To date (YYYY-MM-DD)', '')
    try:
        rows = store.rows(product,start,end)
        st.dataframe(rows, width='stretch', hide_index=True)
        report = store.export_report(product,start,end)
        st.json(report['summary'])
        st.download_button('Download report JSON', json.dumps(report,ensure_ascii=False,indent=2), 'smartbake-report.json', 'application/json')
        csv_rows = [dict(r,total_price=r['total_cents']/100,unit_price=r['unit_cents']/100 if r['unit_cents'] is not None else None) for r in rows]
        st.download_button('Download item CSV', records_to_csv(csv_rows).encode('utf-8-sig'), 'smartbake-items.csv','text/csv')
    except ValueError as exc:
        st.warning(str(exc))
with tabs[1]:
    st.subheader('Extract → review → save')
    st.caption('Supported layout: six-digit product ID, W, name and EUR total; next line contains St and EUR/St. Dates are entered explicitly.')
    if mode=='Demo':
        st.info('Switch to My receipts to import your own files. Demo stays separate.')
    else:
        uploaded = st.file_uploader('Receipt image or OCR text',type=['jpg','jpeg','png','txt'])
        receipt_date = st.date_input('Receipt date',date.today())
        if uploaded:
            raw = uploaded.getvalue()
            digest = hashlib.sha256(raw).hexdigest()
            if st.button('Extract receipt'):
                try:
                    if len(raw)>15*1024*1024: raise ValueError('File limit: 15 MB')
                    if uploaded.name.lower().endswith('.txt'):
                        text=raw.decode('utf-8-sig')
                    else:
                        from src.image_preprocessing import load_image,convert_to_grayscale,resize_image,otsu_threshold
                        from src.ocr_reader import extract_text
                        with tempfile.TemporaryDirectory() as tmp:
                            path=Path(tmp)/('receipt'+Path(uploaded.name).suffix)
                            path.write_bytes(raw)
                            image=load_image(path)
                            if image.shape[0]*image.shape[1]>25_000_000: raise ValueError('Image limit: 25 megapixels')
                            text=extract_text(otsu_threshold(resize_image(convert_to_grayscale(image))))
                    mapping=load_product_mapping(ROOT/'config'/'product_mapping.csv')
                    st.session_state['draft']={'digest':digest,'text':text,'rows':normalize_records(parse_receipt(text),mapping)}
                except Exception as exc:
                    st.error(f'Extraction failed: {exc}')
            draft=st.session_state.get('draft')
            if draft and draft['digest']==digest:
                with st.expander('Extracted source text'):
                    st.text(draft['text'])
                st.info('Compare every row with the original. Correct missing values. Clear the issue field only after checking the row; price consistency is recomputed on save.')
                if not draft['rows']: st.warning('No supported product lines detected. Check the source text/layout.')
                else:
                    frame=st.data_editor(pd.DataFrame(draft['rows']),num_rows='dynamic',hide_index=True,disabled=['valid'],key='editor-'+digest)
                    approved=st.checkbox('I compared these rows with the original receipt',key='approve-'+digest)
                    if st.button('Save reviewed receipt',disabled=not approved):
                        try:
                            records=frame.astype(object).where(pd.notna(frame),None).to_dict('records')
                            rid,created=store.save(uploaded.name,receipt_date.isoformat(),draft['text'],records,digest)
                            st.success(f"{'Saved' if created else 'Already imported'}: {rid}")
                        except Exception as exc: st.error(f'Could not save: {exc}')
with tabs[2]:
    st.subheader('Ask about your receipts')
    st.caption('Try: “How many Croissants did I buy in October 2026, and what did they cost? Also check for receipt errors.”')
    key='chat-'+mode
    if key not in st.session_state: st.session_state[key]=[]
    if st.button('Clear conversation'): st.session_state[key]=[]
    for item in st.session_state[key]:
        with st.chat_message(item['role']):
            st.markdown(item['content'])
            if item.get('trace'):
                with st.expander('Tool calls & source evidence'): st.json(item['trace'])
    question=st.chat_input('Ask in English, German or Vietnamese')
    if question:
        history=st.session_state[key]
        with st.chat_message('user'): st.markdown(question)
        try:
            with st.spinner('Agent is checking the receipt tools…'):
                result=run_agent(question,store,OllamaClient(model),history)
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer'],'trace':result['trace']}])
            with st.chat_message('assistant'):
                st.markdown(result['answer'])
                with st.expander('Tool calls & source evidence',expanded=True): st.json(result['trace'])
                st.download_button('Download analysis',json.dumps(result,ensure_ascii=False,indent=2),'smartbake-analysis.json','application/json')
            if not result['trace']: st.caption('This reply did not call a receipt tool; it is not verified purchase evidence.')
        except Exception as exc:
            st.error(f'Agent unavailable: {exc}. Check that Ollama is running and the selected model is installed. You can still use Overview & reports.')
