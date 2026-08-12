# Kisan Saathi — Setup (read this, nothing else)

## 1. Delete the old copies

In your project folder (`kisan-sahayak`), delete:
- `main.py` (if it exists from before)
- the whole `web` folder (if it exists from before)

## 2. Extract this zip

Extract `kisan_saathi_web.zip` and drag its contents (`main.py` and the `web`
folder) straight into `kisan-sahayak`, so it looks exactly like this:

```
kisan-sahayak\
├── router.py                    (yours — untouched)
├── price_agent.py                 (yours — untouched)
├── rag_agent.py                     (yours — untouched)
├── load_prices.py                     (yours — untouched)
├── mandi.db                             (yours — untouched)
├── data\                                  (yours — untouched)
├── chroma_db\                               (yours — untouched)
├── .env                                       (yours — untouched)
├── main.py                                     <- from this zip
└── web\                                          <- from this zip
    ├── index.html
    ├── css\style.css
    ├── js\app.js
    └── img\hero-farmer.jpg
```

## 3. Install the 3 extra packages (one-time only)

```
.venv\Scripts\activate
pip install fastapi uvicorn python-multipart
```

## 4. Run it

```
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000, hard refresh once (Ctrl+Shift+R).

That's it. Every fix from this conversation (styling, nav cleanup, hero photo,
null-price bug, WAV-based voice transcription) is already baked into these
files. If something still doesn't work, it'll be a real backend error tied
to your machine (missing API key, wrong file location) — send me the
terminal traceback and I'll pinpoint it directly.
