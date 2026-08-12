# Kisan Saathi - AI Agricultural Advisor

A multilingual AI-powered portal for Indian farmers to check Mandi prices and Government Scheme eligibility.

## Features
- 🤖 **RAG-based AI Chatbot** for schemes (PM-KISAN, PMFBY, KCC)
- 📈 **Mandi price analytics** with dynamic Plotly graphs and 14-day price forecasts
- 🌐 **Multilingual support** (English, Hindi, Punjabi, Kannada, Telugu, and more)
- 🎤 **Voice input support** for farmers
- 💪 **Resilient Architecture**: Gracefully degrades to local fallbacks if the AI API hits rate limits

## Live Demo
🚀 [Click here to view the live app](https://kisan-saathi.onrender.com) *(Deploying soon!)*

## Tech Stack
- **Backend:** FastAPI
- **AI Model:** Google Gemini API (with local fallback handling)
- **Database:** SQLite (mandi.db) & ChromaDB
- **Visualization:** Plotly
- **Deployment:** Render
