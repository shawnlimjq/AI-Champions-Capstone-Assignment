import streamlit as st

home_page = st.Page("pages/1_Home_Page.py", title="Home", default=True)
about_us_page = st.Page("pages/2_About_Us.py", title="About Us")
crawl_ai_page = st.Page("pages/3_Crawl_AI_Data.py", title="Crawl AI Data")
# admin_page = st.Page("admin.py", title="Admin Panel", icon=":gear:")
pages_list = [home_page, about_us_page, crawl_ai_page]


nav = st.navigation(
    pages_list,
    position="sidebar", # Can also be "top" or "hidden"
    expanded=True
)
nav.run()
