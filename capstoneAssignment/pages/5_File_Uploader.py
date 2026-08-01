import streamlit as st
import tempfile
from langchain_community.document_loaders import PyPDFLoader
import os

st.set_page_config(page_title="File Uploader", page_icon="📁")

st.title("📁 File Uploader")

files = st.file_uploader("Upload a txt, pdf, or docx file. Multiple files can be selected.", type=["txt", "pdf", "docx"], accept_multiple_files=True)

if files:
    suffix = ""
    name = getattr(files[0], "name", None)
    if name and "." in name:
        suffix = "." + name.rsplit(".", 1)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    data = None
    if hasattr(files[0], "getvalue"):
        data = files[0].getvalue()
    elif hasattr(files[0], "read"):
        data = files[0].read()
    else:
        raise ValueError("Unsupported uploaded_file type")
    tmp.write(data)
    tmp.flush()
    tmp.close()

    loader = PyPDFLoader(tmp.name)

    loaded = loader.load()

    print(loaded)

    os.remove(tmp.name)