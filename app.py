import re
import streamlit as st
from router import route_question, handle_audio_transcription

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False

# ─── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Kisan Sahayak 🌾",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────
# Professional color scheme: Dark blue/teal with clean whites and subtle gradients
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

:root {
    --bg: #0D1B2A;
    --surface: #1B2D45;
    --surface-2: #243B54;
    --sidebar: #0A1628;
    --ink: #E8EDF2;
    --ink-soft: #9BB0C4;
    --ink-faint: #6A7F94;
    --primary: #4FACFE;
    --primary-dark: #2D7FC7;
    --primary-soft: rgba(79, 172, 254, 0.12);
    --teal: #0D9488;
    --teal-soft: rgba(13, 148, 136, 0.14);
    --gold: #F2A93C;
    --gold-soft: rgba(242, 169, 60, 0.12);
    --red: #E2685A;
    --red-soft: rgba(226, 104, 90, 0.12);
    --border: rgba(255,255,255,0.08);
    --border-strong: rgba(255,255,255,0.14);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans Devanagari', -apple-system, Segoe UI, sans-serif;
    font-size: 16px;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background:
        radial-gradient(circle at 50% -10%, rgba(79, 172, 254, 0.08), transparent 55%),
        var(--bg);
}

div[data-testid="stAppViewContainer"] .block-container {
    max-width: 720px;
    margin: 0 auto;
    padding-top: 1.2rem;
}

p, li, span, div[data-testid="stMarkdownContainer"],
div[data-testid="stCaptionContainer"], small, strong {
    color: var(--ink) !important;
    line-height: 1.65;
}
div[data-testid="stCaptionContainer"] { color: var(--ink-soft) !important; }

/* Chat bubbles */
div[data-testid="stChatMessage"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.55rem 0.4rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}

/* Chat input */
div[data-testid="stChatInput"] { background: transparent !important; }
div[data-testid="stChatInput"] > div {
    background: var(--surface) !important;
    border: 2px solid var(--teal) !important;
    border-radius: 16px !important;
    min-height: 52px;
}
div[data-testid="stChatInput"] textarea {
    color: var(--ink) !important;
    font-size: 1.02rem !important;
    caret-color: var(--teal) !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: var(--ink-faint) !important; }
div[data-testid="stChatInput"] button svg { fill: var(--bg) !important; }
div[data-testid="stChatInput"] button { background: var(--teal) !important; border-radius: 10px !important; }

/* Header */
.header-bar {
    display: flex; align-items: center; justify-content: center;
    gap: 0.7rem; padding: 0.4rem 0 0.2rem;
}
.header-icon {
    width: 46px; height: 46px; border-radius: 13px;
    background: linear-gradient(135deg, var(--primary), var(--teal));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; flex-shrink: 0;
}
.header-title {
    font-family: 'Inter', 'Noto Sans Devanagari', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: var(--ink) !important;
    letter-spacing: -0.5px;
    line-height: 1.1;
    background: linear-gradient(135deg, #E8EDF2 0%, #9BB0C4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.header-tagline {
    text-align: center;
    color: var(--ink-soft) !important;
    font-size: 1.0rem;
    font-weight: 400;
    margin: 0.55rem 0 0;
}
.header-underline {
    display: block;
    height: 4px;
    width: 84px;
    background: linear-gradient(90deg, var(--primary), var(--teal));
    border-radius: 6px;
    margin: 0.9rem auto 0;
}

.divider {
    height: 1px;
    background: var(--border);
    border: none;
    margin: 1.3rem 0 1.6rem;
}

/* Route chips */
.chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.32rem 0.85rem;
    border-radius: 999px;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 0.7rem;
}
.chip.price { color: var(--gold) !important; background: var(--gold-soft); }
.chip.scheme { color: var(--teal) !important; background: var(--teal-soft); }

/* Price highlight */
.price-highlight {
    background: var(--surface-2);
    border: 1px solid var(--border-strong);
    border-radius: 16px;
    padding: 1.1rem 1.4rem;
    margin: 0.7rem 0 0.9rem;
    display: flex; align-items: flex-start; gap: 0.9rem;
}
.price-highlight-icon {
    width: 42px; height: 42px; border-radius: 12px; flex-shrink: 0;
    background: var(--gold-soft);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.25rem;
}
.price-highlight-label {
    font-size: 0.8rem; color: var(--ink-soft) !important; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem;
}
.price-highlight-value {
    font-family: 'Inter', sans-serif;
    font-size: 2.15rem; font-weight: 700; color: var(--ink) !important; line-height: 1.15;
}
.delta-pill {
    display: inline-flex; align-items: center; gap: 0.3rem;
    margin-top: 0.5rem; padding: 0.18rem 0.6rem;
    border-radius: 999px; font-weight: 700; font-size: 0.82rem;
}
.delta-pill.up { color: var(--teal) !important; background: var(--teal-soft); }
.delta-pill.down { color: var(--red) !important; background: var(--red-soft); }

