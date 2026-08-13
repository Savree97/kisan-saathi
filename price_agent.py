import os
import re
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()
DB_NAME = "mandi.db"

# Unicode-Safe Entity Maps
COMMODITY_MAP = {
    "tomato": "Tomato", "टमाटर": "Tomato", "टोमेटो": "Tomato", "tamatar": "Tomato",
    "soybean": "Soybean", "सोयाबीन": "Soybean", "soya": "Soybean",
    "rice": "Rice", "चावल": "Rice", "राइस": "Rice", "chawal": "Rice",
    "onion": "Onion", "प्याज": "Onion", "अनियन": "Onion", "pyaj": "Onion",
    "wheat": "Wheat", "गेहूं": "Wheat", "व्हीट": "Wheat", "gehu": "Wheat"
}

LOCATION_MAP = {
    "bhopal": "Bhopal", "भोपाल": "Bhopal",
    "indore": "Indore", "इंदौर": "Indore",
    "ujjain": "Ujjain", "उज्जैन": "Ujjain",
    "punjab": "Punjab", "पंजाब": "Punjab",
    "maharashtra": "Maharashtra", "महाराष्ट्र": "Maharashtra"
}

def extract_entities(question: str):
    """Match commodity/location as whole words, not raw substrings.
    (Plain `in` matching previously let "rice" match inside "prices".)
    """
    q_normalized = question.casefold()
    matched_comm = "Wheat"
    matched_loc = None

    for k, v in COMMODITY_MAP.items():
        if re.search(rf"\b{re.escape(k)}\b", q_normalized):
            matched_comm = v
            break

    for k, v in LOCATION_MAP.items():
        if re.search(rf"\b{re.escape(k)}\b", q_normalized):
            matched_loc = v
            break

    return matched_comm, matched_loc

def compute_price_analytics(df: pd.DataFrame, price_col: str = "modal_price", date_col: str = "date"):
    if df.empty or date_col not in df.columns or price_col not in df.columns:
        return df, {}

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col)

    df["7d_MA"] = df[price_col].rolling(window=7, min_periods=1).mean()

    latest_price = float(df[price_col].iloc[-1])
    earliest_price = float(df[price_col].iloc[0])
    pct_change = ((latest_price - earliest_price) / earliest_price * 100) if earliest_price else 0.0

    forecast_stats = {
        "latest_price": round(latest_price, 2),
        "percent_change": round(pct_change, 2),
        "trend_direction": "stable"
    }

    if len(df) >= 3:
        df["day_index"] = (df[date_col] - df[date_col].min()).dt.days
        x = df["day_index"].values
        y = df[price_col].values
        slope, intercept = np.polyfit(x, y, 1)
        future_day = x[-1] + 14
        projected_price = (slope * future_day) + intercept
        forecast_stats["14d_forecast_price"] = round(float(projected_price), 2)
        if slope > 0.5: forecast_stats["trend_direction"] = "upward"
        elif slope < -0.5: forecast_stats["trend_direction"] = "downward"
        
    return df, forecast_stats

def generate_historical_context_chart(commodity: str, location: str = None):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        if location:
            sql = """
                SELECT date, AVG(modal_price) as modal_price 
                FROM prices 
                WHERE commodity LIKE ? 
                AND (market LIKE ? OR state LIKE ?) 
                GROUP BY date ORDER BY date ASC;
            """
            df_hist = pd.read_sql_query(sql, conn, params=(f'%{commodity}%', f'%{location}%', f'%{location}%'))
        else:
            sql = """
                SELECT date, AVG(modal_price) as modal_price 
                FROM prices 
                WHERE commodity LIKE ? 
                GROUP BY date ORDER BY date ASC;
            """
            df_hist = pd.read_sql_query(sql, conn, params=(f'%{commodity}%',))
        conn.close()
    except Exception:
        if conn: conn.close()
        return None, {}

    if df_hist.empty and location:
        return generate_historical_context_chart(commodity, None)

    if df_hist.empty:
        return None, {}

    df_hist, stats = compute_price_analytics(df_hist)

    loc_label = location if location else "All Regions"
    try:
        fig = px.line(
            df_hist,
            x="date",
            y=["modal_price", "7d_MA"],
            title=f"Price Trend & Moving Average ({commodity} - {loc_label})",
            labels={"value": "Price (Rs./quintal)", "date": "Date", "variable": "Metric"},
            markers=True
        )
        fig.update_layout(template="plotly_white", hovermode="x unified")
    except Exception:
        return None, {}

    return fig, stats

def answer_price_question(question: str, language: str = "en"):
    matched_comm, matched_loc = extract_entities(question)
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        if matched_loc:
            sql = """
                SELECT commodity, market, state, AVG(modal_price) as modal_price 
                FROM prices 
                WHERE commodity LIKE ? 
                AND (market LIKE ? OR state LIKE ?) 
                GROUP BY commodity;
            """
            df_result = pd.read_sql_query(sql, conn, params=(f'%{matched_comm}%', f'%{matched_loc}%', f'%{matched_loc}%'))
            explanation = f"Query executed for commodity='{matched_comm}', location='{matched_loc}'."
        else:
            sql = """
                SELECT commodity, state, AVG(modal_price) as modal_price 
                FROM prices 
                WHERE commodity LIKE ? 
                GROUP BY commodity;
            """
            df_result = pd.read_sql_query(sql, conn, params=(f'%{matched_comm}%',))
            explanation = f"Query executed for commodity='{matched_comm}' across available regions."
        conn.close()
    except Exception as e:
        if conn: conn.close()
        return {"query": "SELECT...", "explanation": "Error running query", "error": str(e), "result": None, "figure": None}

    fig_obj, stats = generate_historical_context_chart(matched_comm, matched_loc)

    return {
        "query": sql,
        "explanation": explanation,
        "result": df_result,
        "figure": fig_obj,
        "percent_change": stats.get("percent_change") if stats else None,
        "forecast_stats": stats,
        "error": None
    }