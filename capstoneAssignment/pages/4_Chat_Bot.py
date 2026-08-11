"""
pages/4_Chat_Bot.py
-------------------
RAG-powered chat interface for the CPF Schemes Self-Help Portal.

Features:
- Blocks access and prompts upload if no documents are indexed in ChromaDB.
- Shows document-based suggested questions before any conversation, then
  switches to conversation-aware follow-up suggestions after each response.
- Streams answers from GPT-4o-mini grounded in retrieved document context.
- Automatically renders a table or chart when the response contains structured data.
"""

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from utils.functions import (
    collection_name,
    extract_visualization_data,
    generate_followup_suggestions,
    get_suggested_prompts,
    get_vectorstore,
    system_prompt_with_context,
)

st.set_page_config(page_title="Chat bot", page_icon="💬")
st.title("💬 Chat bot")

load_dotenv()
secrets = st.secrets.get("credentials", {})
client = OpenAI(api_key=secrets.get("API_KEY", os.getenv("API_KEY", "")))


def has_uploaded_documents() -> bool:
    """Return True if ChromaDB contains at least one non-sentinel document."""
    try:
        metadatas = get_vectorstore()._collection.get(include=["metadatas"]).get("metadatas") or []
        return any(m.get("type") != "suggested_prompts" for m in metadatas)
    except Exception:
        return False


# ── Guard: require uploaded documents ────────────────────────────────────────
if not has_uploaded_documents():
    st.info("📂 No documents uploaded yet.")
    if st.session_state.get("login_role") == "admin":
        st.page_link("pages/5_File_Uploader.py", label="Go to File Uploader", icon="📁")
    else:
        st.caption("Please ask an administrator to upload documents before chatting.")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "dynamic_suggestions" not in st.session_state:
    st.session_state.dynamic_suggestions = None

# ── Toolbar ───────────────────────────────────────────────────────────────────
if st.button("🗑️ Clear Conversation"):
    st.session_state.messages = []
    st.session_state.dynamic_suggestions = None
    st.rerun()

# ── Conversation history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("viz"):
            viz = msg["viz"]
            try:
                df = pd.DataFrame(viz["rows"], columns=viz["columns"])
                st.markdown(f"**{viz['title']}**")
                if viz["type"] == "table":
                    st.dataframe(df, use_container_width=True)
                elif viz["type"] == "bar_chart":
                    st.bar_chart(df.set_index(df.columns[0]))
                elif viz["type"] == "line_chart":
                    st.line_chart(df.set_index(df.columns[0]))
            except Exception:
                pass

# ── Suggested questions ───────────────────────────────────────────────────────
# Use conversation-aware follow-ups once the chat has started; fall back to
# document-based suggestions before the first message.
suggested = (
    st.session_state.dynamic_suggestions
    if st.session_state.messages and st.session_state.dynamic_suggestions
    else get_suggested_prompts()
)
if suggested:
    st.markdown("**💡 Suggested questions:**")
    cols = st.columns(len(suggested))
    for col, suggestion in zip(cols, suggested):
        with col:
            if st.button(suggestion, use_container_width=True):
                st.session_state.pending_prompt = suggestion
                st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
# st.chat_input must always be rendered to stay visible.
typed_prompt = st.chat_input("Ask me anything about CPF Schemes and I will answer you")
prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

# ── Handle prompt ─────────────────────────────────────────────────────────────
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    system_prompt = system_prompt_with_context(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
            stream=True,
        )
        full_response = st.write_stream(stream)

        # Render a chart or table if the response contains structured data
        viz = None
        try:
            viz = extract_visualization_data(full_response)
            if viz:
                df = pd.DataFrame(viz["rows"], columns=viz["columns"])
                st.markdown(f"**{viz['title']}**")
                if viz["type"] == "table":
                    st.dataframe(df, use_container_width=True)
                elif viz["type"] == "bar_chart":
                    st.bar_chart(df.set_index(df.columns[0]))
                elif viz["type"] == "line_chart":
                    st.line_chart(df.set_index(df.columns[0]))
        except Exception:
            pass

    # Store viz alongside the message so it persists across reruns
    st.session_state.messages.append({"role": "assistant", "content": full_response, "viz": viz})

    # Update suggested questions based on the latest conversation turn
    try:
        st.session_state.dynamic_suggestions = generate_followup_suggestions(st.session_state.messages)
    except Exception:
        pass

    st.rerun()
