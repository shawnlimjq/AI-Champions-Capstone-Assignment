import io
from pathlib import Path
import streamlit as st
from langchain_community.vectorstores import Chroma
from utils.functions import (
    collection_name,
    embeddings,
    get_suggested_prompts,
    persist_directory,
    process_uploaded_files,
)

st.set_page_config(page_title="File Uploader", page_icon="📁")

st.title("📁 File Uploader")

SAMPLE_FILE = Path(__file__).parent.parent / "sample_files" / "MediShield_Life_Brochure.pdf"

if "uploaded_file_signature" not in st.session_state:
    st.session_state.uploaded_file_signature = None
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

def get_chroma_upload_info():
    """Return (uploaded_at, file_names) from ChromaDB metadata, or (None, []) if empty."""
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
        results = vectorstore._collection.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        if not metadatas:
            return None, []
        file_names = sorted({m.get("uploaded_file_name", "") for m in metadatas if m.get("uploaded_file_name")})
        uploaded_at_values = [m.get("uploaded_at") for m in metadatas if m.get("uploaded_at")]
        latest_uploaded_at = max(uploaded_at_values) if uploaded_at_values else None
        return latest_uploaded_at, file_names
    except Exception:
        return None, []

col_reset, col_sample = st.columns([1, 2])
with col_reset:
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
        if "vectorstore" in st.session_state:
            del st.session_state.vectorstore
        st.session_state.file_uploader_key += 1
        st.rerun()

with col_sample:
    if SAMPLE_FILE.exists():
        if st.button("📄 Load sample file (MediShield Life Brochure)"):
            data = SAMPLE_FILE.read_bytes()
            sample = io.BytesIO(data)
            sample.name = SAMPLE_FILE.name
            sig = (SAMPLE_FILE.name, len(data))
            if st.session_state.uploaded_file_signature != (sig,):
                with st.spinner("Processing sample file…"):
                    process_uploaded_files([sample], 1000, 100)
                st.session_state.uploaded_file_signature = (sig,)
                st.rerun()

files = st.file_uploader(
    "Upload a PDF file. Multiple files can be selected.",
    type=["pdf"],
    accept_multiple_files=True,
    key=f"file_uploader_{st.session_state.file_uploader_key}",
)

if files:
    current_signature = tuple((file.name, file.size) for file in files)
    if st.session_state.uploaded_file_signature != current_signature:
        process_uploaded_files(files, 1000, 100)
        st.session_state.uploaded_file_signature = current_signature

last_uploaded_at, uploaded_file_names = get_chroma_upload_info()
if uploaded_file_names and last_uploaded_at:
    st.caption(f"Last uploaded: {last_uploaded_at}")
    st.caption(f"Uploaded file(s): {', '.join(uploaded_file_names)}")

suggested = get_suggested_prompts()
if suggested:
    st.markdown("**💡 Suggested questions:**")
    for prompt in suggested:
        st.markdown(f"- {prompt}")
