import streamlit as st

st.set_page_config(page_title="About Us", page_icon="👨🏻‍💻")

st.markdown("# About Us")
st.write(
    """
    This project is a one-stop access to CPF policy eligibility and details. Admins can upload documents regarding the different CPF policies. Users will be able to access the AI chatbot to have their queries regarding the CPF policies answered.

    Problem Statement:
    CPF members are overwhelmed by a proliferation of policies spread across multiple portals and documents, making it hard to determine which policies they are eligible for and to locate exact policy details, terms, and how to claim. This fragmentation leads to confusion, wasted time, and missed benefits as members search across sources. CPF ambassadors may not have the right knowledge to answer member queries, further complicating support. How might we help members quickly determine which CPF policies they are eligible for and access clear, up-to-date policy details in a single, reliable place?

    Objectives:
    - Users of the chatbot will have a faster and more accessible way to get answers about eligible policies, without needing to navigate through multiple pages on government websites or wait for assistance from helplines.

    - By surfacing clear and consistent information, the chatbot delivers direct answers drawn from publicly available sources, rather than leaving users to interpret lengthy policy text on their own.

    - This chatbot is intended for use whenever CPF members need to find an eligible policy or explore a category of policies, such as Healthcare. CPF ambassadors can also use it to quickly retrieve information when addressing members' queries on the ground.

    Data Sources (Samples can be found at https://github.com/shawnlimjq/AI-Champions-Capstone-Assignment/tree/main/capstoneAssignment/sample_files):
    - PDFs from the CPF Board website (https://www.cpf.gov.sg/)
    
    Features:
    - Admins can upload documents regarding the different CPF policies.
    - Users will be able to access the AI chatbot to have their queries regarding the CPF policies answered.

    Done By:
    Shawn Lim (6672486Y) and Wang Jian (6855198C)
    """
)

