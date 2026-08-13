import os
import google.generativeai as genai
from dotenv import load_dotenv

from price_agent import answer_price_question
from rag_agent import answer_eligibility_question

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def handle_audio_transcription(audio_bytes: bytes) -> str:
    if not API_KEY:
        return "Audio transcription requires a Gemini API Key."
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = "Transcribe this audio precisely in its native spoken script. Do not add commentary."
        response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
        return response.text.strip()
    except Exception:
        return "Audio transcription failed."

def classify_intent(query_text: str) -> str:
    q_clean = query_text.casefold()

    # 1. Strict Scheme/Insurance Priority (BLOCKS price matching)
    scheme_keywords = [
        "pmfby", "pm-kisan", "pm kisan", "pmkisan", "insurance", "subsidy", "eligible", 
        "eligibility", "scheme", "rules", "premium", "kharif", "rabi", "पात्र", "योजना", "बीमा", "ಅರ್ಹತೆ"
    ]
    if any(kw in q_clean for kw in scheme_keywords):
        return "rag_agent"

    # 2. Price/Mandi Intent
    price_keywords = [
        "price", "prices", "mandi", "rate", "modal", "quintal", "trend", "bhav", 
        "भाव", "दाम", "ट्रेंड", "प्राइस", "सोयाबीन", "गेहूं", "टमाटर", "bhopal", "punjab"
    ]
    if any(kw in q_clean for kw in price_keywords):
        return "price_agent"
    
    # 3. Script check fallback for pure regional languages
    if any(ch in query_text for ch in ["गेहूं", "टमाटर", "भाव", "₹"]):
        return "price_agent"
    
    return "rag_agent"

def route_question(user_input: str, language: str = "en"):
    try:
        routed_to = classify_intent(user_input)
    except Exception:
        routed_to = "rag_agent"

    try:
        if routed_to == "price_agent":
            response_data = answer_price_question(user_input, language)
        else:
            response_data = answer_eligibility_question(user_input, language)
    except Exception as e:
        response_data = {"error": f"Agent execution failed: {str(e)}"}

    return {
        "routed_to": routed_to,
        "response": response_data,
    }