import os
import pandas as pd
import streamlit as st
from openai import OpenAI
from utils.functions import build_rag_system_prompt, extract_visualization_data, get_suggested_prompts, retrieve_context, system_prompt_with_context, collection_name, embeddings, persist_directory
from langchain_community.vectorstores import Chroma

st.set_page_config(page_title="Chat bot", page_icon="💬")
st.title("💬 Chat bot")


from dotenv import load_dotenv
load_dotenv()

secrets = st.secrets.get("credentials", {})
client = OpenAI(api_key=secrets["API_KEY"])

def has_uploaded_documents():
    """Return True if ChromaDB contains at least one non-sentinel document."""
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
        results = vectorstore._collection.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        return any(m.get("type") != "suggested_prompts" for m in metadatas)
    except Exception:
        return False

if not has_uploaded_documents():
    st.info("📂 No documents uploaded yet. Please go to the **File Uploader** page to upload a document before chatting.")
    st.page_link("pages/5_File_Uploader.py", label="Go to File Uploader", icon="📁")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if st.button("🗑️ Clear Conversation"):
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Show suggested prompts always if available
suggested = get_suggested_prompts()
if suggested:
    st.markdown("**💡 Suggested questions:**")
    cols = st.columns(len(suggested))
    for col, suggestion in zip(cols, suggested):
        with col:
            if st.button(suggestion, use_container_width=True):
                st.session_state.pending_prompt = suggestion
                st.rerun()

# chat_input must always be rendered; pick up pending_prompt only after it renders
typed_prompt = st.chat_input("Ask me anything about CPF Schemes and I will answer you")

prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    system_prompt = system_prompt_with_context(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}]
                     + st.session_state.messages,
            stream=True,
        )
        full_response = st.write_stream(stream)

        # Render a chart/table if the response contains structured data
        viz = None
        try:
            viz = extract_visualization_data(full_response)
        except Exception:
            pass

        if viz:
            df = pd.DataFrame(viz["rows"], columns=viz["columns"])
            st.markdown(f"**{viz['title']}**")
            if viz["type"] == "table":
                st.dataframe(df, use_container_width=True)
            elif viz["type"] == "bar_chart":
                st.bar_chart(df.set_index(df.columns[0]))
            elif viz["type"] == "line_chart":
                st.line_chart(df.set_index(df.columns[0]))

    st.session_state.messages.append({"role": "assistant", "content": full_response})
