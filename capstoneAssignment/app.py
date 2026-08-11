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