/* Plotly chart */
div[data-testid="stPlotlyChart"] {
    background: var(--surface-2);
    border: 1px solid var(--border-strong);
    border-radius: 16px;
    padding: 0.9rem 0.9rem 0.4rem;
    margin-bottom: 0.8rem;
}

/* Scheme answer card */
.scheme-answer-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 5px solid var(--teal);
    border-radius: 0 16px 16px 0;
    padding: 1.15rem 1.4rem;
    margin: 0.5rem 0 0.7rem;
    font-size: 1.02rem;
    line-height: 1.75;
    color: var(--ink) !important;
}

/* Eligibility disclaimer */
.eligibility-disclaimer {
    background: var(--primary-soft);
    border-radius: 12px;
    padding: 0.8rem 1.05rem;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: var(--primary) !important;
    line-height: 1.6;
}

/* Source chunk cards */
.source-chunk {
    background: var(--surface-2);
    border-radius: 12px;
    padding: 0.85rem 1.05rem;
    margin-bottom: 0.6rem;
    font-size: 0.88rem;
    color: var(--ink) !important;
    line-height: 1.6;
}
.source-chunk-title {
    font-weight: 700; color: var(--teal) !important; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;
}

/* SQL box */
.sql-box {
    background: #0A1628; color: var(--teal) !important;
    padding: 0.85rem 1rem; border-radius: 10px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.8rem; white-space: pre-wrap; word-wrap: break-word; line-height: 1.5;
    border: 1px solid var(--border);
}

/* Expanders */
div[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border) !important;
    border-radius: 12px;
}
div[data-testid="stExpander"] summary { color: var(--ink) !important; font-weight: 600; }
div[data-testid="stExpander"] svg { fill: var(--ink-soft) !important; }

/* Buttons */
div[data-testid="stButton"] button {
    border-radius: 999px !important;
    border: 1.5px solid var(--teal) !important;
    background: var(--surface) !important;
    color: var(--teal) !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    min-height: 46px;
}
div[data-testid="stButton"] button:hover {
    background: var(--teal-soft) !important;
    border-color: var(--primary) !important;
}
div[data-testid="stButton"] button:focus-visible {
    outline: 2px solid var(--primary) !important;
    outline-offset: 2px;
}

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--sidebar); }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] {
    color: #D5E0D6 !important;
}
.sidebar-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.35rem; font-weight: 700; color: #FFFFFF !important; margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 0.5rem;
    background: linear-gradient(135deg, #E8EDF2 0%, #9BB0C4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sidebar-lang-chip {
    display: inline-block; background: var(--surface); color: var(--teal) !important;
    padding: 0.22rem 0.7rem; border-radius: 999px; font-size: 0.78rem;
    margin: 0.15rem 0.25rem 0.15rem 0; font-weight: 600;
    border: 1px solid rgba(13, 148, 136, 0.3);
}
section[data-testid="stSidebar"] hr { border-color: var(--border) !important; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background: var(--teal) !important;
    border: none !important;
    color: #0A1628 !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: var(--primary) !important;
}
.sidebar-footnote {
    font-size: 0.76rem; color: var(--ink-faint) !important; line-height: 1.6; margin-top: 0.7rem;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--border);
}

/* Success/Warning/Info boxes */
div[data-testid="stAlert"] {
    background: var(--surface-2) !important;
    border-radius: 12px !important;
    border-left: 4px solid var(--teal) !important;
}
div[data-testid="stAlert"] svg { fill: var(--teal) !important; }
div[data-testid="stAlert"] p { color: var(--ink) !important; }

