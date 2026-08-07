import os
import streamlit as st
from openai import OpenAI
from utils.functions import build_rag_system_prompt, retrieve_context, system_prompt_with_context

st.set_page_config(page_title="Chat bot", page_icon="💬")
st.title("💬 Chat bot")


from dotenv import load_dotenv
load_dotenv()


client = OpenAI(api_key=os.environ["API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("🗑️ Clear Conversation"):
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask me anything about CPF Schemes and I will answer you"):
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

    st.session_state.messages.append({"role": "assistant", "content": full_response})


