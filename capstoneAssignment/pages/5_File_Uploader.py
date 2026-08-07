import streamlit as st
from utils.functions import build_vector_store, process_uploaded_files

st.set_page_config(page_title="File Uploader", page_icon="📁")

st.title("📁 File Uploader")

files = st.file_uploader("Upload a txt, pdf, or docx file. Multiple files can be selected.", type=["txt", "pdf", "docx"], accept_multiple_files=True)

process_uploaded_files(files, 1000, 100)
