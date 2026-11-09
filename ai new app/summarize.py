"""
Document Summarizer: upload a file, get an AI summary.

Setup:
    pip install streamlit anthropic pypdf python-docx
    export ANTHROPIC_API_KEY="your-key-here"
    streamlit run app.py
"""

import io
from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"  # check Google's docs for the current model name
client = genai.Client()  # reads GEMINI_API_KEY from the environment
import streamlit as st
from docx import Document
from pypdf import PdfReader

MAX_CHARS = 400_000  # rough safety cap so huge files don't blow the context window


def extract_text(uploaded) -> str:
    """Pull plain text out of a PDF, DOCX, or text/markdown file."""
    name = uploaded.name.lower()
    data = uploaded.read()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    return data.decode("utf-8", errors="ignore")  # .txt, .md, etc.


def summarize(uploaded, style: str) -> str:
    name = uploaded.name.lower()

    if name.endswith(".pdf"):
        contents = [
            types.Part.from_bytes(data=uploaded.getvalue(), mime_type="application/pdf"),
            style,
        ]
    else:
        text = extract_text(uploaded)
        if not text.strip():
            raise ValueError("No text found in this file.")
        contents = f"{style}\n\n<document>\n{text[:MAX_CHARS]}\n</document>"

    response = client.models.generate_content(model=MODEL, contents=contents)
    return response.text

# ---------- UI ----------
st.title("📄 AI Summarizer")

style_options = {
    "Short (5 bullets)": "Summarize this document in 5 concise bullet points.",
    "Detailed": "Write a detailed summary of this document, organized by section.",
    "Action items": "List the key takeaways and any action items or deadlines in this document.",
}
choice = st.selectbox("Summary style", list(style_options))

uploaded = st.file_uploader("Upload a document", type=["pdf", "docx", "txt", "md"])
if uploaded and st.button("Summarize"):
    with st.spinner("Reading and summarizing..."):
        try:
            summary = summarize(uploaded, style_options[choice])
            st.subheader("Summary")
            st.write(summary)
            st.download_button("Download summary", summary, file_name="summary.md")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
