import json
import os
import unicodedata
from typing import Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from router import route_question, handle_audio_transcription
import pandas as pd

app = FastAPI(title="Kisan Saathi API")

def detect_language(text: str) -> str:
    """Accurate Unicode block detection for Indian scripts"""
    if not text:
        return "en"
    for ch in text:
        cat = unicodedata.category(ch)
        # Filter out punctuation/numbers/symbols, focus on letters
        if cat not in ('Lo', 'Ll', 'Lu'):
            continue
        code = ord(ch)
        if 0x0900 <= code <= 0x097F: return "hi"  # Hindi/Marathi
        if 0x0C80 <= code <= 0x0CFF: return "kn"  # Kannada
        if 0x0C00 <= code <= 0x0C7F: return "te"  # Telugu
        if 0x0B80 <= code <= 0x0BFF: return "ta"  # Tamil
        if 0x0A00 <= code <= 0x0A7F: return "pa"  # Punjabi
        if 0x0A80 <= code <= 0x0AFF: return "gu"  # Gujarati
        if 0x0980 <= code <= 0x09FF: return "bn"  # Bengali
    return "en"

def serialize_price_response(response: dict) -> dict:
    """Helper to serialize DataFrames and Plotly figures for JSON API"""
    out = {
        "query": response.get("query"),
        "explanation": response.get("explanation"),
        "error": response.get("error"),
        "percent_change": response.get("percent_change"),
        "forecast_stats": response.get("forecast_stats", {}),
        "result": [],
        "columns": [],
        "figure": None,
    }
    df = response.get("result")
    if df is not None and not df.empty:
        out["result"] = json.loads(df.to_json(orient="records", date_format="iso"))
        out["columns"] = list(df.columns)
    fig = response.get("figure")
    if fig is not None:
        out["figure"] = json.loads(fig.to_json())
    return out

class AskRequest(BaseModel):
    question: str
    language: Optional[str] = None

@app.post("/api/ask")
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        return {"error": "Empty question provided."}
    
    language = req.language or detect_language(question)
    
    try:
        result = route_question(question, language)
        routed_to = result["routed_to"]
        response = result["response"]

        # Construct Answer Text for Frontend
        answer_text = "No data found for this query."
        if routed_to == "price_agent":
            if "error" in response and response["error"]:
                answer_text = f"⚠️ Query error: {response['error']}"
            else:
                df = response.get("result")
                stats = response.get("forecast_stats", {})
                if df is not None and not df.empty:
                    forecast_msg = ""
                    if stats.get("14d_forecast_price"):
                        forecast_msg = f"\n\n🔮 **14-Day Trend Forecast:** ₹{stats['14d_forecast_price']}/quintal ({stats.get('trend_direction', 'stable')} trajectory)."
                    if "modal_price" in df.columns and len(df) == 1:
                        val = df.iloc[0]["modal_price"]
                        val_str = f"₹{val:,.2f}" if isinstance(val, (int, float)) else str(val)
                        answer_text = f"Average modal price: **{val_str}** per quintal.{forecast_msg}"
        else:
            answer_text = response.get("answer", "Sorry, I couldn't find an answer.")

        return {
            "routed_to": routed_to,
            "language": language,
            "badge": "Mandi Prices & Analytics" if routed_to == "price_agent" else "Scheme Intelligence",
            "answer_text": answer_text,
            "response": serialize_price_response(response) if routed_to == "price_agent" else response,
        }

    except Exception as e:
        return {
            "routed_to": "error",
            "language": language,
            "badge": "System Error",
            "answer_text": "Internal server error processing your request. Please try again.",
            "response": {"error": str(e)}
        }

@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if len(audio_bytes) < 3000:
        return {"text": "", "error": "Recording too short. Please hold the mic button and speak clearly."}
    try:
        text = handle_audio_transcription(audio_bytes)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": f"Transcription failed: {str(e)}"}

if os.path.exists("web"):
    app.mount("/assets", StaticFiles(directory="web"), name="assets")

@app.get("/")
def serve_index():
    if os.path.exists("web/index.html"):
        return FileResponse("web/index.html")
    return {"status": "Kisan Saathi API is running."}