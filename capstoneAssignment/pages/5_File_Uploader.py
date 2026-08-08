from datetime import datetime

import streamlit as st
from langchain_community.vectorstores import Chroma
from utils.functions import (
    collection_name,
    embeddings,
    persist_directory,
    process_uploaded_files,
)

st.set_page_config(page_title="File Uploader", page_icon="📁")

st.title("📁 File Uploader")

if "uploaded_file_signature" not in st.session_state:
    st.session_state.uploaded_file_signature = None
if "last_uploaded_at" not in st.session_state:
    st.session_state.last_uploaded_at = None
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0
if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = []

if st.button("Reset uploads"):
    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    existing_collections = vectorstore._client.list_collections()
    existing_collection_names = {
        item.name if hasattr(item, "name") else item for item in existing_collections
    }
    if collection_name in existing_collection_names:
        vectorstore._client.delete_collection(collection_name)
    st.session_state.uploaded_file_signature = None
    st.session_state.last_uploaded_at = None
    st.session_state.uploaded_file_names = []
    if "vectorstore" in st.session_state:
        del st.session_state.vectorstore
    st.session_state.file_uploader_key += 1
    st.rerun()

files = st.file_uploader(
    "Upload a txt, pdf, or docx file. Multiple files can be selected.",
    type=["txt", "pdf", "docx"],
    accept_multiple_files=True,
    key=f"file_uploader_{st.session_state.file_uploader_key}",
)

if files:
    current_signature = tuple((file.name, file.size) for file in files)
    if st.session_state.uploaded_file_signature != current_signature:
        st.session_state.uploaded_file_names = [uploaded_file.name for uploaded_file in files]
        process_uploaded_files(files, 1000, 100)
        st.session_state.uploaded_file_signature = current_signature
        st.session_state.last_uploaded_at = datetime.now()

if st.session_state.uploaded_file_names and st.session_state.last_uploaded_at:
    st.caption(
        f"Last uploaded: {st.session_state.last_uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    st.caption(f"Uploaded file(s): {', '.join(st.session_state.uploaded_file_names)}")
