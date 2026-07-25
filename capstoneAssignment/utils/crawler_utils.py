import re
from html import unescape
from bs4 import BeautifulSoup


def extract_ai_friendly_text(html: str) -> str:
    """Extract a cleaner, AI-friendly text version of HTML content."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for tag in soup(["header", "nav", "footer", "aside"]):
        tag.decompose()

    text = soup.get_text("\n")
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text
