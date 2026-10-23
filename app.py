import os
import io
import time
import json
import hashlib
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load environment variables
load_dotenv()
default_api_key = os.getenv("GEMINI_API_KEY", "")

# Streamlit Page Configuration
st.set_page_config(
    page_title="🩺 MedReport AI - Medical Lab Report Translator",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Strict Dark Mode & High-Contrast Button CSS Styling
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .stApp {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Hide Streamlit default sidebar/chrome using custom CSS */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebar"] { display: none; }

    [data-testid="collapsedControl"] {
        display: none !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }

    /* Sticky Top Medical Disclaimer Banner (Red / Amber) */
    .sticky-disclaimer-banner {
        position: sticky;
        top: 0;
        z-index: 9999;
        background: linear-gradient(90deg, #451a03 0%, #78350f 50%, #451a03 100%);
        border: 1px solid #f59e0b;
        border-radius: 10px;
        padding: 10px 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25);
    }

    .disclaimer-inner {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .disclaimer-icon {
        font-size: 1.25rem;
    }

    .disclaimer-text {
        color: #fef3c7;
        font-size: 0.88rem;
        line-height: 1.4;
    }

    .disclaimer-text strong {
        color: #fbbf24;
    }

    /* Hackathon MVP Badge */
    .hackathon-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(234, 88, 12, 0.25) 0%, rgba(249, 115, 22, 0.35) 100%);
        border: 1px solid #f97316;
        border-radius: 9999px;
        padding: 3px 12px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #fb923c;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    /* Interactive Medical Acronym Tooltip */
    .med-tooltip-container {
        position: relative;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        cursor: help;
    }

    .tooltip-badge {
        font-size: 0.75rem;
        color: #00E5FF;
        background: rgba(0, 229, 255, 0.15);
        border: 1px solid rgba(0, 229, 255, 0.4);
        border-radius: 50%;
        width: 18px;
        height: 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .med-tooltip-container:hover .tooltip-badge {
        background: #00E5FF;
        color: #000000;
        box-shadow: 0 0 10px #00E5FF;
    }

    .med-tooltip-text {
        visibility: hidden;
        opacity: 0;
        width: 280px;
        background: #111827;
        color: #E2E8F0;
        text-align: left;
        border: 1px solid #00E5FF;
        border-radius: 8px;
        padding: 10px 14px;
        position: absolute;
        z-index: 10000;
        bottom: 125%;
        left: 0;
        transform: translateY(6px);
        transition: opacity 0.2s ease, transform 0.2s ease;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
        font-size: 0.82rem;
        font-weight: 400;
        line-height: 1.45;
        pointer-events: none;
    }

    .med-tooltip-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 20px;
        border-width: 6px;
        border-style: solid;
        border-color: #00E5FF transparent transparent transparent;
    }

    .med-tooltip-container:hover .med-tooltip-text {
        visibility: visible;
        opacity: 1;
        transform: translateY(0);
    }

    /* Soft Red / Amber Cards for Attention Needed */
    .flagged-card-soft {
        background: linear-gradient(135deg, rgba(69, 26, 3, 0.4) 0%, #1f1d24 100%);
        border: 1px solid rgba(245, 158, 11, 0.45);
        border-left: 6px solid #f59e0b;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.15);
    }

    .plain-english-box {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
    }

    .plain-english-title {
        color: #fbbf24;
        font-weight: 700;
        font-size: 0.84rem;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .plain-english-text {
        color: #fef3c7;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .badge-soft-amber {
        display: inline-block;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        border-radius: 9999px;
        background-color: #d97706;
        color: #ffffff;
        border: 1px solid #f59e0b;
        letter-spacing: 0.5px;
    }

    /* Interactive Medical Dictionary Card */
    .dictionary-card {
        background: linear-gradient(135deg, #111827 0%, #1a2234 100%);
        border: 1px solid rgba(0, 229, 255, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }

    .dictionary-title {
        color: #00E5FF;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .dictionary-subtext {
        color: #94A3B8;
        font-size: 0.84rem;
        margin-bottom: 12px;
    }

    .dictionary-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .dictionary-chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(0, 229, 255, 0.08);
        border: 1px solid rgba(0, 229, 255, 0.3);
        color: #E2E8F0;
        border-radius: 9999px;
        padding: 5px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: help;
        transition: all 0.2s ease;
    }

    .dictionary-chip:hover {
        background: rgba(0, 229, 255, 0.2);
        border-color: #00E5FF;
        color: #00E5FF;
        transform: translateY(-1px);
    }

    /* Medical Header Banner Styling */
    .medical-header-banner {
        background: linear-gradient(135deg, #111827 0%, #0F172A 50%, #0D1B2A 100%);
        border: 1px solid rgba(0, 229, 255, 0.25);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 25px rgba(0, 229, 255, 0.08);
        position: relative;
        overflow: hidden;
    }

    .medical-header-banner::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00E5FF 0%, #00B0FF 50%, #00E676 100%);
    }

    .banner-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }

    .banner-left {
        flex: 1 1 460px;
    }

    .banner-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 229, 255, 0.12);
        border: 1px solid rgba(0, 229, 255, 0.35);
        border-radius: 9999px;
        padding: 4px 12px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #00E5FF;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #00E676;
        box-shadow: 0 0 8px #00E676;
        display: inline-block;
        animation: pulse-glow 2s infinite;
    }

    @keyframes pulse-glow {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(0, 230, 118, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }

    .medical-banner-title {
        color: #FFFFFF;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }

    .ai-gradient {
        background: linear-gradient(135deg, #00E5FF 0%, #00E676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .medical-banner-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin: 0;
        line-height: 1.5;
    }

    .banner-right-pills {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .clinical-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(22, 27, 34, 0.85);
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #E2E8F0;
        white-space: nowrap;
    }

    .pill-icon {
        font-size: 0.85rem;
    }

    /* Structured Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A202C 0%, #161B22 100%) !important;
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }

    [data-testid="stMetric"]:hover {
        border-color: #00E5FF66 !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stMetricLabel"] p {
        color: #8B949E !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stMetricValue"] div {
        color: #00E5FF !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }

    /* Clean Medical Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B22;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #30363D;
        margin-bottom: 16px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #8B949E;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 8px 16px;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
        background-color: rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #00E5FF !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #00E5FF !important;
    }

    /* High-Contrast Primary Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%) !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 14px rgba(0, 230, 118, 0.3) !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%) !important;
        color: #000000 !important;
        box-shadow: 0px 0px 20px rgba(0, 230, 118, 0.6) !important;
        transform: translateY(-2px) !important;
    }

    div.stButton > button:active,
    div.stButton > button:focus {
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%) !important;
        color: #000000 !important;
        box-shadow: 0px 0px 10px rgba(0, 230, 118, 0.4) !important;
        transform: translateY(0px) !important;
    }

    div.stButton > button p,
    div.stButton > button span {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* Header & Brand Accent */
    .brand-title {
        color: #00E5FF;
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }

    .brand-subtitle {
        color: #8B949E;
        font-size: 1.05rem;
        margin-bottom: 24px;
        line-height: 1.5;
    }

    /* Top Section: Executive Summary Hero Card */
    .hero-summary-card {
        background: linear-gradient(135deg, #1E222B 0%, #161B22 100%);
        border: 1px solid #30363D;
        border-left: 6px solid #00E5FF;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }

    .hero-summary-title {
        color: #00E5FF;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .hero-summary-body {
        color: #E6EDF3;
        font-size: 1.05rem;
        line-height: 1.65;
        margin-bottom: 16px;
    }

    /* Status Banners */
    .banner-alert {
        background-color: #23191E;
        border: 1px solid #DA363388;
        border-left: 6px solid #DA3633;
        border-radius: 10px;
        padding: 14px 18px;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }

    .banner-normal {
        background-color: #16241C;
        border: 1px solid #23863688;
        border-left: 6px solid #238636;
        border-radius: 10px;
        padding: 14px 18px;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }

    /* Section Header */
    .section-header {
        color: #00E5FF;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 28px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-subtext {
        color: #8B949E;
        font-size: 0.9rem;
        margin-bottom: 16px;
    }

    /* Second Section: Stacked Metric Rows */
    .metric-row-normal {
        background-color: #1E222B;
        border: 1px solid #30363D;
        border-left: 5px solid #238636;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }

    .metric-row-alert {
        background-color: #23191E;
        border: 1px solid #DA363366;
        border-left: 5px solid #DA3633;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 2px 10px rgba(218, 54, 51, 0.2);
    }

    .metric-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .metric-title-text {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    .metric-values-row {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        align-items: baseline;
        margin-bottom: 10px;
    }

    .val-highlight-normal {
        font-size: 1.35rem;
        font-weight: 800;
        color: #00E5FF;
    }

    .val-highlight-alert {
        font-size: 1.35rem;
        font-weight: 800;
        color: #FF7B72;
    }

    .ref-range-text {
        font-size: 0.88rem;
        color: #8B949E;
    }

    .metric-explanation-box {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 10px 14px;
        color: #E6EDF3;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* Badges */
    .badge-normal-dark {
        display: inline-block;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        border-radius: 9999px;
        background-color: #238636;
        color: #FFFFFF;
        border: 1px solid #2ea043;
        letter-spacing: 0.5px;
    }

    .badge-alert-dark {
        display: inline-block;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        border-radius: 9999px;
        background-color: #DA3633;
        color: #FFFFFF;
        border: 1px solid #f85149;
        letter-spacing: 0.5px;
    }

    /* Third Section: Flagged Callout Box */
    .flagged-callout-container {
        background-color: #23191E;
        border: 1px solid #DA363388;
        border-left: 6px solid #DA3633;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(218, 54, 51, 0.15);
    }

    .flagged-item-card {
        background-color: #1E222B;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 12px;
    }

    .normal-all-container {
        background-color: #16241C;
        border: 1px solid #23863688;
        border-left: 6px solid #238636;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
        color: #E6EDF3;
    }

    /* Bottom Disclaimer */
    .disclaimer-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 32px;
        color: #8B949E;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper function to render HTML cleanly without markdown code-block indentation issues
def render_html(html_str: str):
    """
    Strips leading whitespace from every line and renders with unsafe_allow_html=True
    to prevent Markdown from treating indented HTML tags as preformatted code blocks.
    """
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)

# ==============================================================================
# 4. BACKEND CONNECTION READINESS (REST API INTEGRATION HOOK)
# ==============================================================================
API_URL = os.getenv("API_URL", "http://localhost:5000/api/analyze")

def call_backend_api_template(file_bytes: bytes, language: str = "English", api_url: str = API_URL):
    """
    POST request template pointing to http://localhost:5000/api/analyze.
    Use this template to connect an external Node.js / FastAPI / Flask backend.
    
    Equivalent JavaScript fetch() template:
    -------------------------------------------------------------------------
    const formData = new FormData();
    formData.append('file', fileBlob, 'lab_report.png');
    formData.append('language', language);
    
    const response = await fetch(process.env.API_URL || 'http://localhost:5000/api/analyze', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    -------------------------------------------------------------------------
    """
    pass

# ==============================================================================
# INTERACTIVE MEDICAL DICTIONARY & ACRONYM TOOLTIP MAPPING
# ==============================================================================
MEDICAL_DICTIONARY = {
    "CBC": "Complete Blood Count — A routine blood test measuring red cells, white cells, and platelets to evaluate overall health.",
    "HDL": "High-Density Lipoprotein — 'Good' cholesterol that helps carry excess cholesterol from arteries back to the liver.",
    "LDL": "Low-Density Lipoprotein — 'Bad' cholesterol; high levels can gradually build up in arterial walls and form plaques.",
    "RBC": "Red Blood Cells — Oxygen-carrying blood cells that transport oxygen from the lungs throughout the entire body.",
    "WBC": "White Blood Cells — Immune system cells that defend your body against infections, bacteria, and inflammation.",
    "Triglycerides": "A type of fat (lipid) in your blood stored in fat cells and used for cellular energy between meals.",
    "HbA1c": "Hemoglobin A1c — A key diabetes marker showing your average blood glucose (sugar) level over the last 2-3 months.",
    "Glucose": "Blood Sugar — The primary sugar in your bloodstream providing fuel and energy to all your body cells.",
    "Creatinine": "A natural waste product from muscle breakdown filtered out by healthy kidneys; monitors kidney function.",
    "Hemoglobin": "The essential protein inside red blood cells responsible for carrying oxygen throughout the body.",
    "Cholesterol": "A waxy, fat-like substance found in all cells; necessary for hormone and cell membrane synthesis.",
}

def format_metric_name_with_tooltip(name: str) -> str:
    """
    Renders metric name with an interactive hover tooltip explaining acronyms in plain 8th-grade English.
    """
    name_clean = name.strip()
    matched_term = None
    for term, definition in MEDICAL_DICTIONARY.items():
        if term.lower() in name_clean.lower():
            matched_term = (term, definition)
            break
    
    if matched_term:
        term, definition = matched_term
        return f'<span class="med-tooltip-container"><strong style="color: #FFFFFF; font-size: 1.05rem;">{name_clean}</strong><span class="tooltip-badge">ℹ️</span><span class="med-tooltip-text"><strong>{term}:</strong> {definition}</span></span>'
    else:
        return f'<strong style="color: #FFFFFF; font-size: 1.05rem;">{name_clean}</strong>'

# 1. Grayscale & Ultra-Low Payload Compression (< 20 KB payload)
def optimize_image_for_api(pil_image: Image.Image) -> Image.Image:
    """
    Grayscale & Ultra-Low Payload Compression:
    - Converts uploaded image to Grayscale ("L") mode.
    - Downscales so max(width, height) <= 640px maintaining aspect ratio.
    - Saves to JPEG format with quality=55 in an io.BytesIO() buffer (~20KB payload).
    """
    img = pil_image.convert("L")
    max_dim = 640
    if img.width > max_dim or img.height > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=55)
    buffer.seek(0)
    return Image.open(buffer)

# Realistic Multi-Language Sample Data for Demo / Offline Mode
SAMPLE_DATA = {
    "English": {
        "summary": "This routine lab panel shows that your basic blood cell counts and kidney functions are completely healthy. However, your fasting blood glucose and LDL cholesterol are slightly above standard reference ranges, which warrants a discussion with your doctor regarding diet and lifestyle.",
        "overall_status": "Attention Needed",
        "metrics": [
            {
                "name": "Fasting Blood Glucose",
                "value": "118 mg/dL",
                "reference_range": "70 – 99 mg/dL",
                "status": "High",
                "explanation": "Elevated fasting blood sugar, which can suggest early insulin resistance or pre-diabetes.",
            },
            {
                "name": "Hemoglobin A1c (HbA1c)",
                "value": "5.9 %",
                "reference_range": "< 5.7 %",
                "status": "High",
                "explanation": "Reflects your 3-month average blood glucose; slightly above the normal boundary.",
            },
            {
                "name": "Total Cholesterol",
                "value": "215 mg/dL",
                "reference_range": "< 200 mg/dL",
                "status": "High",
                "explanation": "Overall blood lipid count is mildly elevated, primarily driven by LDL particles.",
            },
            {
                "name": "LDL Cholesterol",
                "value": "138 mg/dL",
                "reference_range": "< 100 mg/dL",
                "status": "High",
                "explanation": "Known as 'bad' cholesterol; excess amounts can gradually build up in arterial walls.",
            },
            {
                "name": "HDL Cholesterol",
                "value": "48 mg/dL",
                "reference_range": "> 40 mg/dL",
                "status": "Normal",
                "explanation": "Known as 'good' cholesterol; helps remove other cholesterol forms from the bloodstream.",
            },
            {
                "name": "Serum Creatinine",
                "value": "0.9 mg/dL",
                "reference_range": "0.6 – 1.2 mg/dL",
                "status": "Normal",
                "explanation": "Measures kidney filtration efficiency; demonstrates optimal kidney performance.",
            },
            {
                "name": "Hemoglobin",
                "value": "14.2 g/dL",
                "reference_range": "13.0 – 17.0 g/dL",
                "status": "Normal",
                "explanation": "Protein carrying oxygen throughout the body; confirms healthy red blood cell levels.",
            },
        ],
        "doctor_questions": [
            "Do my elevated blood sugar and HbA1c levels require dietary modifications or should we consider medication?",
            "What specific lifestyle or nutritional adjustments can help reduce my LDL cholesterol levels?",
            "When would you recommend scheduling follow-up blood work to monitor these metrics?",
        ],
    },
    "Hindi": {
        "summary": "यह नियमित लैब रिपोर्ट दर्शाती है कि आपकी रक्त कोशिकाएं और गुर्दे (किडनी) पूरी तरह से स्वस्थ हैं। हालांकि, आपका फास्टिंग ब्लड शुगर और एलडीएल कोलेस्ट्रॉल सामान्य सीमा से थोड़ा अधिक है, जिसके लिए डॉक्टर से परामर्श लेना उचित रहेगा।",
        "overall_status": "Attention Needed",
        "metrics": [
            {
                "name": "फास्टिंग ब्लड ग्लूकोज",
                "value": "118 mg/dL",
                "reference_range": "70 – 99 mg/dL",
                "status": "High",
                "explanation": "खाली पेट रक्त शर्करा का बढ़ा हुआ स्तर, जो प्री-डायबिटीज का प्रारंभिक संकेत हो सकता है।",
            },
        ],
        "doctor_questions": [
            "क्या मेरे बढ़े हुए ब्लड शुगर और HbA1c को केवल आहार और व्यायाम से नियंत्रित किया जा सकता है?",
            "एलडीएल कोलेस्ट्रॉल को सामान्य सीमा में लाने के लिए मुझे कौन से खाद्य पदार्थों से बचना चाहिए?",
            "इन मानों की प्रगति देखने के लिए मुझे दोबारा टेस्ट कब कराना चाहिए?",
        ],
    },
    "Marathi": {
        "summary": "हा लॅब रिपोर्ट दर्शवतो की तुमच्या शरीरातील रक्त पेशी आणि मूत्रपिंड (किडनी) पूर्णपणे निरोगी आहेत. तथापि, उपाशीपोटी रक्तातील साखर आणि एलडीएल कोलेस्ट्रॉल सामान्य मर्यादेपेक्षा थोडे जास्त आढळले आहे, ज्यासाठी डॉक्टरांचा सल्ला घेणे आवश्यक आहे.",
        "overall_status": "Attention Needed",
        "metrics": [
            {
                "name": "फास्टिंग ब्लड ग्लुकोज",
                "value": "118 mg/dL",
                "reference_range": "70 – 99 mg/dL",
                "status": "High",
                "explanation": "उपाशीपोटी रक्तातील साखरेचे वाढलेले प्रमाण, जे प्री-डायबेटिसचे प्रारंभिक लक्षण असू शकते.",
            },
        ],
        "doctor_questions": [
            "माझ्या रक्तातील साखर आणि HbA1c नियंत्रित करण्यासाठी आहारातील कोणते बदल पुरेसे ठरतील?",
        ],
    },
    "Spanish": {
        "summary": "Este panel de laboratorio rutinario indica que sus recuentos sanguíneos y funciones renales son completamente saludables.",
        "overall_status": "Attention Needed",
        "metrics": [
            {
                "name": "Glucosa en ayunas",
                "value": "118 mg/dL",
                "reference_range": "70 – 99 mg/dL",
                "status": "High",
                "explanation": "Nivel elevado de azúcar en sangre en ayunas, lo que puede sugerir resistencia temprana a la insulina o prediabetes.",
            },
        ],
        "doctor_questions": [
            "¿Mis niveles de glucosa y HbA1c requieren cambios en la dieta y ejercicio, o deberíamos evaluar medicación?",
        ],
    },
}

# Theme State Initialization
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# --- TOP NAVIGATION BAR ---
col_nav_left, col_nav_right = st.columns([1, 1])
with col_nav_left:
    with st.popover("⚙️ System Config", use_container_width=False):
        st.markdown("### ⚙️ Control Panel")
        demo_mode = st.checkbox(
            "Demo / Offline Mode",
            value=False,
            help="Use pre-generated realistic sample medical data for testing without calling external APIs.",
        )
        api_key_input = st.text_input(
            "Gemini API Key",
            value=default_api_key,
            type="password",
            disabled=demo_mode,
            help="Enter your Google Gemini API key. Defaults to GEMINI_API_KEY from .env.",
        )
        st.divider()
        st.markdown("### ⚠️ Clinical Notice")
        st.info(
            "**Educational Assistance Only:** MedTranslate AI does NOT provide medical diagnosis or treatment plans. "
            "Always review laboratory results with a licensed healthcare provider."
        )

with col_nav_right:
    # Techy animated theme toggle
    st.markdown(
        """
        <style>
        .theme-toggle-container {
            display: flex;
            justify-content: flex-end;
            margin-top: 5px;
        }
        div.stButton > button[key="theme_toggle_btn"] {
            border: 2px solid #00E5FF !important;
            animation: pulse-neon 2s infinite;
            background: transparent !important;
            color: #00E5FF !important;
            font-size: 0.9rem !important;
            padding: 0.4rem 1.2rem !important;
        }
        @keyframes pulse-neon {
            0% { box-shadow: 0 0 5px #00E5FF, inset 0 0 5px #00E5FF; }
            50% { box-shadow: 0 0 15px #00E5FF, inset 0 0 10px #00E5FF; }
            100% { box-shadow: 0 0 5px #00E5FF, inset 0 0 5px #00E5FF; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="theme-toggle-container">', unsafe_allow_html=True)
    theme_label = "🌙 Dark Mode" if st.session_state.theme == "dark" else "☀️ Light Mode"
    if st.button(theme_label, key="theme_toggle_btn"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Dynamic Light Mode CSS Injection
if st.session_state.theme == "light":
    st.markdown(
        """
        <style>
        /* Light Mode High-Contrast Overrides */
        .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
        .medical-banner-title { color: #0F172A !important; }
        .medical-banner-subtitle { color: #334155 !important; }
        .section-header { color: #0F172A !important; }
        .hero-summary-card, .metric-row-normal, .dictionary-card, .flagged-item-card, .flagged-card-soft, .normal-all-container, .disclaimer-card {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        }
        .metric-header-row, .dictionary-title, .hero-summary-title, .plain-english-title { color: #0F172A !important; }
        .val-highlight-normal, .val-highlight-alert, .ai-gradient { text-shadow: none !important; }
        [data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #CBD5E1 !important; }
        [data-testid="stMetricValue"] div { color: #0F172A !important; }
        .metric-explanation-box, .plain-english-box {
            background-color: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            color: #1E293B !important;
        }
        .ref-range-text, .dictionary-subtext, .plain-english-text, .hero-summary-body { color: #334155 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# 1. Top Sticky Disclaimer Banner (Red / Amber Text)
render_html(
    """
    <div class="sticky-disclaimer-banner">
        <div class="disclaimer-inner">
            <span class="disclaimer-icon">⚠️</span>
            <span class="disclaimer-text">
                <strong>DISCLAIMER:</strong> This tool provides educational information only and does not constitute medical diagnosis or advice. Always consult your healthcare provider.
            </span>
        </div>
    </div>
    """
)

# Header: Logo icon + App Title ("MedReport AI") + "Hackathon MVP" badge (Theme: AI for Healthcare)
render_html(
    """
    <div class="medical-header-banner">
        <div class="banner-content">
            <div class="banner-left">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                    <span class="banner-badge">
                        <span class="pulse-dot"></span>
                        <span>THEME: AI FOR HEALTHCARE</span>
                    </span>
                    <span class="hackathon-badge">
                        ⚡ HACKATHON MVP
                    </span>
                    <span class="brand-title" style="display: none;">MedReport AI</span>
                    <span class="brand-subtitle" style="display: none;">Medical Lab Report Translator</span>
                </div>
                <h1 class="medical-banner-title">
                    <span class="med-icon">🩺</span> MedReport <span class="ai-gradient">AI</span>
                </h1>
                <p class="medical-banner-subtitle">
                    Medical Lab Report Translator — Complex Reports Translated into 8th-Grade Explanations with Interactive Tooltips
                </p>
            </div>
            <div class="banner-right-pills">
                <div class="clinical-pill"><span class="pill-icon">📖</span> 8th-Grade Reading Level</div>
                <div class="clinical-pill"><span class="pill-icon">💡</span> Interactive Acronym Tooltips</div>
                <div class="clinical-pill"><span class="pill-icon">⚡</span> Sub-Second Demo Ready</div>
            </div>
        </div>
    </div>
    """
)

if demo_mode:
    st.warning("⚠️ DEMO MODE ACTIVE: Displaying sample mock data.")

# Clear analysis state callback
def clear_analysis_state():
    """Explicit on_change callback to clear cached state whenever a file is uploaded, changed, or removed."""
    if "analysis_result" in st.session_state:
        st.session_state.analysis_result = None
    if "raw_response" in st.session_state:
        st.session_state.raw_response = None
    if "dashboard_data" in st.session_state:
        st.session_state.dashboard_data = None
    if "dashboard_source" in st.session_state:
        st.session_state.dashboard_source = None
    if "streaming_complete" in st.session_state:
        st.session_state.streaming_complete = False
    if "is_fallback" in st.session_state:
        st.session_state.is_fallback = False

# Session state initialization & file tracking
if "file_hash" not in st.session_state:
    st.session_state["file_hash"] = None
if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "raw_response" not in st.session_state:
    st.session_state.raw_response = None
if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None
if "dashboard_source" not in st.session_state:
    st.session_state.dashboard_source = None
if "streaming_complete" not in st.session_state:
    st.session_state.streaming_complete = False
if "is_fallback" not in st.session_state:
    st.session_state.is_fallback = False
if "current_lang" not in st.session_state:
    st.session_state.current_lang = "English"

# File Uploader with drag-and-drop support for PDF/PNG/JPG files & Sample Demo Button
with st.container():
    col_up, col_lang, col_demo = st.columns([2.0, 1.0, 1.2], gap="medium")
    with col_up:
        uploaded_file = st.file_uploader(
            "Upload Lab Report Scan (PDF, PNG, JPG, JPEG)",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Upload an image scan or clear photo of your lab test results.",
            on_change=clear_analysis_state,
            key="lab_report_uploader",
        )
    with col_lang:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        selected_language = st.selectbox(
            "Target Language",
            options=["English", "Hindi", "Marathi", "Spanish"],
            index=["English", "Hindi", "Marathi", "Spanish"].index(st.session_state.current_lang) if st.session_state.current_lang in ["English", "Hindi", "Marathi", "Spanish"] else 0,
            help="Select the language for the translated report explanation.",
            key="lang_selector"
        )
        st.session_state.current_lang = selected_language
    with col_demo:
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 12px; padding: 12px 16px; margin-top: 26px;">
                <div style="color: #38bdf8; font-weight: 700; font-size: 0.84rem; margin-bottom: 2px;">⚡ LIVE JUDGE DEMO</div>
                <div style="color: #94a3b8; font-size: 0.78rem; line-height: 1.35; margin-bottom: 8px;">Bypass upload to instantly fill the dashboard with clinical mock data:</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        load_sample_clicked = st.button("⚡ Load Sample Report", use_container_width=True, key="btn_load_sample_top")
        if load_sample_clicked:
            with st.status("⚡ Loading Clinical Mock Report for Judges...", expanded=True) as status:
                time.sleep(0.1)
                demo_data = SAMPLE_DATA.get(selected_language, SAMPLE_DATA["English"])
                st.session_state.analysis_result = demo_data
                st.session_state.raw_response = None
                st.session_state.dashboard_data = demo_data
                st.session_state.dashboard_source = "Demo Sample Report"
                st.session_state.is_fallback = False
                st.session_state.current_lang = selected_language
                st.session_state.streaming_complete = True
                status.update(label="✅ Sample Report Loaded Instantly!", state="complete", expanded=False)
                st.success("✅ Hackathon Demo Mode: Sample report loaded instantly for live judge review!")
                st.rerun()

# 2. MD5 File Hash Tracking & State Reset
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    current_hash = hashlib.md5(file_bytes).hexdigest()
    if st.session_state.get("file_hash") != current_hash:
        st.session_state["file_hash"] = current_hash
        st.session_state["analysis_result"] = None
        st.session_state["raw_response"] = None
        st.session_state["dashboard_data"] = None
        st.session_state["dashboard_source"] = None
        st.session_state["streaming_complete"] = False
        st.session_state["is_fallback"] = False
else:
    st.session_state["file_hash"] = None
    st.session_state["analysis_result"] = None
    st.session_state["raw_response"] = None
    st.session_state["dashboard_data"] = None
    st.session_state["dashboard_source"] = None
    st.session_state["streaming_complete"] = False
    st.session_state["is_fallback"] = False


# Helper error detection
def is_rate_limit_or_high_demand(err: Exception) -> bool:
    code = getattr(err, "code", None)
    err_str = str(err).lower()
    return (code in [429, 500, 502, 503, 504]) or any(
        indicator in err_str
        for indicator in [
            "429",
            "503",
            "resource_exhausted",
            "rate limit",
            "quota",
            "overloaded",
            "unavailable",
            "high demand",
            "spike",
            "busy",
            "too many requests",
            "timeout",
        ]
    )

# 3 & 4. Response Streaming & Strict 25-Second Timeout / Max 2 Retries
def call_model_stream_with_timeout(
    client,
    model_name: str,
    active_image,
    language: str,
    system_instruction: str,
    stream_placeholder=None,
    max_attempts: int = 2,
    retry_delay: float = 2.0,
):
    """
    Calls Gemini model via generate_content_stream with strict 25s timeout and max 2 attempts.
    Buffers chunks into blocks of ~10-15 tokens to prevent UI re-rendering lag.
    """
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
        max_output_tokens=1500,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=25000),  # 25 seconds strict transport timeout
        tools=None,
    )

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            accumulated_text = ""
            chunk_buffer = ""
            buffer_tokens = 0
            BUFFER_THRESHOLD = 12  # Buffer ~10-15 tokens before triggering UI re-render
            last_render_time = time.time()
            start_time = time.time()

            stream = client.models.generate_content_stream(
                model=model_name,
                contents=[
                    active_image,
                    f"Extract and analyze key lab metrics into JSON in {language}. Keep all string values concise and brief.",
                ],
                config=config,
            )

            for chunk in stream:
                # Enforce strict 25-second deadline
                if time.time() - start_time > 25.0:
                    raise TimeoutError("Gemini streaming request exceeded strict 25-second deadline.")
                if chunk.text:
                    accumulated_text += chunk.text
                    chunk_buffer += chunk.text
                    buffer_tokens += len(chunk.text.split())

                    # Buffer updates: only re-render when ~10-15 tokens buffered or 150ms elapsed
                    now = time.time()
                    if stream_placeholder is not None and (buffer_tokens >= BUFFER_THRESHOLD or (now - last_render_time > 0.15)):
                        preview = accumulated_text[-250:].replace("<", "&lt;").replace(">", "&gt;")
                        stream_placeholder.markdown(
                            f"""
                            <div style="background-color: #161B22; border: 1px solid #00E5FF88; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                                <div style="color: #00E5FF; font-size: 0.85rem; font-weight: 700; margin-bottom: 4px;">⚡ STREAMING RESPONSE IN REAL-TIME...</div>
                                <div style="color: #8B949E; font-size: 0.8rem; font-family: monospace; white-space: pre-wrap; word-break: break-all;">{preview}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        chunk_buffer = ""
                        buffer_tokens = 0
                        last_render_time = now

            # Render any remaining buffer
            if stream_placeholder is not None and chunk_buffer:
                preview = accumulated_text[-250:].replace("<", "&lt;").replace(">", "&gt;")
                stream_placeholder.markdown(
                    f"""
                    <div style="background-color: #161B22; border: 1px solid #00E5FF88; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                        <div style="color: #00E5FF; font-size: 0.85rem; font-weight: 700; margin-bottom: 4px;">⚡ STREAMING RESPONSE IN REAL-TIME...</div>
                        <div style="color: #8B949E; font-size: 0.8rem; font-family: monospace; white-space: pre-wrap; word-break: break-all;">{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if not accumulated_text.strip():
                raise RuntimeError("Model returned an empty response stream.")

            return accumulated_text

        except Exception as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(retry_delay)
                continue
            else:
                raise last_error

def parse_report_json(response_text: str):
    """
    Robust JSON Cleaning & Parsing:
    - Cleans markdown formatting: response_text.replace("```json", "").replace("```", "").strip()
    - Wraps json.loads(cleaned_text) in a safe try-except block.
    - Returns parsed dict on success, None on failure.
    """
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_text)
    except Exception:
        return None

# 2. Fast Deterministic Generation & Minimalist System Prompt
def analyze_lab_report(active_image, language: str, api_key: str, stream_placeholder=None):
    """
    Analyzes lab report using gemini-3.8-flash (temp=0.1, max_output_tokens=1500).
    Uses streaming with a strict 25s timeout, token buffering, and max 2 retries.
    Falls back to gemini-3.5-flash-lite on rate limit/high demand.
    Returns (response_text, source_name).
    """
    system_instruction = f"""
You are MedTranslate AI, an ultra-fast medical translator converting laboratory test reports into concise, high-impact clinical dashboards.

Translate the provided lab report into the patient's selected language: {language}.
All text in the output MUST be translated into {language}.

Output ONLY the required sections cleanly. Zero intro, zero concluding remarks, zero conversational fluff.
Output strictly a valid JSON object matching this schema:
{{
  "summary": "Max 2 short sentences plain-language summary of what tests were performed and key findings.",
  "overall_status": "Normal" or "Attention Needed",
  "metrics": [
    {{
      "name": "Test/Metric Name",
      "value": "Value with unit",
      "reference_range": "Normal range",
      "status": "Normal", "High", or "Low",
      "explanation": "Concise 1-sentence clinical note."
    }}
  ],
  "doctor_questions": [
    "Concise question 1 for doctor",
    "Concise question 2 for doctor",
    "Concise question 3 for doctor"
  ]
}}
Strict prompt efficiency and payload size constraints:
- Keep all string values concise and brief so the generated JSON payload stays small and streams quickly.
- Summary: Max 2 short sentences (plain language).
- Metrics: Strictly 3 to 5 key parameters (prioritize abnormal or flagged findings).
- Metric Explanation: Strictly 1 brief sentence (under 15 words).
- Doctor Questions: 3 concise bullet points (under 15 words each).
- Output ONLY the raw JSON object. Do NOT wrap in markdown formatting or conversational commentary.
"""
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=25000),
    )

    # 1. Primary Model: gemini-3.8-flash with streaming & 25s timeout
    try:
        response_text = call_model_stream_with_timeout(
            client=client,
            model_name="gemini-3.8-flash",
            active_image=active_image,
            language=language,
            system_instruction=system_instruction,
            stream_placeholder=stream_placeholder,
            max_attempts=2,
            retry_delay=2.0,
        )
        return response_text, "gemini-3.8-flash"
    except Exception as e_primary:
        # 2. Lightweight Fallback: gemini-3.5-flash-lite
        if is_rate_limit_or_high_demand(e_primary):
            try:
                response_text = call_model_stream_with_timeout(
                    client=client,
                    model_name="gemini-3.5-flash-lite",
                    active_image=active_image,
                    language=language,
                    system_instruction=system_instruction,
                    stream_placeholder=stream_placeholder,
                    max_attempts=2,
                    retry_delay=2.0,
                )
                return response_text, "gemini-3.5-flash-lite"
            except Exception as e_fallback:
                raise e_fallback
        raise e_primary

# 4. Uploaded Image Verification
if uploaded_file is not None:
    uploaded_file.seek(0)
    if uploaded_file.name.lower().endswith((".png", ".jpg", ".jpeg")):
        try:
            st.image(uploaded_file, caption="Image queued for analysis", use_container_width=True)
        except Exception:
            st.info(f"📄 Document uploaded: **{uploaded_file.name}**")
    else:
        st.info(f"📄 Document uploaded: **{uploaded_file.name}** ({round(len(uploaded_file.getvalue()) / 1024, 1)} KB)")

# Analyze Button
analyze_clicked = st.button("🔬 Analyze Lab Report", type="primary", use_container_width=True)
if analyze_clicked:
    if demo_mode:
        # Step-by-Step Visual Feedback with st.status
        with st.status("⚡ Processing Lab Report (Demo Mode)...", expanded=True) as status:
            status.update(label="📸 Loading pre-processed clinical sample...", state="running")
            time.sleep(0.15)
            status.update(label="📊 Rendering visual dashboard...", state="running")
            time.sleep(0.15)
            demo_data = SAMPLE_DATA.get(selected_language, SAMPLE_DATA["English"])
            st.session_state.analysis_result = demo_data
            st.session_state.raw_response = None
            st.session_state.dashboard_data = demo_data
            st.session_state.dashboard_source = "Demo Mode"
            st.session_state.is_fallback = False
            st.session_state.current_lang = selected_language
            st.session_state.streaming_complete = True
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
            st.success("✅ Vertical Dark Dashboard Loaded (Demo Mode)")
    else:
        active_api_key = api_key_input.strip() if api_key_input else ""
        if not active_api_key:
            st.warning("⚠️ Please provide a Gemini API Key in the sidebar or check 'Demo / Offline Mode'.")
        elif uploaded_file is None:
            st.warning("⚠️ Please upload a lab report image (JPG, JPEG, PNG) before analyzing.")
        else:
            # 2. Enforce Live Image Processing: read directly from io.BytesIO(uploaded_file.getvalue())
            try:
                uploaded_file.seek(0)
                active_image = Image.open(io.BytesIO(uploaded_file.getvalue()))
                if active_image.mode not in ("RGB", "L"):
                    active_image = active_image.convert("RGB")
            except Exception as e:
                st.error(f"Failed to read active uploaded image from memory: {e}")
                active_image = None

            if active_image is not None:
                # Step-by-Step Visual Feedback with st.status & Strict Timeout
                with st.status("⚡ Processing Lab Report...", expanded=True) as status:
                    try:
                        # Step 1: Live Image Verification
                        status.update(label="📸 Preparing active uploaded image for analysis...", state="running")

                        # Step 2: Querying Gemini 3.8 Flash with live streaming
                        status.update(label="🤖 Querying Gemini 3.8 Flash (25s max)...", state="running")
                        stream_placeholder = st.empty()

                        response_text, source_name = analyze_lab_report(
                            active_image=active_image,
                            language=selected_language,
                            api_key=active_api_key,
                            stream_placeholder=stream_placeholder,
                        )
                        stream_placeholder.empty()

                        # 2. Robust JSON Cleaning & Parsing
                        data = parse_report_json(response_text)

                        if data is not None and isinstance(data, dict):
                            # Step 3: Rendering Visual Dashboard
                            status.update(label="📊 Rendering visual dashboard...", state="running")
                            st.session_state.analysis_result = data
                            st.session_state.raw_response = None
                            st.session_state.dashboard_data = data
                            st.session_state.dashboard_source = source_name
                            st.session_state.is_fallback = False
                            st.session_state.current_lang = selected_language
                            st.session_state.streaming_complete = True

                            # On Complete
                            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                            st.success(f"✅ Fast Analysis Complete! (Generated via `{source_name}`)")
                        else:
                            # Safe fallback: render raw response directly using st.markdown instead of raising API Error dialog box
                            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                            st.session_state.analysis_result = None
                            st.session_state.raw_response = response_text
                            st.session_state.dashboard_data = None
                            st.session_state.dashboard_source = source_name
                            st.session_state.is_fallback = False
                            st.session_state.current_lang = selected_language
                            st.session_state.streaming_complete = True
                            with st.container():
                                st.markdown("---")
                                render_html('<div class="section-header">📋 Report Translation & Summary</div>')
                                st.markdown(response_text)

                    except Exception as ex:
                        stream_placeholder.empty()
                        status.update(label="❌ Analysis Failed", state="error", expanded=True)
                        st.error(f"API Error: {ex}")

# Render Vertical (Line-by-Line) Stacked Dashboard
active_dashboard_data = st.session_state.get("analysis_result") or st.session_state.get("dashboard_data")
if active_dashboard_data is not None:
    data = active_dashboard_data
    lang = st.session_state.get("current_lang", selected_language)
    metrics = data.get("metrics", [])
    doctor_questions = data.get("doctor_questions", [])
    summary_text = data.get("summary", "")

    flagged_metrics = [
        m for m in metrics if str(m.get("status", "")).strip().capitalize() in ["High", "Low", "Abnormal"]
    ]
    normal_metrics = [
        m for m in metrics if str(m.get("status", "")).strip().capitalize() not in ["High", "Low", "Abnormal"]
    ]
    is_attention_needed = len(flagged_metrics) > 0

    st.markdown("---")

    # Structured Dashboard View: Metric Cards & Split-Screen / Tabbed Results Container
    with st.container():
        # Top Summary Metrics: Total Markers Checked | Normal Count | Requires Attention Count
        with st.container():
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Markers Checked", len(metrics))
            with col_stat2:
                st.metric("Normal Count", len(normal_metrics))
            with col_stat3:
                st.metric(
                    "Requires Attention Count",
                    len(flagged_metrics),
                    delta=f"{len(flagged_metrics)} out of range" if is_attention_needed else "All clear",
                    delta_color="inverse" if is_attention_needed else "normal",
                )

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        # Helper HTML card builders
        def build_flagged_card_html(fm: dict) -> str:
            status_text = str(fm.get("status", "Abnormal")).upper()
            name_html = format_metric_name_with_tooltip(fm.get("name", "Metric"))
            val = fm.get("value", "N/A")
            ref = fm.get("reference_range", "N/A")
            expl = fm.get("explanation", "")
            return f"""
<div class="flagged-card-soft">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        {name_html}
        <span class="badge-soft-amber">⚠️ {status_text}</span>
    </div>
    <div style="margin-bottom: 8px;">
        <span style="color: #fb923c; font-weight: 800; font-size: 1.25rem;">{val}</span>
        <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 10px;">(Standard Range: <strong style="color: #e2e8f0;">{ref}</strong>)</span>
    </div>
    <div class="plain-english-box">
        <div class="plain-english-title">💡 What this means (8th-Grade Plain English):</div>
        <div class="plain-english-text">{expl}</div>
    </div>
</div>
"""

        def build_normal_card_html(m: dict) -> str:
            name_html = format_metric_name_with_tooltip(m.get("name", "Metric"))
            val = m.get("value", "N/A")
            ref = m.get("reference_range", "N/A")
            expl = m.get("explanation", "")
            return f"""
<div class="metric-row-normal">
    <div class="metric-header-row">
        {name_html}
        <span class="badge-normal-dark">✅ NORMAL</span>
    </div>
    <div class="metric-values-row">
        <div>
            <span class="ref-range-text">Patient Value: </span>
            <span class="val-highlight-normal">{val}</span>
        </div>
        <div>
            <span class="ref-range-text">Standard Healthy Range: </span>
            <strong style="color: #E6EDF3;">{ref}</strong>
        </div>
    </div>
    <div class="metric-explanation-box">
        💡 <strong>Plain English Explanation:</strong> {expl}
    </div>
</div>
"""

        # Interactive Acronym Dictionary HTML
        dictionary_html = """
<div class="dictionary-card">
    <div class="dictionary-title">📖 Interactive Medical Acronym Quick Dictionary</div>
    <div class="dictionary-subtext">Hover or tap any medical abbreviation for an 8th-grade plain-English explanation:</div>
    <div class="dictionary-chips">
        <span class="med-tooltip-container"><span class="dictionary-chip">CBC ℹ️</span><span class="med-tooltip-text"><strong>CBC (Complete Blood Count):</strong> A routine blood test measuring red cells, white cells, and platelets.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">HDL ℹ️</span><span class="med-tooltip-text"><strong>HDL (High-Density Lipoprotein):</strong> "Good" cholesterol that clears excess fats from arteries back to the liver.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">LDL ℹ️</span><span class="med-tooltip-text"><strong>LDL (Low-Density Lipoprotein):</strong> "Bad" cholesterol that can build plaque in arteries if high.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">RBC ℹ️</span><span class="med-tooltip-text"><strong>RBC (Red Blood Cells):</strong> Oxygen-carrying cells transporting fresh oxygen to all body tissues.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">WBC ℹ️</span><span class="med-tooltip-text"><strong>WBC (White Blood Cells):</strong> Immune defender cells fighting infections, bacteria, and inflammation.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">Triglycerides ℹ️</span><span class="med-tooltip-text"><strong>Triglycerides:</strong> Blood fats stored in fat cells providing energy between meals.</span></span>
        <span class="med-tooltip-container"><span class="dictionary-chip">HbA1c ℹ️</span><span class="med-tooltip-text"><strong>HbA1c (Hemoglobin A1c):</strong> Key test reflecting your 3-month average blood glucose levels.</span></span>
    </div>
</div>
"""

        normal_all_html = """
<div class="normal-all-container">
    <div style="color: #3FB950; font-size: 1.1rem; font-weight: 700; margin-bottom: 6px;">
        ✅ All Markers Normal
    </div>
    <div style="color: #E6EDF3; font-size: 0.92rem;">
        No out-of-range values detected in this test panel. Continue maintaining healthy habits.
    </div>
</div>
"""

        # Tabbed & Split-Screen Results Dashboard
        tab_split, tab_flagged, tab_normal, tab_summary, tab_backend = st.tabs([
            "⚡ Split-Screen Dashboard",
            f"🚨 Action Items for Doctor ({len(flagged_metrics)})",
            f"📖 Medical Dictionary & Normal Results ({len(normal_metrics)})",
            "📋 Full Executive Summary",
            "🔌 Backend API Integration Hook",
        ])

        # TAB 1: SPLIT-SCREEN DASHBOARD (SIDE-BY-SIDE)
        with tab_split:
            col_left, col_right = st.columns([1, 1], gap="large")

            # Left Column: Section A (Highlighting Tool: Action Items for Doctor)
            with col_left:
                render_html('<div class="section-header" style="color: #fb923c;">🚨 Section A: Requires Attention</div>')
                render_html('<div class="section-subtext">Out-of-range values with 8th-grade plain-English explanations & doctor questions</div>')

                if is_attention_needed:
                    for fm in flagged_metrics:
                        render_html(build_flagged_card_html(fm))
                else:
                    render_html(normal_all_html)

                # Checklist in Left Column
                st.markdown(
                    """
                    <div style="background-color: #1E222B; border: 1px solid #30363D; border-radius: 12px; padding: 14px 18px; margin-top: 14px; margin-bottom: 12px;">
                        <div style="color: #00E5FF; font-weight: 700; font-size: 0.96rem; margin-bottom: 4px;">
                            🩺 Questions to Ask Your Doctor
                        </div>
                        <div style="color: #8B949E; font-size: 0.82rem;">
                            Auto-generated checklist based on out-of-range findings:
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                split_selected_q = []
                for q_idx, question in enumerate(doctor_questions, start=1):
                    checked = st.checkbox(
                        f"**Q{q_idx}:** {question}",
                        value=True,
                        key=f"split_q_{q_idx}",
                    )
                    if checked:
                        split_selected_q.append(question)

                # Checklist text generation
                checklist_lines = [
                    "==================================================================",
                    "        🩺 MedReport AI - Doctor Consultation Checklist          ",
                    "        Theme: AI for Healthcare (Hackathon MVP)                ",
                    "==================================================================",
                    f"Language: {lang}",
                    "",
                    "1. EXECUTIVE SUMMARY:",
                    f"   {summary_text}",
                    "",
                    "2. QUESTIONS TO ASK YOUR DOCTOR:",
                ]
                if split_selected_q:
                    for s_idx, sq in enumerate(split_selected_q, 1):
                        checklist_lines.append(f"   [ ] Q{s_idx}: {sq}")
                else:
                    checklist_lines.append("   (No questions selected)")

                checklist_lines.append("")
                checklist_lines.append("3. FLAGGED / OUT-OF-RANGE MARKERS REQUIRING ATTENTION:")
                if flagged_metrics:
                    for fm in flagged_metrics:
                        checklist_lines.append(
                            f"   • {fm.get('name')}: {fm.get('value')} (Standard: {fm.get('reference_range')}) - [{fm.get('status')}]"
                        )
                        checklist_lines.append(f"     What this means: {fm.get('explanation')}")
                else:
                    checklist_lines.append("   • All analyzed parameters were within normal reference ranges.")

                checklist_lines.extend(
                    [
                        "",
                        "==================================================================",
                        "DISCLAIMER: This checklist provides educational information only",
                        "and does not constitute medical diagnosis or advice. Always",
                        "consult your healthcare provider.",
                        "==================================================================",
                    ]
                )
                checklist_content = "\n".join(checklist_lines)

                st.download_button(
                    label="📥 Download Doctor Questions Checklist (.txt)",
                    data=checklist_content,
                    file_name=f"medreport_doctor_checklist_{lang.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="btn_download_split",
                )

            # Right Column: Section B (Interactive Medical Dictionary & Normal Results)
            with col_right:
                render_html('<div class="section-header" style="color: #38bdf8;">📖 Section B: Medical Dictionary & Normal Results</div>')
                render_html('<div class="section-subtext">Healthy lab markers grouped cleanly with green badges & acronym hover tooltips</div>')

                # Interactive Dictionary Card
                render_html(dictionary_html)

                if normal_metrics:
                    for nm in normal_metrics:
                        render_html(build_normal_card_html(nm))
                else:
                    st.info("No normal markers in this panel.")

        # TAB 2: DEDICATED SECTION A (ACTION ITEMS & FLAGGED CARD DEEP DIVE)
        with tab_flagged:
            with st.container():
                render_html('<div class="section-header" style="color: #fb923c;">🚨 Highlighting Tool: Out-of-Range Lab Values</div>')
                render_html('<div class="section-subtext">Action items prioritized for your upcoming physician consultation</div>')

                if is_attention_needed:
                    for fm in flagged_metrics:
                        render_html(build_flagged_card_html(fm))
                else:
                    render_html(normal_all_html)

                # Full-width checklist card
                st.markdown(
                    """
                    <div style="background-color: #1E222B; border: 1px solid #30363D; border-radius: 12px; padding: 18px 20px; margin-top: 20px; margin-bottom: 14px;">
                        <div style="color: #00E5FF; font-weight: 700; font-size: 1.05rem; margin-bottom: 6px;">
                            🩺 Questions to Ask Your Doctor (Full Checklist)
                        </div>
                        <div style="color: #8B949E; font-size: 0.88rem;">
                            Select the inquiries you would like to discuss con su healthcare provider:
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                tab_selected_q = []
                for q_idx, question in enumerate(doctor_questions, start=1):
                    checked = st.checkbox(
                        f"**Q{q_idx}:** {question}",
                        value=True,
                        key=f"tab_q_{q_idx}",
                    )
                    if checked:
                        tab_selected_q.append(question)

                st.download_button(
                    label="📥 Download Doctor Questions Checklist (.txt)",
                    data=checklist_content,
                    file_name=f"medreport_doctor_checklist_{lang.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="btn_download_tab",
                )

        # TAB 3: DEDICATED SECTION B (MEDICAL DICTIONARY & NORMAL RESULTS)
        with tab_normal:
            with st.container():
                render_html('<div class="section-header" style="color: #38bdf8;">📖 Interactive Medical Dictionary & Normal Results</div>')
                render_html('<div class="section-subtext">Clean green cards for normal markers with interactive medical acronym definitions</div>')

                render_html(dictionary_html)

                if normal_metrics:
                    for nm in normal_metrics:
                        render_html(build_normal_card_html(nm))
                else:
                    st.info("No normal markers in this panel.")

        # TAB 4: EXECUTIVE SUMMARY & CLINICAL STATUS
        with tab_summary:
            with st.container():
                render_html('<div class="section-header">📋 Executive Summary & Translation</div>')
                render_html('<div class="section-subtext">High-level translation and clinical status overview</div>')

                summary_html = f"""
<div class="hero-summary-card">
    <div class="hero-summary-title">Summary & Key Findings</div>
    <div class="hero-summary-body">{summary_text}</div>
</div>
"""
                render_html(summary_html)

                if is_attention_needed:
                    banner_html = f"""
<div class="banner-alert">
    <span>⚠️</span>
    <span><strong>Attention Recommended:</strong> {len(flagged_metrics)} out of {len(metrics)} analyzed marker(s) fall outside standard clinical reference ranges.</span>
</div>
"""
                    render_html(banner_html)
                else:
                    banner_html = """
<div class="banner-normal">
    <span>✅</span>
    <span><strong>Optimal Status:</strong> All analyzed metrics fall within standard healthy reference ranges.</span>
</div>
"""
                    render_html(banner_html)

        # TAB 5: BACKEND API INTEGRATION HOOK
        with tab_backend:
            with st.container():
                render_html('<div class="section-header">🔌 Backend Connection Readiness</div>')
                render_html('<div class="section-subtext">Simple REST API POST request template pointed to http://localhost:5000/api/analyze for team leader integration</div>')

                st.markdown(
                    f"""
                    <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 18px 22px; margin-bottom: 18px;">
                        <div style="color: #38bdf8; font-weight: 700; font-size: 1rem; margin-bottom: 6px;">Target API Endpoint:</div>
                        <code style="background-color: #0E1117; color: #00E5FF; padding: 6px 12px; border-radius: 6px; font-size: 0.95rem;">{API_URL}</code>
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 10px;">Configure via <code>API_URL</code> in your <code>.env</code> file.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                    ```javascript
                    // ==============================================================================
                    // JavaScript fetch() POST Request Template
                    // Route lab reports to: http://localhost:5000/api/analyze
                    // ==============================================================================

                    async function analyzeLabReport(fileBlob, language = 'English') {
                      const API_ENDPOINT = process.env.API_URL || 'http://localhost:5000/api/analyze';
                      const formData = new FormData();
                      formData.append('file', fileBlob, 'lab_report.png');
                      formData.append('language', language);

                      try {
                        const response = await fetch(API_ENDPOINT, {
                          method: 'POST',
                          body: formData,
                        });

                        if (!response.ok) {
                          throw new Error(`Server returned HTTP ${response.status}`);
                        }

                        const data = await response.json();
                        return data;
                      } catch (error) {
                        console.error('Backend API error:', error);
                        throw error;
                      }
                    }

                    // Axios Alternative:
                    // const response = await axios.post(process.env.API_URL || 'http://localhost:5000/api/analyze', formData);
                    ```
                    """
                )
elif st.session_state.get("raw_response") and not analyze_clicked:
    with st.container():
        st.markdown("---")
        render_html('<div class="section-header">📋 Report Translation & Summary</div>')
        st.markdown(st.session_state["raw_response"])

# ================= 5. BOTTOM SECTION: MANDATORY MEDICAL DISCLAIMER =================
disclaimer_html = """
<div class="disclaimer-card">
    🔒 <strong>Mandatory Medical Disclaimer:</strong> MedTranslate AI is an informational tool created for 
    educational and communication assistance only. It is <strong>not</strong> a substitute for professional 
    medical diagnosis, advice, or treatment. Always consult a qualified, licensed healthcare provider 
    regarding any laboratory test results or underlying medical conditions.
</div>
"""
render_html(disclaimer_html)
