"""
Diagnostic: list every model your API key can see, and which ones support
embedContent. Run this once to find out which embedding model name to use
instead of guessing.

    python list_models.py
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GOOGLE_API_KEY / GEMINI_API_KEY not set in .env")
genai.configure(api_key=API_KEY)

print(f"Key loaded, ends in: ...{API_KEY[-6:]}\n")
print("Models this key can see, and what they support:\n")

found_embedding_model = False
for m in genai.list_models():
    print(f"- {m.name}")
    print(f"    supported methods: {m.supported_generation_methods}")
    if "embedContent" in m.supported_generation_methods:
        found_embedding_model = True

print()
if found_embedding_model:
    print("At least one model above supports embedContent — use that exact name "
          "(the full 'models/...' string) as EMBED_MODEL in build_index.py and rag_agent.py.")
else:
    print("No model on this key supports embedContent at all. This usually means "
          "either: (1) the Generative Language API embedding endpoint isn't enabled "
          "for this key/project, or (2) this key is scoped to a product that doesn't "
          "include embeddings (e.g. a restricted or region-limited key). Check "
          "https://aistudio.google.com/apikey for your key's access, or generate a "
          "fresh key there and retry.")