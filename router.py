import os
import google.generativeai as genai
from dotenv import load_dotenv

from price_agent import answer_price_question
from rag_agent import answer_eligibility_question

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

INTENT_MODEL = "gemini-2.5-flash"

INTENT_PROMPT = """You are an intent router for a farmer-assistant app with exactly two agents:

- price_agent: handles questions about mandi (market) prices, price trends, price
  forecasts/history for crops in specific locations.
- rag_agent: handles questions about government scheme eligibility, subsidies,
  crop insurance, or rules — e.g. PM-KISAN, PMFBY, premiums, eligibility criteria.

Classify the user's question into exactly one of these two labels.
Respond with ONLY the label text, nothing else: either "price_agent" or "rag_agent".

Question: {question}
"""


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


def classify_intent_keywords(query_text: str) -> str:
    """Rule-based fallback classifier. Used when the LLM call fails, times out,
    or returns something we don't recognize — keeps routing working even if
    Gemini is down, rather than the whole request failing."""
    q_clean = query_text.casefold()

    scheme_keywords = [
        "pmfby", "pm-kisan", "pm kisan", "pmkisan", "insurance", "subsidy", "eligible",
        "eligibility", "scheme", "rules", "premium", "kharif", "rabi", "पात्र", "योजना", "बीमा", "ಅರ್ಹತೆ"
    ]
    if any(kw in q_clean for kw in scheme_keywords):
        return "rag_agent"

    price_keywords = [
        "price", "prices", "mandi", "rate", "modal", "quintal", "trend", "bhav",
        "भाव", "दाम", "ट्रेंड", "प्राइस", "सोयाबीन", "गेहूं", "टमाटर", "bhopal", "punjab"
    ]
    if any(kw in q_clean for kw in price_keywords):
        return "price_agent"

    if any(ch in query_text for ch in ["गेहूं", "टमाटर", "भाव", "₹"]):
        return "price_agent"

    return "rag_agent"


def classify_intent(query_text: str) -> str:
    """LLM-based intent classification via Gemini, with an automatic fallback
    to keyword matching if the API call fails or returns an unexpected label."""
    if API_KEY:
        try:
            model = genai.GenerativeModel(INTENT_MODEL)
            res = model.generate_content(
                INTENT_PROMPT.format(question=query_text),
                generation_config={"temperature": 0},
            )
            label = (res.text or "").strip().strip('"').strip("'").casefold()
            if label in ("price_agent", "rag_agent"):
                return label
            print(f"Intent classifier returned unrecognized label {label!r}, falling back to keywords.")
        except Exception as e:
            print(f"Gemini intent classification failed, falling back to keywords: {e}")

    return classify_intent_keywords(query_text)


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