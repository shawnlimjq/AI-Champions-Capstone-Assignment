"""
app.py
------
Entry point for the CPF Schemes Self-Help Portal.

Defines all pages and enforces role-based navigation:
  - Logged-out / unauthenticated: Home, About Us, Methodology
  - Regular user: + Chat Bot
  - Admin: + Chat Bot + File Uploader
"""

import streamlit as st

# ── Startup check: require API key ───────────────────────────────────────────
_api_key = st.secrets.get("credentials", {}).get("API_KEY", "")
if not _api_key:
    st.error(
        "⚠️ **OpenAI API key not configured.**\n\n"
        "Please add your API key to the app secrets:\n"
        "```\n[credentials]\nAPI_KEY = \"sk-...\"\n```\n"
        "On Streamlit Cloud: go to **Settings → Secrets** and add the above."
    )
    st.stop()

home_page = st.Page("pages/1_Home_Page.py", title="Home", default=True)
about_us_page = st.Page("pages/2_About_Us.py", title="About Us")
methodology_page = st.Page("pages/3_Methodology.py", title="Methodology")
chat_bot_page = st.Page("pages/4_Chat_Bot.py", title="Chat Bot")
file_uploader_page = st.Page("pages/5_File_Uploader.py", title="File Uploader")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "login_role" not in st.session_state:
    st.session_state.login_role = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

role = st.session_state.login_role
if role == "admin":
    pages_list = [home_page, about_us_page, methodology_page, chat_bot_page, file_uploader_page]
elif role == "regular":
    pages_list = [home_page, about_us_page, methodology_page, chat_bot_page]
else:
    pages_list = [home_page, about_us_page, methodology_page]

nav = st.navigation(pages_list, position="sidebar", expanded=True)
nav.run()

