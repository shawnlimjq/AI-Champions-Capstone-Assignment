import tempfile
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings(
    model='text-embedding-3-small',
    api_key=os.environ['API_KEY'],)
not_found = "I couldn't find that information in the uploaded document."
system_prompt_no_doc = "You are a helpful assistant."
persist_directory = "vectorstore"
collection_name = "cpf_data"

def process_uploaded_files(files, chunk_size, chunk_overlap):
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
            raise ValueError("Unsupported file type")
        tmp.write(data)
        tmp.flush()
        tmp.close()

        loader = PyPDFLoader(tmp.name)

        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        
        chunks = splitter.split_documents(pages)
        print(f"\nFirst chunk preview:\n{chunks[0].page_content}")
        build_vector_store(chunks, name)
        
        os.remove(tmp.name)

def build_vector_store(chunks, name):

    print("Building vector store (calls OpenAI embeddings API)...")
    vectorstore = Chroma.from_documents(chunks, embeddings, ids = name, collection_name = collection_name, persist_directory=persist_directory)
    print(f"\u2705 Vector store built with {vectorstore._collection.count()} vectors")

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
