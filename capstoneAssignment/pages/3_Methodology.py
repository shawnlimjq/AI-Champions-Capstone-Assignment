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
""", height=1600)

st.divider()

# ── Use Case 2: RAG Chat ──────────────────────────────────────────────────────
st.header("Use Case 2 — RAG Chat")
st.markdown("""
Any logged-in user can navigate to the **Chat Bot** page.
The page first checks ChromaDB for uploaded documents — if none exist the user is prompted
to upload documents first (admins get a direct link; regular users see an advisory message).

**Suggested questions** are always displayed above the chat input:
- **Before the first message** — 3 document-based questions generated during upload and stored in ChromaDB.
- **After each response** — 3 conversation-aware follow-up questions generated by GPT-4o-mini from
  the last 3 turns of chat history, replacing the previous suggestions dynamically.

When the user submits a query — by clicking a suggestion button or typing — the application
retrieves the top-10 most relevant chunks from ChromaDB, injects them into the RAG system prompt, and
streams a grounded answer from GPT-4o-mini.

After streaming, a second LLM call checks whether the response contains structured (tabular or chart-worthy)
data. If so, the chart or table is rendered below the answer **and stored in session state** alongside
the message text so it persists across page reruns and navigation.
""")

mermaid("""
flowchart TD
    A([User opens Chat Bot page]) --> B{Documents in\\nChromaDB?}
    B -- No, admin --> C([Show link to File Uploader])
    B -- No, regular user --> D([Show advisory message])
    B -- Yes --> E[Fetch document-based suggestions\\nfrom ChromaDB sentinel doc]
    E --> F([Display suggestion buttons + chat input])
    F --> G{User submits a query}
    G -- Clicks suggestion button --> H[Set pending_prompt & rerun]
    G -- Types in chat input --> I[Use typed prompt]
    H --> J[Resolve prompt from session state]
    I --> J
    J --> K[Embed query with\\ntext-embedding-3-small]
    K --> L[Retrieve top-10 chunks\\nfrom ChromaDB via cosine similarity]
    L --> M[Build RAG system prompt\\nwith retrieved context]
    M --> N[Stream response from GPT-4o-mini]
    N --> O([Display streamed answer])
    O --> P[Send response to GPT-4o-mini\\nfor visualization check]
    P --> Q{Structured data\\ndetected?}
    Q -- Yes, table --> R([Render st.dataframe\\nbelow answer])
    Q -- Yes, bar chart --> S([Render st.bar_chart\\nbelow answer])
    Q -- Yes, line chart --> T([Render st.line_chart\\nbelow answer])
    Q -- No --> U[Store message + viz=None\\nin session state]
    R --> V[Store message + viz dict\\nin session state]
    S --> V
    T --> V
    V --> W[Generate 3 follow-up suggestions\\nfrom last 3 chat turns via GPT-4o-mini]
    U --> W
    W --> X([Update suggestion buttons\\nwith conversation-aware questions])
    X --> F
""", height=2200)

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

