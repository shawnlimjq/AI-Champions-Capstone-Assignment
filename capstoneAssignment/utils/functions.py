"""
utils/functions.py
------------------
Shared utilities for the CPF Schemes Self-Help Portal.

Responsibilities:
- Document loading, chunking, and vector store management (ChromaDB)
- RAG context retrieval and system prompt construction
- AI-generated suggested prompts (document-based and conversation follow-ups)
- Visualization data extraction from LLM responses
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import streamlit as st

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
persist_directory = "vectorstore"
collection_name = "cpf_data"

_NOT_FOUND = "I couldn't find that information in the uploaded document."
_SUGGESTED_PROMPTS_ID = "__suggested_prompts__"


def _get_api_key() -> str:
    """Resolve the OpenAI API key from Streamlit secrets."""
    return st.secrets["credentials"]["API_KEY"]


def _get_embeddings() -> OpenAIEmbeddings:
    """Lazily create the embeddings instance so it's resolved at call time, not import time."""
    if "embeddings" not in st.session_state:
        st.session_state["embeddings"] = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=_get_api_key()
        )
    return st.session_state["embeddings"]


def _get_openai_client() -> OpenAI:
    """Lazily create the OpenAI client so it's resolved at call time, not import time."""
    if "openai_client" not in st.session_state:
        st.session_state["openai_client"] = OpenAI(api_key=_get_api_key())
    return st.session_state["openai_client"]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_vectorstore() -> Chroma:
    """Return a fresh ChromaDB vectorstore instance (internal use)."""
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=_get_embeddings(),
    )