/* Spinner */
div[data-testid="stSpinner"] > div {
    border-top-color: var(--teal) !important;
    border-right-color: var(--teal) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
    <div class="header-icon">🌾</div>
    <div class="header-title">Kisan Sahayak</div>
</div>
<p class="header-tagline">Mandi prices &amp; government scheme eligibility — ask in your own language</p>
<div class="header-underline"></div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🌾 Kisan Sahayak</div>', unsafe_allow_html=True)
    st.markdown(
        "Ask about **mandi price trends** or **government scheme eligibility** "
        "(PM-KISAN, PMFBY) — by voice or text, in your own language."
    )
    st.markdown("**Languages supported**")
    langs = ["English", "हिंदी", "বাংলা", "தமிழ்", "తెలుగు", "ಕನ್ನಡ", "മലയാളം", "ગુજરાતી", "ਪੰਜਾਬੀ", "ଓଡ଼ିଆ"]
    st.markdown("".join(f'<span class="sidebar-lang-chip">{l}</span>' for l in langs), unsafe_allow_html=True)
    st.markdown("---")
    st.caption("📊 Price data: historical mandi records (not live)")
    st.caption("📋 Scheme data: PM-KISAN & PMFBY official rules")
    st.markdown("---")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown(
        '<div class="sidebar-footnote">Demo project, not an official government service. '
        'Eligibility answers are general guidance — always confirm with your local CSC '
        'or bank branch before applying.</div>',
        unsafe_allow_html=True,
    )

# ─── Session State ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── Constants ───────────────────────────────────────────────────
ELIGIBILITY_DISCLAIMER = (
    "⚠️ This answer is based on the details you've shared and the official scheme rules — "
    "it's a guide, not a final verification. Please confirm your eligibility with your local "
    "Common Service Centre (CSC) or bank branch before applying."
)

# ─── Language Detection ──────────────────────────────────────────
_SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi)
    "bn": (0x0980, 0x09FF),  # Bengali
    "pa": (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    "gu": (0x0A80, 0x0AFF),  # Gujarati
    "or": (0x0B00, 0x0B7F),  # Oriya
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "ml": (0x0D00, 0x0D7F),  # Malayalam
}
_HINGLISH_HINTS = {
    "kya", "hai", "hain", "kitna", "kitne", "kaisa", "kaise", "mein", "ka", "ki", "ke",
    "batao", "bhai", "paisa", "rupaye", "daam", "bhav", "kar", "sakta", "skta", "hu",
    "mai", "mujhe", "chahiye", "kaun", "konsa", "yojna", "yojana",
}

def detect_language(text: str) -> str:
    """Guess the language/script of a question: a two-letter code, or 'en'."""
    for lang, (start, end) in _SCRIPT_RANGES.items():
        if any(start <= ord(ch) <= end for ch in text):
            return lang
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if words & _HINGLISH_HINTS:
        return "hi"
    return "en"

# ─── Helper: Re-theme a Plotly figure to match the app ──────────
def theme_figure(figure):
    """Force the incoming Plotly figure onto the dark app palette with
    balanced margins and legible (light-on-dark) text/gridlines,
    regardless of how it was built upstream."""
    try:
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#D5E0D6", family="Inter, sans-serif", size=12),
            title_font=dict(color="#E8EDF2", size=14),
            margin=dict(l=54, r=28, t=36, b=48),
            xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.14)",
                       linecolor="rgba(255,255,255,0.14)", color="#9BB0C4"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.14)",
                       linecolor="rgba(255,255,255,0.14)", color="#9BB0C4"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#D5E0D6")),
        )
        figure.update_traces(line_color="#0D9488", selector=dict(type="scatter"))
        figure.update_traces(marker_color="#0D9488", selector=dict(type="scatter"))
        figure.update_traces(marker_color="#F2A93C", selector=dict(type="bar"))
    except Exception:
        pass
    return figure

# ─── Helper: Build Answer Text ─────────────────────────────────
def build_answer_text(routed_to, response, language):
    if routed_to == "price_agent":
        hindi = language == "hi"
        if "error" in response:
            return f"⚠️ {'क्वेरी में त्रुटि' if hindi else 'Query error'}: {response['error']}"
        df = response.get("result")
        if df is not None and not df.empty:
            if len(df) == 1 and len(df.columns) == 1:
                return None  # shown via the price highlight tile instead
            elif len(df) == 1:
                parts = [f"**{col}**: {df.iloc[0][col]}" for col in df.columns]
                return " | ".join(parts)
            else:
                return (f"**{len(df)} डेटा पॉइंट** मिले। नीचे चार्ट और डेटा देखें।" if hindi
                        else f"Found **{len(df)} data points**. See the chart and data below.")
        return "इस सवाल के लिए कोई डेटा नहीं मिला।" if hindi else "No data found for this query."
    else:
        return response.get("answer", "Sorry, I couldn't find an answer.")

def get_badge(routed_to):
    if routed_to == "price_agent":
        return '<span class="chip price">📈 Mandi Prices</span>'
    return '<span class="chip scheme">📋 Scheme Info</span>'

def get_avatar(routed_to):
    return "📈" if routed_to == "price_agent" else "🌱"

