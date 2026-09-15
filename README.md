<div align="center">

# 🌾 Kisan Saathi
### AI Agricultural Advisor

**Mandi prices and government scheme eligibility — in your own language.**

[![Live Demo](https://img.shields.io/badge/🔗_Live_Demo-kisan--saathi.onrender.com-2ea44f?style=for-the-badge)](https://kisan-saathi-qjjl.onrender.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-4285F4?style=flat-square&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-FF6F00?style=flat-square)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/Tests-19_passing-brightgreen?style=flat-square)](#)
[![Languages](https://img.shields.io/badge/Languages-8%2B-orange?style=flat-square)](#)

</div>

---

Kisan Saathi is a bilingual/multilingual assistant that helps Indian farmers get two things fast: **current mandi (market) price trends** for their crops, and **plain-language answers to "am I eligible for this scheme?"** — grounded in actual government scheme documents, not just an AI's best guess.

Ask by text or voice. Get an answer with the actual source cited.

<br>

## 📑 Table of Contents

| | | |
|---|---|---|
| [1. Overview](#1-overview) | [2. Project Structure](#2-project-structure) | [3. Features](#3-features) |
| [4. API Endpoints](#4-api-endpoints) | [5. Preview](#5-preview) | [6. Architecture Diagram](#6-architecture-diagram) |
| [7. Tech Stack](#7-tech-stack) | [8. Local Deployment](#8-local-deployment) | |

<br>

## 1. Overview

Kisan Saathi answers two kinds of farmer questions, routed automatically to the right specialist agent:

| | |
|---|---|
| 📈 **Price Agent** | Pulls historical mandi price data, returns trends, forecasts, and interactive Plotly charts. |
| 📋 **Scheme Agent (RAG)** | Retrieves the exact relevant passage from PM-KISAN / PMFBY documents via vector search, then asks Gemini to answer *using that retrieved text* — not its general recollection. |

The routing decision is made by an LLM call, with a keyword-based fallback so a Gemini outage never takes the app down.

<div align="center">

| 🌐 Languages | 🏛️ Schemes Covered | 🗺️ States of Price Data | 🧩 RAG Chunks | 🎯 Chunks Retrieved / Query | ✅ Tests |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **8+** | **2** | **5** | **~14** | **Top 3** | **19/19** |

</div>

<br>

## 2. Project Structure

```
kisan-saathi/
├── app.py                 # FastAPI entrypoint (main API)
├── main.py                # Alternate Streamlit UI
├── router.py               # Intent classification + request routing
├── rag_agent.py            # RAG retrieval + scheme eligibility answers
├── price_agent.py          # Mandi price queries
├── build_index.py          # One-time script: chunks + embeds scheme docs into ChromaDB
├── list_models.py          # Diagnostic: lists Gemini models available to your API key
├── load_prices.py          # Loads mandi price CSV into SQLite
├── data/
│   ├── scheme_docs.txt     # Source documents for RAG (PM-KISAN, PMFBY)
│   └── mandi_prices.csv    # Source data for price agent
├── chroma_db/               # Generated vector store (gitignored)
├── mandi.db                 # Generated SQLite price database
├── web/                     # Frontend (HTML/CSS/JS)
├── tests/
│   ├── test_router.py      # Routing logic tests
│   └── test_rag_agent.py   # Retrieval + generation tests
└── requirements.txt
```

<br>

## 3. Features

- 🔍 **Grounded RAG answers** — every scheme answer cites the actual retrieved source chunk, shown to the user as an expandable reference.
- 🌐 **8+ Indian languages** — auto-detected via Unicode script ranges (Devanagari, Tamil, Telugu, Kannada, Gujarati, Bengali, Punjabi, and more).
- 🎙️ **Voice input** — audio transcribed via Gemini, in addition to text.
- 🔀 **Hybrid intent routing** — LLM classification with an automatic keyword fallback, so a Gemini outage degrades gracefully instead of breaking the app.
- 📊 **Interactive price charts** — Plotly visualizations for mandi price trends and forecasts.
- ✅ **Fully tested** — 19 pytest cases covering routing and retrieval, all mocked, running in seconds with no API key or network access.
- ⚠️ **Honest disclaimers** — every eligibility answer is flagged as guidance, not final verification, pointing users to their nearest CSC or bank branch.

<br>

## 4. API Endpoints

<table>
<tr><td>

**`POST /api/ask`**

</td></tr>
<tr><td>

```json
{ "question": "Am I eligible for PM-KISAN?", "language": "en" }
```

`language` is optional — auto-detected from the question text if omitted.
Returns the routed agent, the answer, and (for scheme questions) the retrieved source chunks used to ground the answer.

</td></tr>
</table>

<table>
<tr><td>

**`POST /api/transcribe`**

</td></tr>
<tr><td>

Accepts an audio file upload, returns transcribed text via Gemini.

</td></tr>
</table>

<br>

## 5. Preview

> 🖼️ Add screenshots here — homepage, Scheme Agent answer with cited sources, price trend chart.

<div align="center">

| Homepage | Scheme Agent in Action |
|:---:|:---:|
| *screenshot placeholder* | *screenshot placeholder* |

</div>

<br>

## 6. Architecture Diagram

```
                         User question
                              │
                              ▼
              Language detection (Unicode script matching)
                              │
                              ▼
        Intent Router ── LLM classification (Gemini)
              │                  └── falls back to ── keyword rules
              │                                              │
              ├──────────────────────┬───────────────────────┘
              ▼                      ▼
        Price Agent            Scheme Agent (RAG)
   (SQL query templates              │
    over mandi price data)           ▼
                          1. Embed the question (Gemini embeddings)
                          2. Query ChromaDB for top-3 relevant chunks
                          3. Pass retrieved chunks + question to Gemini
                          4. Return answer + the actual source chunks used
```

Scheme documents are chunked **per-topic** (not fixed-size splitting) so related content — like a full "who is excluded" list — stays together as one retrievable unit. Chunks are embedded once, offline, via `build_index.py`, and stored in a persistent ChromaDB collection — so each live query only needs to embed the short user question, not the whole document corpus.

<br>

## 7. Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| 🖥️ Backend API | FastAPI |
| 🎨 Alternate UI | Streamlit |
| 🧠 LLM / Generation | Google Gemini `gemini-2.5-flash` |
| 🔢 Embeddings | Google Gemini `gemini-embedding-001` |
| 🗂️ Vector Store | ChromaDB |
| 💾 Price Data | SQLite + pandas |
| 📊 Charts | Plotly |
| 🧪 Testing | pytest + unittest.mock |
| ☁️ Deployment | Render |

</div>

<br>

## 8. Local Deployment

```bash
# 1. Clone and install
git clone https://github.com/Savree97/kisan-saathi.git
cd kisan-saathi
python -m venv .venv
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Set up your API key
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
# Get a key at https://aistudio.google.com/apikey

# 3. Build the vector index (rebuild whenever scheme_docs.txt changes)
python build_index.py

# 4. Load price data
python load_prices.py

# 5. Run the app
uvicorn app:app --reload
# or, Streamlit UI:
streamlit run main.py
```

**Run tests:**
```bash
pip install pytest
python -m pytest tests/ -v
```

<br>

---

<div align="center">

### ⚠️ Disclaimer

Kisan Saathi is a demo/portfolio project, **not** an official government service.
Eligibility answers are general guidance based on retrieved scheme text — always confirm details with your local Common Service Centre (CSC) or bank branch before applying.

<br>

**[🔗 Try the Live Demo](https://kisan-saathi-qjjl.onrender.com/)** · **[Report an Issue](https://github.com/Savree97/kisan-saathi/issues)**

</div>
