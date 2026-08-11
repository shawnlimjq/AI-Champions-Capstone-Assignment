"""
pages/5_File_Uploader.py
------------------------
Admin-only page for uploading PDF documents into the ChromaDB vector store.

Features:
- One-click sample file loader (MediShield Life Brochure).
- Multi-file PDF upload widget.
- Displays upload timestamp and indexed file names sourced from ChromaDB metadata.
- Shows AI-generated suggested questions after successful indexing.
- Reset button to wipe the entire ChromaDB collection.
"""

import io
from pathlib import Path

import streamlit as st

from utils.functions import (
    collection_name,
    get_suggested_prompts,
    get_vectorstore,
    process_uploaded_files,
)

st.set_page_config(page_title="File Uploader", page_icon="📁")
st.title("📁 File Uploader")

SAMPLE_FILE = Path(__file__).parent.parent / "sample_files" / "MediShield_Life_Brochure.pdf"

if "uploaded_file_signature" not in st.session_state:
    st.session_state.uploaded_file_signature = None
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0


def get_chroma_upload_info() -> tuple:
    """
    Query ChromaDB metadata to retrieve upload info.

    Returns:
        Tuple of (latest_uploaded_at: str | None, file_names: list[str]).
    """
    try:
        metadatas = get_vectorstore()._collection.get(include=["metadatas"]).get("metadatas") or []
        if not metadatas:
            return None, []
        file_names = sorted({
            m.get("uploaded_file_name", "")
            for m in metadatas if m.get("uploaded_file_name")
        })
        uploaded_at_values = [m.get("uploaded_at") for m in metadatas if m.get("uploaded_at")]
        return max(uploaded_at_values) if uploaded_at_values else None, file_names
    except Exception:
        return None, []


# ── Toolbar: Reset & Sample file ─────────────────────────────────────────────
col_reset, col_sample = st.columns([1, 2])

with col_reset:
    if st.button("Reset uploads"):
        vectorstore = get_vectorstore()
        existing_names = {
            item.name if hasattr(item, "name") else item
            for item in vectorstore._client.list_collections()
        }
        if collection_name in existing_names:
            vectorstore._client.delete_collection(collection_name)
        st.session_state.uploaded_file_signature = None
        st.session_state.pop("vectorstore", None)
        st.session_state.pop("embeddings", None)
        st.session_state.file_uploader_key += 1
        st.rerun()

with col_sample:
    if SAMPLE_FILE.exists() and st.button("📄 Load sample file (MediShield Life Brochure)"):
        data = SAMPLE_FILE.read_bytes()
        sample = io.BytesIO(data)
        sample.name = SAMPLE_FILE.name
        sig = (SAMPLE_FILE.name, len(data))
        if st.session_state.uploaded_file_signature != (sig,):
            with st.spinner("Processing sample file…"):
                process_uploaded_files([sample], 1000, 100)
            st.session_state.uploaded_file_signature = (sig,)
            st.rerun()

# ── File uploader widget ──────────────────────────────────────────────────────
files = st.file_uploader(
    "Upload a PDF file. Multiple files can be selected.",
    type=["pdf"],
    accept_multiple_files=True,
    key=f"file_uploader_{st.session_state.file_uploader_key}",
)

if files:
    current_signature = tuple((f.name, f.size) for f in files)
    if st.session_state.uploaded_file_signature != current_signature:
        with st.spinner("Processing uploaded files…"):
            process_uploaded_files(files, 1000, 100)
        st.session_state.uploaded_file_signature = current_signature

# ── Upload status & suggested questions ──────────────────────────────────────
last_uploaded_at, uploaded_file_names = get_chroma_upload_info()
if uploaded_file_names and last_uploaded_at:
    st.caption(f"Last uploaded: {last_uploaded_at}")
    st.caption(f"Uploaded file(s): {', '.join(uploaded_file_names)}")

suggested = get_suggested_prompts()
if suggested:
    st.markdown("**💡 Suggested questions:**")
    for prompt in suggested:
        st.markdown(f"- {prompt}")