# ─── Helper: Render Expandable Details ──────────────────────────
def render_details(meta):
    routed_to = meta.get("routed_to")
    response = meta.get("response", {})
    language = meta.get("language", "en")
    hindi = language == "hi"

    if routed_to == "price_agent":
        df = response.get("result")
        figure = response.get("figure")

        if figure is not None:
            st.plotly_chart(theme_figure(figure), use_container_width=True)
        else:
            if df is not None and not df.empty and "error" not in response and len(df) == 1 and len(df.columns) == 1:
                val = df.iloc[0, 0]
                display_val = f"₹{val:,.2f}" if isinstance(val, float) else f"₹{val}"
                pct = response.get("percent_change")
                label = "मूल्य / प्रति क्विंटल" if hindi else "Price / quintal"
                delta_html = ""
                if pct is not None:
                    if pct > 0:
                        delta_html = f'<div class="delta-pill up">▲ {pct:.1f}% {"हाल के रिकॉर्ड में" if hindi else "over recent records"}</div>'
                    elif pct < 0:
                        delta_html = f'<div class="delta-pill down">▼ {abs(pct):.1f}% {"हाल के रिकॉर्ड में" if hindi else "over recent records"}</div>'
                st.markdown(
                    f'<div class="price-highlight">'
                    f'<div class="price-highlight-icon">💰</div>'
                    f'<div>'
                    f'<div class="price-highlight-label">{label}</div>'
                    f'<div class="price-highlight-value">{display_val}</div>'
                    f'{delta_html}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            context_chart = response.get("context_chart")
            if context_chart is not None:
                st.plotly_chart(theme_figure(context_chart), use_container_width=True)

        details_label = "📊 क्वेरी विवरण" if hindi else "📊 Query Details"
        with st.expander(details_label, expanded=False):
            sql = response.get("query", "")
            st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)
            explanation = response.get("explanation", "")
            if explanation:
                st.caption(f"💡 {explanation}")
            result = response.get("result")
            if result is not None and not result.empty:
                st.dataframe(result, use_container_width=True)

    elif routed_to == "rag_agent":
        st.markdown(
            f'<div class="eligibility-disclaimer">{ELIGIBILITY_DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )
        chunks = response.get("retrieved_chunks", [])
        if chunks:
            src_label = "📄 प्रयुक्त स्रोत दस्तावेज़" if hindi else "📄 Source Documents Used"
            with st.expander(src_label, expanded=False):
                for i, chunk in enumerate(chunks):
                    st.markdown(
                        f'<div class="source-chunk">'
                        f'<div class="source-chunk-title">Source {i+1}</div>'
                        f'{chunk.strip()}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

# ─── Render Chat History ────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        avatar = "🧑‍🌾"
    else:
        avatar = get_avatar(msg.get("meta", {}).get("routed_to", ""))
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "assistant":
            routed_to = msg.get("meta", {}).get("routed_to", "")
            st.markdown(get_badge(routed_to), unsafe_allow_html=True)
            if routed_to == "rag_agent":
                st.markdown(f'<div class="scheme-answer-card">{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg["content"]:
                st.markdown(msg["content"])
        else:
            st.markdown(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            render_details(msg["meta"])

# ─── Suggestion Chips (only when chat is empty) ─────────────────
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    cols = st.columns(2)
    suggestions = [
        "What is the trend of wheat prices in Indore?",
        "Am I eligible for PM-KISAN?",
        "क्या मैं PMFBY फसल बीमा ले सकता हूँ?",
        "Average price of tomato in Bhopal?",
    ]
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"suggestion_{i}", use_container_width=True):
            st.session_state.pending_prompt = s
            st.rerun()
    st.markdown("")

# ─── Voice + Text Input ──────────────────────────────────────────
voice_transcript = None
if MIC_AVAILABLE:
    input_col, mic_col = st.columns([6, 1])
    with mic_col:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", just_once=True, key="voice_recorder")
    if audio and audio.get("bytes"):
        with st.spinner("Listening... / सुन रहा हूँ..."):
            voice_transcript = handle_audio_transcription(audio["bytes"])

prompt = st.chat_input("पूछें / Ask your question...")

if not prompt and voice_transcript:
    prompt = voice_transcript

if not prompt and "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(prompt)

    language = detect_language(prompt)

    with st.spinner("Thinking... / सोच रहा हूँ..."):
        result = route_question(prompt, language)

    routed_to = result["routed_to"]
    response = result["response"]
    answer_text = build_answer_text(routed_to, response, language)

    with st.chat_message("assistant", avatar=get_avatar(routed_to)):
        st.markdown(get_badge(routed_to), unsafe_allow_html=True)
        if routed_to == "rag_agent":
            st.markdown(f'<div class="scheme-answer-card">{answer_text}</div>', unsafe_allow_html=True)
        elif answer_text:
            st.markdown(answer_text)
        meta = {"routed_to": routed_to, "response": response, "language": language}
        render_details(meta)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text or "",
        "meta": meta,
    })