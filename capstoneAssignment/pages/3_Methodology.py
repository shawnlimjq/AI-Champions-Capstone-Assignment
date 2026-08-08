import streamlit as st

st.set_page_config(page_title="Methodology", page_icon="✍🏻", layout="wide")

st.title("Methodology")
st.write("""
    This website is built using Streamlit, a Python framework for creating interactive web applications. The website consists of multiple pages, each serving a specific purpose. The pages are organized in a sidebar navigation menu, allowing users to easily switch between them.

    1) The home page where you will find a login button. There are 2 different kind of users for this website, the admin and the regular user. The admin has access to all pages, including the file uploader page, while the regular user has access to only 3 pages, the home page, about us page and methodology page. The chat bot page is accessible to both admin and regular users.
    2) The about us page where you will find information about the project and the team members who worked on it.
    3) The methodology page where you will find information about the methodology used to build the website.
    4) The chat bot page where you can interact with a chat bot that can answer questions about CPF Schemes. The chat bot uses OpenAI's gpt-4o-mini to generate responses based on the user's input and the context of the conversation. The context will be retrieved from the uploaded documents which has been stored in chromadb. If the user's query is not found in the uploaded documents, the chat bot will reply that it cannot answer the question.
    5) The file uploader page where the admin can upload documents related to CPF Schemes to be stored in a chromadb instance.
    """
)

