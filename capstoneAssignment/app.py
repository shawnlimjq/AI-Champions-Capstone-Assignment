import streamlit as st

home_page = st.Page("pages/1_Home_Page.py", title="Home", default=True)
about_us_page = st.Page("pages/2_About_Us.py", title="About Us")
crawl_ai_page = st.Page("pages/3_Crawl_AI_Data.py", title="Crawl AI Data")
chat_bot_page = st.Page("pages/4_Chat_Bot.py", title="Chat Bot")
# admin_page = st.Page("admin.py", title="Admin Panel", icon=":gear:")
pages_list = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "login_role" not in st.session_state:
    st.session_state.login_role = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = ""



if st.session_state.login_role =="":
    # Public layout for logged-out users
    pages_list = [home_page, about_us_page]
elif st.session_state.login_role == "regular":
    # User-only layout
    pages_list = [home_page, about_us_page, chat_bot_page]
elif st.session_state.login_role == "admin":
    # Admin layout can see everything
    pages_list = [home_page, about_us_page, crawl_ai_page, chat_bot_page]

# 4. Generate the navigation sidebar and run the page
nav = st.navigation(
    pages_list,
    position="sidebar", # Can also be "top" or "hidden"
    expanded=True
)
nav.run()

