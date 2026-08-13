import os
from typing import List

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

EMBED_MODEL = "models/gemini-embedding-001"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "scheme_docs"
TOP_K = 3

LANG_NAMES = {
    "hi": "Hindi (Devanagari script)", "kn": "Kannada (Kannada script)",
    "te": "Telugu (Telugu script)", "ta": "Tamil (Tamil script)",
    "pa": "Punjabi (Gurmukhi script)", "gu": "Gujarati (Gujarati script)",
    "bn": "Bengali (Bengali script)", "en": "English"
}

_collection = None


def _get_collection():
    """Lazily connect to the persisted ChromaDB collection built by build_index.py.
    Cached at module level so we don't reopen the sqlite store on every request."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def retrieve_chunks(question: str, top_k: int = TOP_K) -> List[str]:
    """Embed the question and pull the top_k most relevant chunks from ChromaDB.

    Returns [] instead of raising if the index or API key isn't available, so
    the caller can fall back gracefully rather than crashing the whole request.
    Run `python build_index.py` first if this always comes back empty — it
    means chroma_db/ hasn't been built yet (or was built with a different
    embedding model).
    """
    if not API_KEY:
        return []
    try:
        collection = _get_collection()
    except Exception as e:
        print(f"ChromaDB collection unavailable (did you run build_index.py?): {e}")
        return []

    try:
        q_embed = genai.embed_content(
            model=EMBED_MODEL,
            content=question,
            task_type="retrieval_query",
        )["embedding"]
    except Exception as e:
        print(f"Query embedding failed: {e}")
        return []

    try:
        results = collection.query(query_embeddings=[q_embed], n_results=top_k)
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"ChromaDB query failed: {e}")
        return []


def generate_scheme_answer(question: str, retrieved_chunks: List[str], language: str = "en") -> str:
    target_lang = LANG_NAMES.get(language, "English")
    context = "\n\n---\n\n".join(retrieved_chunks) if retrieved_chunks else ""

    if API_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            if context:
                prompt = f"""
You are a friendly agricultural scheme advisor for Indian farmers.
Answer the user's question using ONLY the context below. If the context does
not contain the answer, say so honestly instead of guessing or making up numbers.
The user asked in {target_lang}. You MUST answer strictly in {target_lang}. Do NOT output English.

Context:
{context}

User Question: {question}
"""
            else:
                # No retrieved context (index not built yet, or nothing matched closely
                # enough) — say so instead of quietly inventing figures.
                prompt = f"""
You are a friendly agricultural scheme advisor for Indian farmers.
No reference document context was available for this question, so answer
briefly from general knowledge and clearly tell the user this specific answer
is not verified against the official scheme documents. The user asked in
{target_lang}. You MUST answer strictly in {target_lang}. Do NOT output English.

User Question: {question}
"""
            res = model.generate_content(prompt, safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
            })
            if res and res.text:
                return res.text
        except Exception as e:
            print(f"Gemini Primary API Error: {e}")

    # Last resort if generation itself failed (API down, quota, etc.)
    fallback = {
        "hi": "क्षमा करें, सर्वर व्यस्त है। कृपया कुछ क्षण बाद पुनः प्रयास करें।",
        "pa": "ਮਾਫ ਕਰਨਾ, ਸਰਵਰ ਵਿਅਸਤ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਬਾਅਦ ਵਿੱਚ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "kn": "ಕ್ಷಮಿಸಿ, ಸರ್ವರ್ ಬಿಡುವಿಲ್ಲದಿದೆ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.",
    }
    return fallback.get(language, "Sorry, the server is busy. Please try again later.")


def answer_eligibility_question(question: str, language: str = "en"):
    retrieved_chunks = retrieve_chunks(question)
    return {
        "question": question,
        "retrieved_chunks": retrieved_chunks,
        "answer": generate_scheme_answer(question, retrieved_chunks, language),
    }