def get_vectorstore() -> Chroma:
    """Return a ChromaDB vectorstore instance (public, for use in pages)."""
    return _get_vectorstore()


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from an LLM response."""
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("```")
        ).strip()
    return text


# ── Document ingestion ────────────────────────────────────────────────────────

def process_uploaded_files(files, chunk_size: int, chunk_overlap: int) -> None:
    """
    Load, chunk, embed, and index a list of uploaded PDF files into ChromaDB.
    Also generates and stores 3 suggested questions based on the content.

    Args:
        files: Iterable of file-like objects with a `.name` attribute (PDF only).
        chunk_size: Maximum character length of each text chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.
    """
    if not files:
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []

    for uploaded_file in files:
        documents = _load_pdf(uploaded_file)
        chunks = splitter.split_documents(documents)
        if not chunks:
            continue
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No document content could be extracted from the uploaded files.")

    _build_vector_store(all_chunks)
    generate_suggested_prompts(all_chunks)


def _load_pdf(uploaded_file) -> list:
    """
    Write an uploaded file to a temporary path, load it with PyPDFLoader,
    and stamp each page with upload metadata.

    Returns:
        List of LangChain Document objects.
    """
    file_name = Path(getattr(uploaded_file, "name", "uploaded_file")).name
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        tmp.write(data)
        tmp.flush()
        tmp.close()

        documents = PyPDFLoader(tmp.name).load()
        uploaded_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for doc in documents:
            doc.metadata["uploaded_file_name"] = file_name
            doc.metadata["source"] = file_name
            doc.metadata["uploaded_at"] = uploaded_at
        return documents
    finally:
        tmp.close()
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def _build_vector_store(chunks: list) -> None:
    """Embed chunks and upsert them into ChromaDB."""
    vectorstore = _get_vectorstore()
    ids = [
        f"{chunk.metadata.get('uploaded_file_name', 'document')}-{i}-{uuid4().hex}"
        for i, chunk in enumerate(chunks)
    ]
    vectorstore.add_documents(chunks, ids=ids)
    vectorstore.persist()


# ── Suggested prompts ─────────────────────────────────────────────────────────

def generate_suggested_prompts(chunks: list) -> None:
    """
    Ask GPT-4o-mini to generate 3 questions from document content and persist
    them as a sentinel document in ChromaDB so they survive page reloads.

    Args:
        chunks: List of LangChain Document chunks (first 10 are sampled).
    """
    sample_text = "\n\n".join(c.page_content for c in chunks[:10])
    response = _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Given the following document excerpts, generate exactly 3 concise, "
                    "specific questions a user might want to ask about the content. "
                    'Return ONLY a JSON array of 3 strings, e.g. ["Q1", "Q2", "Q3"].'
                ),
            },
            {"role": "user", "content": sample_text},
        ],
    )
    prompts = json.loads(_strip_code_fences(response.choices[0].message.content.strip()))

    vectorstore = _get_vectorstore()
    doc = Document(
        page_content=_SUGGESTED_PROMPTS_ID,
        metadata={"type": "suggested_prompts", "prompts": json.dumps(prompts)},
    )
    vectorstore.add_documents([doc], ids=[_SUGGESTED_PROMPTS_ID])
    vectorstore.persist()


def get_suggested_prompts() -> list[str]:
    """
    Retrieve the document-based suggested prompts stored in ChromaDB.

    Returns:
        List of question strings, or an empty list if none are stored.
    """
    try:
        result = _get_vectorstore()._collection.get(
            ids=[_SUGGESTED_PROMPTS_ID], include=["metadatas"]
        )
        metadatas = result.get("metadatas") or []
        if metadatas and metadatas[0].get("prompts"):
            return json.loads(metadatas[0]["prompts"])
    except Exception:
        pass
    return []


def generate_followup_suggestions(messages: list[dict]) -> list[str]:
    """
    Generate 3 follow-up question suggestions based on recent conversation history.

    Args:
        messages: Full conversation as a list of {"role": str, "content": str} dicts.
                  Only the last 6 messages (3 turns) are used.

    Returns:
        List of 3 question strings.
    """
    history = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in messages[-6:]
    )
    response = _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Based on the conversation below, generate exactly 3 concise follow-up questions "
                    "the user might want to ask next. "
                    'Return ONLY a JSON array of 3 strings, e.g. ["Q1", "Q2", "Q3"]. '
                    "Do not include markdown fences or any other text."
                ),
            },
            {"role": "user", "content": history},
        ],
    )
    return json.loads(_strip_code_fences(response.choices[0].message.content.strip()))


# ── RAG pipeline ──────────────────────────────────────────────────────────────

def retrieve_context(vectorstore: Chroma, query: str, k: int = 4) -> tuple[str, list]:
    """
    Retrieve the top-k most relevant document chunks for a query.

    Args:
        vectorstore: ChromaDB vectorstore instance.
        query: User query string.
        k: Number of chunks to retrieve.

    Returns:
        Tuple of (concatenated context string, list of Document objects).
    """
    docs = vectorstore.as_retriever(search_kwargs={"k": k}).invoke(query)
    context = "---".join(doc.page_content for doc in docs)
    return context, docs


def build_rag_system_prompt(context: str) -> str:
    """
    Build a RAG system prompt that grounds the LLM to the retrieved context.

    Args:
        context: Concatenated text of retrieved document chunks.

    Returns:
        System prompt string.
    """
    return (
        "You are a helpful assistant. Answer the user's question using ONLY "
        "the information provided in the context below. "
        f"If the answer is not in the context, say: {_NOT_FOUND} "
        "If your answer contains numerical data that could be shown as a table or chart, "
        "describe it briefly in prose but DO NOT format it as a markdown table or list of numbers — "
        "a separate visualization will be generated and displayed automatically. "
        f"Context: {context}"
    )


def system_prompt_with_context(prompt: str) -> str:
    """
    Build the full system prompt for a user query by retrieving relevant context
    from ChromaDB and injecting it into the RAG prompt.

    Args:
        prompt: The user's query.

    Returns:
        System prompt string with injected context.
    """
    vectorstore = _get_vectorstore()
    st.session_state.vectorstore = vectorstore
    context, _ = retrieve_context(vectorstore, prompt, k=10)
    return build_rag_system_prompt(context)


# ── Visualization extraction ──────────────────────────────────────────────────

def extract_visualization_data(response_text: str) -> dict | None:
    """
    Ask GPT-4o-mini whether an assistant response contains data suitable for
    a table or chart, and extract it as structured JSON if so.

    Args:
        response_text: The full assistant response string.

    Returns:
        A dict with keys:
            - "type": "table" | "bar_chart" | "line_chart"
            - "title": short descriptive title
            - "columns": list of column name strings
            - "rows": list of lists (values matching columns order)
        Returns None if the response is not suitable for visualization.
    """
    response = _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Analyse the assistant response below and decide if it contains data "
                    "suitable for a table or chart. "
                    "If yes, return ONLY a JSON object with these keys:\n"
                    '  "type": one of "table", "bar_chart", "line_chart"\n'
                    '  "title": a short descriptive title\n'
                    '  "columns": array of column name strings\n'
                    '  "rows": array of arrays (values in columns order; use numbers where applicable)\n'
                    'If not suitable, return ONLY {"type": "none"}. '
                    "No markdown fences or extra text."
                ),
            },
            {"role": "user", "content": response_text},
        ],
    )
    result = json.loads(_strip_code_fences(response.choices[0].message.content.strip()))
    return None if result.get("type") == "none" else result
