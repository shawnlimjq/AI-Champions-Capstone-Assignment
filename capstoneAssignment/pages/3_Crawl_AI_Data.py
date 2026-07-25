import streamlit as st
from urllib.request import Request, urlopen

from utils.crawler_utils import extract_ai_friendly_text

st.set_page_config(page_title="Crawl AI Data", page_icon="🕸️", layout="wide")

st.title("Crawl a Page for AI-Friendly Content")
st.write("Paste a public URL to fetch the page and extract the main text in a cleaner format for AI tools.")

url = st.text_input("Website URL", placeholder="https://example.com")

if st.button("Crawl Page", type="primary"):
    if not url.strip():
        st.warning("Please enter a URL before crawling.")
    else:
        try:
            request = Request(url.strip(), headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=20) as response:
                content_type = response.headers.get_content_type()
                if "html" not in content_type:
                    st.error("The URL does not appear to return HTML content.")
                    st.stop()

                html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")

            cleaned_text = extract_ai_friendly_text(html)

            if cleaned_text:
                st.success("Content extracted successfully.")
                st.text_area("AI-friendly extracted text", cleaned_text, height=400)

                st.download_button(
                    label="Download as .txt",
                    data=cleaned_text,
                    file_name="extracted_content.txt",
                    mime="text/plain",
                )
            else:
                st.info("No readable content was found on the page.")

        except Exception as exc:
            st.error(f"Unable to crawl the website: {exc}")
