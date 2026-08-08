import tempfile
import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings(
    model='text-embedding-3-small',
    api_key=st.secrets["API_KEY"],)
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

        for document in documents:
            document.metadata["uploaded_file_name"] = file_name
            document.metadata["source"] = file_name

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
        f"If the answer is not in the context, say: {not_found}"
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
