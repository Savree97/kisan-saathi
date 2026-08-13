import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

LANG_NAMES = {
    "hi": "Hindi (Devanagari script)", "kn": "Kannada (Kannada script)",
    "te": "Telugu (Telugu script)", "ta": "Tamil (Tamil script)",
    "pa": "Punjabi (Gurmukhi script)", "gu": "Gujarati (Gujarati script)",
    "bn": "Bengali (Bengali script)", "en": "English"
}

def generate_scheme_answer(question: str, language: str = "en") -> str:
    target_lang = LANG_NAMES.get(language, "English")
    
    # 1. Attempt primary Gemini generation
    if API_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
You are a friendly agricultural scheme advisor for Indian farmers. 
The user asked in {target_lang}. You MUST answer strictly in {target_lang}. Do NOT output English.

**REQUIRED RULES FOR PMFBY:**
If the user asks about insurance, PMFBY, or premiums, ALWAYS include these exact numbers:
- Kharif Crops: 2.0% of sum insured.
- Rabi Crops: 1.5% of sum insured.
- Commercial/Horticultural Crops: 5.0% of sum insured.

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

    # 2. Dynamic Fallback (429 or timeout error)
    # This tries to summarize the specific question politely instead of a hardcoded paragraph
    if API_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            fallback_prompt = f"""
The user asked: "{question}" in {target_lang}.
The main AI server is temporarily busy. Give a short, polite reply in {target_lang} stating the server is busy.
IMPORTANT: If the question is about PMFBY, tell them Kharif=2%, Rabi=1.5%, Commercial=5%.
"""
            res = model.generate_content(fallback_prompt)
            if res and res.text:
                return res.text
        except Exception:
            pass

    # 3. Absolute Last Resort (If all APIs crash)
    if language == "hi":
        return "क्षमा करें, सर्वर व्यस्त है। कृपया कुछ क्षण बाद पुनः प्रयास करें। (PMFBY: खरीफ 2%, रबी 1.5%, वाणिज्यिक 5%)"
    elif language == "pa":
        return "ਮਾਫ ਕਰਨਾ, ਸਰਵਰ ਵਿਅਸਤ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਬਾਅਦ ਵਿੱਚ ਕੋਸ਼ਿਸ਼ ਕਰੋ। (PMFBY: ਖਰੀਫ 2%, ਰੱਬੀ 1.5%, ਵਪਾਰਕ 5%)"
    elif language == "kn":
        return "ಕ್ಷಮಿಸಿ, ಸರ್ವರ್ ಬಿಡುವಿಲ್ಲದಿದೆ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ. (PMFBY: ಖರೀಫ್ 2%, ರಬಿ 1.5%, ವಾಣಿಜ್ಯ 5%)"
    
    return "Sorry, the server is busy. Please try again later. (PMFBY: Kharif 2%, Rabi 1.5%, Commercial 5%)"

def answer_eligibility_question(question: str, language: str = "en"):
    return {
        "question": question,
        "retrieved_chunks": [],
        "answer": generate_scheme_answer(question, language)
    }