"""
Build (or rebuild) the ChromaDB vector store that rag_agent.py retrieves from.

Run this manually whenever data/scheme_docs.txt changes, and once before the
very first run of the app (the existing chroma_db/ folder in the repo was
never actually populated by code, so it gets wiped and rebuilt from scratch
here to guarantee the embeddings match this script's model/dimensions):

    python build_index.py
"""
import os
import re
import shutil

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit(
        "GOOGLE_API_KEY / GEMINI_API_KEY not set in .env — embeddings need it."
    )
genai.configure(api_key=API_KEY)

EMBED_MODEL = "models/gemini-embedding-001"
DOCS_PATH = "data/scheme_docs.txt"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "scheme_docs"


def chunk_scheme_docs(path: str):
    """Split scheme_docs.txt into per-scheme, per-topic chunks.

    The file is a series of schemes separated by a '---' line. Within each
    scheme we split on blank lines, so each chunk stays a coherent topic
    unit (e.g. the whole "who is excluded" bullet list as one chunk, not a
    fragment of it), and we prefix the embedded text with the scheme title
    so a chunk that doesn't literally say "PM-KISAN" still embeds as being
    about PM-KISAN.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    sections = re.split(r"\n-{3,}\n", raw.strip())
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n", 1)
        title = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        scheme_id = re.sub(r"[^a-z0-9]+", "_", title.split("(")[0].strip().lower()).strip("_")
        for i, para in enumerate(paragraphs):
            chunks.append({
                "id": f"{scheme_id}_{i}",
                "scheme": title,
                "text": para,                       # shown to the user / used as generation context
                "embed_text": f"{title}\n\n{para}",  # what actually gets embedded
            })
    return chunks


def build_index():
    if os.path.exists(CHROMA_PATH):
        print(f"Removing stale index at {CHROMA_PATH}/ ...")
        shutil.rmtree(CHROMA_PATH)

    chunks = chunk_scheme_docs(DOCS_PATH)
    print(f"Chunked {DOCS_PATH} into {len(chunks)} chunks.")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.create_collection(COLLECTION_NAME)

    embeddings = []
    for c in chunks:
        res = genai.embed_content(
            model=EMBED_MODEL,
            content=c["embed_text"],
            task_type="retrieval_document",
            title=c["scheme"],
        )
        embeddings.append(res["embedding"])
        print(f"  embedded {c['id']}")

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"scheme": c["scheme"]} for c in chunks],
        embeddings=embeddings,
    )
    print(f"\nIndexed {len(chunks)} chunks into ChromaDB collection "
          f"'{COLLECTION_NAME}' at {CHROMA_PATH}/")


if __name__ == "__main__":
    build_index()