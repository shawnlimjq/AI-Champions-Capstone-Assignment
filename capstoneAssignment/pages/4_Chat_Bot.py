import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Chat bot", page_icon="💬")
st.title("💬 Chat bot")

prompt=st.chat_input("Ask me anything about CPF Schemes and I will answer you", key="input")

if prompt:
    st.write(f"You: {prompt}")