import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Methodology", page_icon="✍🏻", layout="wide")

st.title("✍🏻 Methodology")

# ── Helper ──────────────────────────────────────────────────────────────────
def mermaid(diagram: str, height: int = 400):
    """Render a Mermaid diagram using the CDN."""
    components.html(
        f"""
        <div style="background:#1e1e1e; border-radius:8px; padding:16px;">
          <pre class="mermaid" style="background:transparent;">{diagram}</pre>
        </div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
        </script>
        """,
        height=height,
    )


# ── Overview ─────────────────────────────────────────────────────────────────
st.header("Overview")
st.markdown("""
This application is a **CPF Schemes Self-Help Portal** built with [Streamlit](https://streamlit.io).
It allows authorised users to upload CPF-related documents and ask natural-language questions about them.
Answers are grounded in the uploaded content via a **Retrieval-Augmented Generation (RAG)** pipeline
powered by [ChromaDB](https://www.trychroma.com/) and [OpenAI GPT-4o-mini](https://platform.openai.com/docs/models).

The portal has two primary use cases:

| # | Use Case | Who can use it |
|---|----------|----------------|
| 1 | **Document Upload & Indexing** — upload PDF; embed and store them in ChromaDB; auto-generate suggested questions | Admin only |
| 2 | **RAG Chat** — ask questions about the uploaded documents; receive grounded answers optionally visualised as charts or tables | Admin & Regular users |
""")

st.divider()

# ── Technology Stack ──────────────────────────────────────────────────────────
st.header("Technology Stack")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
**Frontend / UI**
- Streamlit — multi-page app with role-based navigation

**Vector Store**
- ChromaDB (local persistent store)
- LangChain `Chroma` wrapper

**Embeddings**
- OpenAI `text-embedding-3-small`
""")
with col2:
    st.markdown("""
**LLM**
- OpenAI `gpt-4o-mini` (chat completions, streaming)

**Document Loaders**
- LangChain `PyPDFLoader`

**Text Splitting**
- LangChain `RecursiveCharacterTextSplitter` (chunk 1000 / overlap 100)
""")

st.divider()

# ── Data Flow ─────────────────────────────────────────────────────────────────
st.header("Data Flow")
st.markdown("""
All persistent state lives in **ChromaDB** — there is no separate database.
Each document chunk is stored with metadata (`uploaded_file_name`, `source`, `uploaded_at`).
A special sentinel document (`id = __suggested_prompts__`) stores the AI-generated suggested questions
so they survive page reloads and new browser sessions.
""")

st.divider()

# ── Use Case 1: Document Upload ───────────────────────────────────────────────
st.header("Use Case 1 — Document Upload & Indexing")
st.markdown("""
An **Admin** uploads one or more **PDF** documents via the file uploader widget
or by clicking the **Load sample file** button (MediShield Life Brochure is pre-bundled).
The application processes each file, splits it into overlapping chunks, embeds each chunk using
OpenAI embeddings, and stores the vectors in ChromaDB.
After indexing, GPT-4o-mini analyses a sample of the chunks and generates three suggested questions
that are also persisted in ChromaDB so the Chat page can display them at any time.
""")

mermaid("""
flowchart TD
    A([Admin opens File Uploader page]) --> B{Use sample file\\nor upload?}
    B -- Sample file button --> C[Read bundled\\nMediShield_Life_Brochure.pdf]
    B -- Manual upload --> D[Select one or more files]
    C --> E{File signature\\nalready indexed?}
    D --> E
    E -- Yes --> F([Show existing upload info & suggested questions])
    E -- No --> G[Load PDF via LangChain\\nPyPDFLoader]
    G --> H[Split into chunks\\nchunk=1000 / overlap=100]
    H --> I[Embed chunks with\\nOpenAI text-embedding-3-small]
    I --> J[Upsert vectors + metadata\\ninto ChromaDB\\nuploaded_file_name, source, uploaded_at]
    J --> K[Sample first 10 chunks]
    K --> L[Ask GPT-4o-mini to generate\\n3 suggested questions]
    L --> M[Store questions as sentinel doc\\nin ChromaDB id=__suggested_prompts__]
    M --> N([Display upload timestamp,\\nfile names & suggested questions])
    J --> N
""", height=1100)

st.divider()

# ── Use Case 2: RAG Chat ──────────────────────────────────────────────────────
st.header("Use Case 2 — RAG Chat")
st.markdown("""
Any logged-in user can navigate to the **Chat Bot** page.
The page first checks ChromaDB for uploaded documents — if none exist the user is prompted
to upload documents first via a direct link to the File Uploader.

Once documents are present, **suggested questions** (generated during upload) are always shown
as clickable buttons above the chat input, regardless of conversation state.

When the user submits a query — either by clicking a suggested question or typing — the application
retrieves the top-10 most relevant chunks from ChromaDB, injects them into the system prompt, and
streams a grounded answer from GPT-4o-mini.
After streaming, a second LLM call checks whether the response contains tabular or chart-worthy
data; if so a chart or table is rendered automatically below the text response.
""")

mermaid("""
flowchart TD
    A([User opens Chat Bot page]) --> B{Documents in\\nChromaDB?}
    B -- No --> C([Show info message +\\nlink to File Uploader])
    B -- Yes --> D[Fetch suggested questions\\nfrom ChromaDB]
    D --> E([Always display suggested\\nquestion buttons + chat input])
    E --> F{User submits a query}
    F -- Clicks suggested button --> G[Set pending_prompt\\nrerun page]
    F -- Types in chat input --> H[Use typed prompt]
    G --> I[Resolve prompt]
    H --> I
    I --> J[Embed query with\\ntext-embedding-3-small]
    J --> K[Retrieve top-10 chunks\\nfrom ChromaDB via cosine similarity]
    K --> L[Build RAG system prompt\\nwith retrieved context]
    L --> M[Stream response from\\nGPT-4o-mini]
    M --> N([Display streamed answer])
    N --> O[Send response to GPT-4o-mini\\nfor visualization check]
    O --> P{Structured data\\ndetected?}
    P -- No --> Q([Suggested questions & chat input\\nremain available])
    P -- Yes, table --> R([Render st.dataframe below answer])
    P -- Yes, bar chart --> S([Render st.bar_chart below answer])
    P -- Yes, line chart --> T([Render st.line_chart below answer])
    R --> Q
    S --> Q
    T --> Q
""", height=1300)

st.divider()

# ── Role-Based Access ─────────────────────────────────────────────────────────
st.header("Role-Based Access Control")
st.markdown("""
User credentials are stored in `.streamlit/secrets.toml`.
The `app.py` navigation layer enforces page visibility based on the `login_role` stored in session state.

| Page | Regular User | Admin |
|------|:---:|:---:|
| Home | ✅ | ✅ |
| About Us | ✅ | ✅ |
| Methodology | ✅ | ✅ |
| Chat Bot | ✅ | ✅ |
| File Uploader | ❌ | ✅ |
""")

