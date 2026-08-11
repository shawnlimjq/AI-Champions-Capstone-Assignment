import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

load_dotenv()
secrets = st.secrets.get("credentials", {})
embeddings = OpenAIEmbeddings(
    model='text-embedding-3-small',
    api_key=secrets["API_KEY"],)
openai_client = OpenAI(api_key=secrets["API_KEY"])
not_found = "I couldn't find that information in the uploaded document."
system_prompt_no_doc = "You are a helpful assistant."
persist_directory = "vectorstore"
collection_name = "cpf_data"

def process_uploaded_files(files, chunk_size, chunk_overlap):
    if not files:
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    all_chunks = []

    for uploaded_file in files:
        documents = load_uploaded_file(uploaded_file)
        chunks = splitter.split_documents(documents)
        if not chunks:
            continue
        print(f"\nFirst chunk preview from {uploaded_file.name}:\n{chunks[0].page_content}")
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No document content could be extracted from the uploaded files.")

    build_vector_store(all_chunks)
    generate_suggested_prompts(all_chunks)


def load_uploaded_file(uploaded_file):
    file_name = Path(getattr(uploaded_file, "name", "uploaded_file")).name
    suffix = Path(file_name).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        if hasattr(uploaded_file, "getvalue"):
            data = uploaded_file.getvalue()
        elif hasattr(uploaded_file, "read"):
            data = uploaded_file.read()
        else:
            raise ValueError("Unsupported file type")

        tmp.write(data)
        tmp.flush()
        tmp.close()

        if suffix == ".pdf":
            loader = PyPDFLoader(tmp.name)
            documents = loader.load()
        elif suffix == ".txt":
            loader = TextLoader(tmp.name, encoding="utf-8")
            documents = loader.load()
        elif suffix == ".docx":
            loader = Docx2txtLoader(tmp.name)
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")

        uploaded_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for document in documents:
            document.metadata["uploaded_file_name"] = file_name
            document.metadata["source"] = file_name
            document.metadata["uploaded_at"] = uploaded_at

        return documents
    finally:
        tmp.close()
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def build_vector_store(chunks):
    print("Building vector store (calls OpenAI embeddings API)...")
    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    ids = [
        f"{chunk.metadata.get('uploaded_file_name', 'document')}-{index}-{uuid4().hex}"
        for index, chunk in enumerate(chunks)
    ]
    vectorstore.add_documents(chunks, ids=ids)
    vectorstore.persist()
    print(f"\u2705 Vector store built with {vectorstore._collection.count()} vectors")


def generate_suggested_prompts(chunks):
    """Ask OpenAI to generate 3 suggested prompts based on document content and store in ChromaDB."""
    sample_text = "\n\n".join(c.page_content for c in chunks[:10])
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Given the following document excerpts, "
                    "generate exactly 3 concise, specific questions a user might want to ask about the content. "
                    "Return ONLY a JSON array of 3 question strings, e.g. [\"Q1\", \"Q2\", \"Q3\"]."
                ),
            },
            {"role": "user", "content": sample_text},
        ],
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("```")
        ).strip()
    prompts = json.loads(raw)

    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    # Store prompts as a special sentinel document in the collection
    from langchain_core.documents import Document
    doc = Document(
        page_content="__suggested_prompts__",
        metadata={"type": "suggested_prompts", "prompts": json.dumps(prompts)},
    )
    vectorstore.add_documents([doc], ids=["__suggested_prompts__"])
    vectorstore.persist()
    print(f"✅ Suggested prompts stored: {prompts}")


def get_suggested_prompts():
    """Retrieve stored suggested prompts from ChromaDB. Returns a list of strings."""
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
        result = vectorstore._collection.get(
            ids=["__suggested_prompts__"], include=["metadatas"]
        )
        metadatas = result.get("metadatas") or []
        if metadatas and metadatas[0].get("prompts"):
            return json.loads(metadatas[0]["prompts"])
    except Exception:
        pass
    return []

def clear_vector_store():
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
    if "vectorstore" in st.session_state:
        del st.session_state.vectorstore

def retrieve_context(vectorstore, query, k=4):
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)
    context = "---".join([doc.page_content for doc in docs])
    return context, docs

def build_rag_system_prompt(context):
    return (
        "You are a helpful assistant. Answer the user's question using ONLY "
        "the information provided in the context below. "
        f"If the answer is not in the context, say: {not_found} "
        "If your answer contains numerical data that could be shown as a table or chart, "
        "describe it briefly in prose but DO NOT format it as a markdown table or list of numbers — "
        "a separate visualization will be generated and displayed automatically. "
        f"Context:{context}"
    )

def system_prompt_with_context(prompt):
    retrieved_docs = []
    st.session_state.vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
    if "vectorstore" in st.session_state:
        context, retrieved_docs = retrieve_context(
            st.session_state.vectorstore, prompt, k=10
        )
        system_prompt = build_rag_system_prompt(context)
    else:
        system_prompt = system_prompt_no_doc
    return system_prompt


def extract_visualization_data(response_text):
    """
    Ask the LLM whether the response contains data suitable for a table or chart.
    Returns a dict with keys:
      - "type": "table" | "bar_chart" | "line_chart" | "none"
      - "title": str
      - "columns": list[str]   (for table/chart)
      - "rows": list[list]     (for table/chart, each inner list matches columns)
    Returns None if the response is not suitable for visualization.
    """
    check_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You analyse assistant responses and decide if they contain data "
                    "that can be displayed as a table or chart. "
                    "If yes, extract the data and return ONLY a JSON object with these keys:\n"
                    '  "type": one of "table", "bar_chart", "line_chart"\n'
                    '  "title": a short descriptive title\n'
                    '  "columns": array of column name strings\n'
                    '  "rows": array of arrays (each inner array matches the columns order, use numbers where applicable)\n'
                    "If the response does NOT contain data suitable for a table or chart, "
                    'return ONLY the JSON object {"type": "none"}. '
                    "Do not include markdown fences or any other text."
                ),
            },
            {"role": "user", "content": response_text},
        ],
    )
    raw = check_response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines() if not line.strip().startswith("```")
        ).strip()
    result = json.loads(raw)
    if result.get("type") == "none":
        return None
    return result
