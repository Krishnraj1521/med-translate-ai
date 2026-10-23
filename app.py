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

# ==============================================================================
# 1. TOP HEADER BAR WITH THEME TOGGLE ON TOP RIGHT
# ==============================================================================
col_header_title, col_header_theme = st.columns([3, 1])

with col_header_theme:
    theme = st.radio("🎨 Theme Mode", ["☀️ Light", "🌙 Dark"], index=0, horizontal=True, key="top_theme_toggle")

# ==============================================================================
# 2. DYNAMIC CSS (HIDE SIDEBAR & FIX LIGHT MODE FONT READABILITY)
# ==============================================================================
if theme == "☀️ Light":
    st.markdown("""
    <style>
        /* Hide Streamlit Sidebar Completely */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }

        /* Global Background & Strict Dark Text Color Fix for Light Mode */
        .stApp, .stApp * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
        
        p, span, label, h1, h2, h3, h4, h5, h6, div, [data-testid="stMarkdownContainer"] p { color: #0F172A !important; }
        strong, b { color: #020617 !important; }
        
        /* Widget Labels & Selectbox Text Color Fix */
        .stSelectbox label, .stFileUploader label, .stRadio label, .stTextInput label { color: #0F172A !important; font-weight: 700 !important; }
        div[data-baseweb="select"] * { color: #0F172A !important; background-color: #FFFFFF !important; }
        div[data-baseweb="menu"] * { color: #0F172A !important; background-color: #FFFFFF !important; }
        input { color: #0F172A !important; background-color: #FFFFFF !important; }

        /* Sticky Disclaimer Banner */
        .sticky-disclaimer-banner { background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 10px 18px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .disclaimer-text { color: #92400E !important; font-size: 0.88rem; line-height: 1.4; }
        .disclaimer-text strong { color: #B45309 !important; }

        /* Cards & Metric Container Styling */
        .hero-summary-card { background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 6px solid #22C55E; border-radius: 12px; padding: 22px 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        .hero-summary-body { color: #15803D !important; font-size: 1.05rem; line-height: 1.65; }

        .flagged-card-soft { background: #FFFBEB; border: 1px solid #FDE68A; border-left: 6px solid #F59E0B; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; }
        .metric-row-normal { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #22C55E; border-radius: 12px; padding: 18px 22px; margin-bottom: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        
        .metric-name { color: #0F172A !important; font-size: 1.05rem; font-weight: 700; }
        .metric-value-alert { color: #D97706 !important; font-weight: 800; font-size: 1.35rem; }
        .metric-ref-alert { color: #475569 !important; font-size: 0.85rem; margin-left: 10px; }
        
        .metric-value-normal { color: #15803D !important; font-weight: 800; font-size: 1.35rem; }
        .metric-ref-normal { color: #475569 !important; font-size: 0.88rem; }
        
        .plain-english-box { background: #FEF3C7; border: 1px solid #FDE68A; border-radius: 8px; padding: 10px 14px; margin-top: 10px; }
        .plain-english-title { color: #B45309 !important; font-weight: 700; font-size: 0.84rem; margin-bottom: 4px; }
        .plain-english-text { color: #92400E !important; font-size: 0.92rem; line-height: 1.55; }
        .metric-explanation-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; color: #334155 !important; font-size: 0.88rem; margin-top: 10px;}

        .badge-soft-amber { background-color: #FEF3C7; color: #D97706 !important; border: 1px solid #F59E0B; padding: 4px 12px; font-size: 0.78rem; font-weight: 700; border-radius: 9999px; }
        .badge-normal-dark { background-color: #DCFCE7; color: #15803D !important; border: 1px solid #22C55E; padding: 4px 12px; font-size: 0.78rem; font-weight: 700; border-radius: 9999px; }
        
        .section-header { color: #0F172A !important; font-size: 1.25rem; font-weight: 700; margin-top: 24px; margin-bottom: 8px; }
        .section-subtext { color: #475569 !important; font-size: 0.9rem; margin-bottom: 16px; }

        .dictionary-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .dictionary-title { color: #0F172A !important; font-size: 1rem; font-weight: 700; }
        .dictionary-subtext { color: #475569 !important; font-size: 0.84rem; margin-bottom: 12px; }
        .dictionary-chip { background: #F1F5F9; border: 1px solid #CBD5E1; color: #334155 !important; border-radius: 9999px; padding: 5px 12px; font-size: 0.8rem; font-weight: 600; cursor: help; }
        
        .banner-alert { background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 6px solid #EF4444; border-radius: 10px; padding: 14px 18px; color: #991B1B !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 18px; display: flex; align-items: center; gap: 12px;}
        .banner-normal { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 6px solid #22C55E; border-radius: 10px; padding: 14px 18px; color: #166534 !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 18px; display: flex; align-items: center; gap: 12px;}

        /* Interactive Medical Acronym Tooltip */
        .med-tooltip-container { position: relative; display: inline-flex; align-items: center; gap: 6px; cursor: help; }
        .tooltip-badge { font-size: 0.75rem; color: #2563EB !important; background: #DBEAFE; border: 1px solid #BFDBFE; border-radius: 50%; width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; }
        .med-tooltip-text { visibility: hidden; opacity: 0; width: 280px; background: #1E293B; color: #F8FAFC !important; text-align: left; border-radius: 8px; padding: 10px 14px; position: absolute; z-index: 10000; bottom: 125%; left: 0; font-size: 0.82rem; font-weight: 400; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2); }
        .med-tooltip-container:hover .med-tooltip-text { visibility: visible; opacity: 1; }

        /* Metric Cards */
        [data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; padding: 16px 20px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; }
        [data-testid="stMetricLabel"] p { color: #475569 !important; font-weight: 600 !important; }
        [data-testid="stMetricValue"] div { color: #0F172A !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        /* Hide Streamlit Sidebar Completely */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }

        .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        
        .sticky-disclaimer-banner { background: linear-gradient(90deg, #451a03 0%, #78350f 50%, #451a03 100%); border: 1px solid #f59e0b; border-radius: 10px; padding: 10px 18px; margin-bottom: 20px; }
        .disclaimer-text { color: #fef3c7 !important; font-size: 0.88rem; line-height: 1.4; }
        .disclaimer-text strong { color: #fbbf24 !important; }

        .hero-summary-card { background: linear-gradient(135deg, #1E222B 0%, #161B22 100%); border: 1px solid #30363D; border-left: 6px solid #00E5FF; border-radius: 14px; padding: 22px 24px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4); }
        .hero-summary-body { color: #E6EDF3 !important; font-size: 1.05rem; line-height: 1.65; }

        .flagged-card-soft { background: linear-gradient(135deg, rgba(69, 26, 3, 0.4) 0%, #1f1d24 100%); border: 1px solid rgba(245, 158, 11, 0.45); border-left: 6px solid #f59e0b; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; }
        .metric-row-normal { background-color: #1E222B; border: 1px solid #30363D; border-left: 5px solid #238636; border-radius: 12px; padding: 18px 22px; margin-bottom: 14px; }

        .metric-name { color: #FFFFFF !important; font-size: 1.05rem; font-weight: 700; }
        .metric-value-alert { color: #fb923c !important; font-weight: 800; font-size: 1.35rem; }
        .metric-ref-alert { color: #94a3b8 !important; font-size: 0.85rem; margin-left: 10px; }
        
        .metric-value-normal { color: #00E5FF !important; font-weight: 800; font-size: 1.35rem; }
        .metric-ref-normal { color: #8B949E !important; font-size: 0.88rem; }

        .plain-english-box { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 8px; padding: 10px 14px; margin-top: 10px; }
        .plain-english-title { color: #fbbf24 !important; font-weight: 700; font-size: 0.84rem; margin-bottom: 4px; }
        .plain-english-text { color: #fef3c7 !important; font-size: 0.92rem; line-height: 1.55; }
        .metric-explanation-box { background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 14px; color: #E6EDF3 !important; font-size: 0.88rem; margin-top: 10px;}

        .badge-soft-amber { background-color: #d97706; color: #ffffff !important; border: 1px solid #f59e0b; padding: 4px 12px; font-size: 0.78rem; font-weight: 700; border-radius: 9999px; }
        .badge-normal-dark { background-color: #238636; color: #FFFFFF !important; border: 1px solid #2ea043; padding: 4px 12px; font-size: 0.78rem; font-weight: 700; border-radius: 9999px; }

        .section-header { color: #00E5FF !important; font-size: 1.35rem; font-weight: 700; margin-top: 28px; margin-bottom: 8px; }
        .section-subtext { color: #8B949E !important; font-size: 0.9rem; margin-bottom: 16px; }

        .dictionary-card { background: linear-gradient(135deg, #111827 0%, #1a2234 100%); border: 1px solid rgba(0, 229, 255, 0.25); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; }
        .dictionary-title { color: #00E5FF !important; font-size: 1rem; font-weight: 700; }
        .dictionary-subtext { color: #94A3B8 !important; font-size: 0.84rem; margin-bottom: 12px; }
        .dictionary-chip { background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.3); color: #E2E8F0 !important; border-radius: 9999px; padding: 5px 12px; font-size: 0.8rem; font-weight: 600; cursor: help; }

        .banner-alert { background-color: #23191E; border: 1px solid #DA363388; border-left: 6px solid #DA3633; border-radius: 10px; padding: 14px 18px; color: #FFFFFF !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 18px; display: flex; align-items: center; gap: 12px;}
        .banner-normal { background-color: #16241C; border: 1px solid #23863688; border-left: 6px solid #238636; border-radius: 10px; padding: 14px 18px; color: #FFFFFF !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 18px; display: flex; align-items: center; gap: 12px;}

        /* Interactive Medical Acronym Tooltip */
        .med-tooltip-container { position: relative; display: inline-flex; align-items: center; gap: 6px; cursor: help; }
        .tooltip-badge { font-size: 0.75rem; color: #00E5FF !important; background: rgba(0, 229, 255, 0.15); border: 1px solid rgba(0, 229, 255, 0.4); border-radius: 50%; width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; }
        .med-tooltip-text { visibility: hidden; opacity: 0; width: 280px; background: #111827; color: #E2E8F0 !important; text-align: left; border: 1px solid #00E5FF; border-radius: 8px; padding: 10px 14px; position: absolute; z-index: 10000; bottom: 125%; left: 0; font-size: 0.82rem; font-weight: 400; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6); }
        .med-tooltip-container:hover .med-tooltip-text { visibility: visible; opacity: 1; }

        /* Metric Cards */
        [data-testid="stMetric"] { background: linear-gradient(135deg, #1A202C 0%, #161B22 100%) !important; border: 1px solid #30363D !important; border-radius: 12px !important; padding: 16px 20px !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important; }
        [data-testid="stMetricLabel"] p { color: #8B949E !important; font-weight: 600 !important; }
        [data-testid="stMetricValue"] div { color: #00E5FF !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# Helper function to render HTML
def render_html(html_str: str):
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)

# ==============================================================================
# 3. INTERACTIVE MEDICAL DICTIONARY & IMAGE COMPRESSION (API FIX)
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
    name_clean = name.strip()
    matched_term = None
    for term, definition in MEDICAL_DICTIONARY.items():
        if term.lower() in name_clean.lower():
            matched_term = (term, definition)
            break
    if matched_term:
        term, definition = matched_term
        return f'<span class="med-tooltip-container"><strong class="metric-name">{name_clean}</strong><span class="tooltip-badge">ℹ️</span><span class="med-tooltip-text"><strong>{term}:</strong> {definition}</span></span>'
    else:
        return f'<strong class="metric-name">{name_clean}</strong>'

def optimize_image_for_api(pil_image: Image.Image) -> Image.Image:
    """Fast Image Compression to fix API 'read operation timed out' limits."""
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    pil_image.thumbnail((1600, 1600))  # Drastically speeds up Gemini processing
    return pil_image

# Realistic Multi-Language Sample Data
SAMPLE_DATA = {
    "English": {
        "summary": "This routine lab panel shows that your basic blood cell counts and kidney functions are completely healthy. However, your fasting blood glucose and LDL cholesterol are slightly above standard reference ranges, which warrants a discussion with your doctor regarding diet and lifestyle.",
        "overall_status": "Attention Needed",
        "metrics": [
            {"name": "Fasting Blood Glucose", "value": "118 mg/dL", "reference_range": "70 – 99 mg/dL", "status": "High", "explanation": "Elevated fasting blood sugar, which can suggest early insulin resistance or pre-diabetes."},
            {"name": "Hemoglobin A1c (HbA1c)", "value": "5.9 %", "reference_range": "< 5.7 %", "status": "High", "explanation": "Reflects your 3-month average blood glucose; slightly above the normal boundary."},
            {"name": "Total Cholesterol", "value": "215 mg/dL", "reference_range": "< 200 mg/dL", "status": "High", "explanation": "Overall blood lipid count is mildly elevated, primarily driven by LDL particles."},
            {"name": "LDL Cholesterol", "value": "138 mg/dL", "reference_range": "< 100 mg/dL", "status": "High", "explanation": "Known as 'bad' cholesterol; excess amounts can gradually build up in arterial walls."},
            {"name": "HDL Cholesterol", "value": "48 mg/dL", "reference_range": "> 40 mg/dL", "status": "Normal", "explanation": "Known as 'good' cholesterol; helps remove other cholesterol forms from the bloodstream."},
            {"name": "Serum Creatinine", "value": "0.9 mg/dL", "reference_range": "0.6 – 1.2 mg/dL", "status": "Normal", "explanation": "Measures kidney filtration efficiency; demonstrates optimal kidney performance."},
            {"name": "Hemoglobin", "value": "14.2 g/dL", "reference_range": "13.0 – 17.0 g/dL", "status": "Normal", "explanation": "Protein carrying oxygen throughout the body; confirms healthy red blood cell levels."},
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
            {"name": "फास्टिंग ब्लड ग्लूकोज", "value": "118 mg/dL", "reference_range": "70 – 99 mg/dL", "status": "High", "explanation": "खाली पेट रक्त शर्करा का बढ़ा हुआ स्तर, जो प्री-डायबिटीज का प्रारंभिक संकेत हो सकता है।"},
            {"name": "हीमोग्लोबिन A1c (HbA1c)", "value": "5.9 %", "reference_range": "< 5.7 %", "status": "High", "explanation": "पिछले 3 महीनों के औसत ब्लड शुगर को दर्शाता है; सामान्य सीमा से थोड़ा ऊपर है।"},
            {"name": "कुल कोलेस्ट्रॉल", "value": "215 mg/dL", "reference_range": "< 200 mg/dL", "status": "High", "explanation": "रक्त में कुल कोलेस्ट्रॉल स्तर सामान्य से अधिक है, मुख्य रूप से एलडीएल में वृद्धि के कारण।"},
            {"name": "एलडीएल कोलेस्ट्रॉल", "value": "138 mg/dL", "reference_range": "< 100 mg/dL", "status": "High", "explanation": "'खराब कोलेस्ट्रॉल' के रूप में जाना जाता है; अधिक मात्रा धमनियों में रुकावट पैदा कर सकती है।"},
            {"name": "एचडीएल कोलेस्ट्रॉल", "value": "48 mg/dL", "reference_range": "> 40 mg/dL", "status": "Normal", "explanation": "'अच्छा कोलेस्ट्रॉल'; हृदय स्वास्थ्य की रक्षा करता है और बिल्कुल सामान्य है।"},
            {"name": "सीरम क्रिएटिनिन", "value": "0.9 mg/dL", "reference_range": "0.6 – 1.2 mg/dL", "status": "Normal", "explanation": "गुर्दे की कार्यप्रणाली का सूचक; आपकी किडनी बिल्कुल स्वस्थ और सामान्य है।"},
            {"name": "हीमोग्लोबिन", "value": "14.2 g/dL", "reference_range": "13.0 – 17.0 g/dL", "status": "Normal", "explanation": "लाल रक्त कोशिकाओं में ऑक्सीजन ले जाने वाला प्रोटीन; एनीमिया का कोई लक्षण नहीं है।"},
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
            {"name": "फास्टिंग ब्लड ग्लुकोज", "value": "118 mg/dL", "reference_range": "70 – 99 mg/dL", "status": "High", "explanation": "उपाशीपोटी रक्तातील साखरेचे वाढलेले प्रमाण, जे प्री-डायबेटिसचे प्रारंभिक लक्षण असू शकते."},
            {"name": "हिमोग्लोबिन A1c (HbA1c)", "value": "5.9 %", "reference_range": "< 5.7 %", "status": "High", "explanation": "मागील ३ महिन्यांतील रक्तातील साखरेची सरासरी पातळी दर्शवते; सामान्य प्रमाणापेक्षा किंचित जास्त आहे."},
            {"name": "एकूण कोलेस्ट्रॉल", "value": "215 mg/dL", "reference_range": "< 200 mg/dL", "status": "High", "explanation": "रक्तातील एकूण कोलेस्ट्रॉल थोडे जास्त आहे, प्रामुख्याने एलडीएल कोलेस्ट्रॉल वाढल्यामुळे."},
            {"name": "एलडीएल कोलेस्ट्रॉल", "value": "138 mg/dL", "reference_range": "< 100 mg/dL", "status": "High", "explanation": "'वाईट कोलेस्ट्रॉल' म्हणून ओळखले जाते; याचे वाढलेले प्रमाण काळजीपूर्वक नियंत्रित करणे गरजेचे आहे."},
            {"name": "एचडीएल कोलेस्ट्रॉल", "value": "48 mg/dL", "reference_range": "> 40 mg/dL", "status": "Normal", "explanation": "'चांगले कोलेस्ट्रॉल'; हृदयाचे रक्षण करते आणि योग्य प्रमाणात आहे."},
            {"name": "सीरम क्रिएटिनिन", "value": "0.9 mg/dL", "reference_range": "0.6 – 1.2 mg/dL", "status": "Normal", "explanation": "किडनीची कार्यक्षमता मोजणारा घटक; तुमची किडनी योग्य प्रकारे काम करत आहे."},
            {"name": "हिमोग्लोबिन", "value": "14.2 g/dL", "reference_range": "13.0 – 17.0 g/dL", "status": "Normal", "explanation": "रक्तातील प्राणवायू वाहून नेणारे प्रथिन; अॅनिमियाची कोणतीही लक्षणे नाहीत."},
        ],
        "doctor_questions": [
            "माझ्या रक्तातील साखर आणि HbA1c नियंत्रित करण्यासाठी आहारातील कोणते बदल पुरेसे ठरतील?",
            "एलडीएल कोलेस्ट्रॉल कमी करण्यासाठी मला जीवनशैलीत कोणते विशिष्ट बदल करावे लागतील?",
            "या चाचण्यांची पुन्हा कधी तपासणी करून घ्यावी लागेल?",
        ],
    },
    "Spanish": {
        "summary": "Este panel de laboratorio rutinario indica que sus recuentos sanguíneos y funciones renales son completamente saludables. No obstante, su glucosa en ayunas y el colesterol LDL se encuentran ligeramente por encima de los límites normales, por lo que se aconseja consultar con su médico sobre ajustes en su estilo de vida.",
        "overall_status": "Attention Needed",
        "metrics": [
            {"name": "Glucosa en ayunas", "value": "118 mg/dL", "reference_range": "70 – 99 mg/dL", "status": "High", "explanation": "Nivel elevado de azúcar en sangre en ayunas, lo que puede sugerir resistencia temprana a la insulina o prediabetes."},
            {"name": "Hemoglobina A1c (HbA1c)", "value": "5.9 %", "reference_range": "< 5.7 %", "status": "High", "explanation": "Refleja el promedio de azúcar en sangre durante los últimos 3 meses; ligeramente por encima del límite normal."},
            {"name": "Colesterol Total", "value": "215 mg/dL", "reference_range": "< 200 mg/dL", "status": "High", "explanation": "El colesterol total en sangre está ligeramente elevado, impulsado principalmente por el colesterol LDL."},
            {"name": "Colesterol LDL", "value": "138 mg/dL", "reference_range": "< 100 mg/dL", "status": "High", "explanation": "Conocido como colesterol 'malo'; niveles excesivos pueden acumular placa en las arterias con el tiempo."},
            {"name": "Colesterol HDL", "value": "48 mg/dL", "reference_range": "> 40 mg/dL", "status": "Normal", "explanation": "Conocido como colesterol 'bueno'; ayuda a retirar el exceso de lípidos y se encuentra en rango saludable."},
            {"name": "Creatinina sérica", "value": "0.9 mg/dL", "reference_range": "0.6 – 1.2 mg/dL", "status": "Normal", "explanation": "Indicador de función renal; demuestra una filtración renal saludable y óptima."},
            {"name": "Hemoglobina", "value": "14.2 g/dL", "reference_range": "13.0 – 17.0 g/dL", "status": "Normal", "explanation": "Proteína encargada de transportar oxígeno; confirma que no hay signos de anemia."},
        ],
        "doctor_questions": [
            "¿Mis niveles de glucosa y HbA1c requieren cambios en la dieta y ejercicio, o deberíamos evaluar medicación?",
            "¿Qué pautas nutricionales específicas debo seguir para reducir el colesterol LDL de manera efectiva?",
            "¿Cuándo sugiere programar análisis de sangre de seguimiento para evaluar el progreso?",
        ],
    },
}

# ==============================================================================
# 4. CLEAN UI LAYOUT (HEADER, SETTINGS EXPANDER & UPLOAD BAR WITH LANGUAGE)
# ==============================================================================
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

# Title Header
st.markdown("""
<div style="text-align: center; max-width: 850px; margin: 0 auto; padding-bottom: 15px;">
    <h2 style="font-weight: 800; margin-bottom: 10px;">🩺 MedReport <span style="color: #22C55E;">AI</span></h2>
    <p style="font-size: 1.1rem; line-height: 1.6;">
        Raw lab reports with cryptic acronyms cause unnecessary fear. <strong>MedReport AI</strong> instantly translates complex bloodwork into warm, 8th-grade explanations and ready-to-ask questions for your doctor.
    </p>
</div>
""", unsafe_allow_html=True)

# Collapsible Settings Bar (For API key input and Demo Mode)
with st.expander("⚙️ API Key & Advanced Settings", expanded=False):
    col_cfg1, col_cfg2 = st.columns([2, 1])
    with col_cfg2:
        demo_mode = st.checkbox("Demo / Offline Mode", value=False, help="Use realistic sample data for testing.")
    with col_cfg1:
        api_key_input = st.text_input("Gemini API Key", value=default_api_key, type="password", disabled=demo_mode)

if demo_mode:
    st.warning("⚠️ DEMO MODE ACTIVE: Displaying sample mock data.")

def clear_analysis_state():
    if "analysis_result" in st.session_state: st.session_state.analysis_result = None
    if "raw_response" in st.session_state: st.session_state.raw_response = None
    if "dashboard_data" in st.session_state: st.session_state.dashboard_data = None

# Session state initialization
if "file_hash" not in st.session_state: st.session_state["file_hash"] = None
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "raw_response" not in st.session_state: st.session_state.raw_response = None
if "dashboard_data" not in st.session_state: st.session_state.dashboard_data = None

# UPLOAD BAR WITH INTEGRATED LANGUAGE SELECTOR
col_up, col_lang = st.columns([3, 1], gap="medium")

with col_up:
    uploaded_file = st.file_uploader(
        "Drop your lab report here or click to browse (PDF, PNG, JPG, JPEG)",
        type=["jpg", "jpeg", "png", "pdf"],
        on_change=clear_analysis_state,
        key="lab_report_uploader",
    )

with col_lang:
    selected_language = st.selectbox(
        "🌐 Target Language",
        options=["English", "Hindi", "Marathi", "Spanish"],
        index=0,
        key="upload_bar_lang_select",
        help="Select the language for the report explanation."
    )

if "current_lang" not in st.session_state: 
    st.session_state.current_lang = selected_language

# Hash Tracking
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    current_hash = hashlib.md5(file_bytes).hexdigest()
    if st.session_state.get("file_hash") != current_hash:
        st.session_state["file_hash"] = current_hash
        clear_analysis_state()
else:
    st.session_state["file_hash"] = None
    clear_analysis_state()

# Centered Action Buttons
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    load_sample_clicked = st.button("⚡ Instant Judge Demo (Load Sample Report)", use_container_width=True)
with col_btn2:
    analyze_clicked = st.button("🔬 Analyze Lab Report", type="primary", use_container_width=True)

if load_sample_clicked:
    with st.status("⚡ Loading Clinical Mock Report for Judges...", expanded=True) as status:
        time.sleep(0.1)
        demo_data = SAMPLE_DATA.get(selected_language, SAMPLE_DATA["English"])
        st.session_state.analysis_result = demo_data
        st.session_state.dashboard_data = demo_data
        st.session_state.dashboard_source = "Demo Sample Report"
        st.session_state.current_lang = selected_language
        status.update(label="✅ Sample Report Loaded Instantly!", state="complete", expanded=False)
        st.rerun()

# Intro Info Cards
if not uploaded_file and not st.session_state.analysis_result:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.info("**📖 8th-Grade Reading Level**\n\nSimplifies complex medical terminology into plain, reassuring English.")
    c2.warning("**⚠️ Action Highlighting**\n\nInstantly flags out-of-range metrics and explains them clearly.")
    c3.success("**🩺 Doctor Checklist**\n\nAuto-generates relevant questions tailored for your next doctor's visit.")

# ==============================================================================
# 5. GEMINI API CALLS (WITH EXTENDED 120 SECOND TIMEOUT & PROMPT FIX)
# ==============================================================================
def is_rate_limit_or_high_demand(err: Exception) -> bool:
    err_str = str(err).lower()
    return "429" in err_str or "503" in err_str or "quota" in err_str or "timeout" in err_str

def call_model_stream_with_timeout(
    client, model_name: str, active_image, language: str, system_instruction: str, stream_placeholder=None
):
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
        max_output_tokens=1500,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=120000), 
    )

    accumulated_text = ""
    start_time = time.time()
    stream = client.models.generate_content_stream(
        model=model_name,
        contents=[active_image, f"Extract and analyze key lab metrics into JSON in {language}. Keep string values concise."],
        config=config,
    )

    for chunk in stream:
        if time.time() - start_time > 120.0:
            raise TimeoutError("Gemini streaming request exceeded strict 120-second deadline.")
        if chunk.text:
            accumulated_text += chunk.text

    if not accumulated_text.strip():
        raise RuntimeError("Model returned an empty response stream.")
    return accumulated_text

def parse_report_json(response_text: str):
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
    try: return json.loads(cleaned_text)
    except Exception: return None

def analyze_lab_report(active_image, language: str, api_key: str, stream_placeholder=None):
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
Strict prompt efficiency and payload constraints:
- CRITICAL UNIT FIX: Ensure accurate medical units for each metric based on standard clinical formats. E.g., Glucose and Cholesterol should use 'mg/dL' or 'mmol/L'. Hemoglobin should use 'g/dL'. DO NOT use 'cumm' (cubic millimeters) for Glucose or Lipids.
- Metrics: Strictly 3 to 5 key parameters (prioritize abnormal or flagged findings).
- Metric Explanation: Strictly 1 brief sentence (under 15 words).
- Output ONLY the raw JSON object. Do NOT wrap in markdown.
"""
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=120000))
    
    try:
        response_text = call_model_stream_with_timeout(client, "gemini-3.8-flash", active_image, language, system_instruction, stream_placeholder)
        return response_text, "gemini-3.8-flash"
    except Exception as e_primary:
        if is_rate_limit_or_high_demand(e_primary):
            try:
                response_text = call_model_stream_with_timeout(client, "gemini-3.5-flash-lite", active_image, language, system_instruction, stream_placeholder)
                return response_text, "gemini-3.5-flash-lite"
            except Exception as e_fallback:
                raise e_fallback
        raise e_primary

# ==============================================================================
# 6. PROCESSING & DASHBOARD RENDERING
# ==============================================================================
if analyze_clicked:
    active_api_key = api_key_input.strip() if api_key_input else ""
    if not active_api_key and not demo_mode:
        st.warning("⚠️ Please provide a Gemini API Key in '⚙️ API Key & Advanced Settings' or check 'Demo / Offline Mode'.")
    elif uploaded_file is None:
        st.warning("⚠️ Please upload a lab report image (JPG, JPEG, PNG) before analyzing.")
    else:
        try:
            uploaded_file.seek(0)
            raw_image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            active_image = optimize_image_for_api(raw_image)
        except Exception as e:
            st.error(f"Failed to read image: {e}")
            active_image = None

        if active_image is not None:
            with st.status("⚡ Translating Lab Report...", expanded=True) as status:
                try:
                    status.update(label="📸 Scanning lab report & identifying parameters...", state="running")
                    stream_placeholder = st.empty()
                    
                    response_text, source_name = analyze_lab_report(
                        active_image=active_image,
                        language=selected_language,
                        api_key=active_api_key,
                        stream_placeholder=stream_placeholder,
                    )
                    
                    data = parse_report_json(response_text)

                    if data is not None and isinstance(data, dict):
                        status.update(label="📊 Generating personalized clinical dashboard...", state="running")
                        st.session_state.analysis_result = data
                        st.session_state.dashboard_data = data
                        st.session_state.current_lang = selected_language
                        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                    else:
                        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                        st.session_state.raw_response = response_text

                except Exception as ex:
                    status.update(label="❌ Analysis Failed (Timeout or Server Limit)", state="error", expanded=True)
                    st.error(f"API Error: {ex}")

# Render the Split-Screen Results Dashboard
active_dashboard_data = st.session_state.get("analysis_result") or st.session_state.get("dashboard_data")
if active_dashboard_data is not None:
    data = active_dashboard_data
    lang = st.session_state.get("current_lang", selected_language)
    metrics = data.get("metrics", [])
    doctor_questions = data.get("doctor_questions", [])
    summary_text = data.get("summary", "")

    flagged_metrics = [m for m in metrics if str(m.get("status", "")).strip().capitalize() in ["High", "Low", "Abnormal"]]
    normal_metrics = [m for m in metrics if str(m.get("status", "")).strip().capitalize() not in ["High", "Low", "Abnormal"]]
    is_attention_needed = len(flagged_metrics) > 0

    st.markdown("---")
    
    # "Plain-English Executive Summary" Panel
    render_html('<div style="font-size: 0.85rem; font-weight: 700; color: #166534; margin-bottom: 5px;">📖 PLAIN-ENGLISH EXECUTIVE SUMMARY</div>')
    render_html(f'<div class="hero-summary-card"><div class="hero-summary-body">{summary_text}</div></div>')

    # Top KPI Metrics
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1: st.metric("TOTAL MARKERS CHECKED", len(metrics))
    with col_stat2: st.metric("NORMAL / OPTIMAL COUNT", len(normal_metrics))
    with col_stat3: st.metric("REQUIRES ATTENTION", len(flagged_metrics), delta=f"{len(flagged_metrics)} out of range" if is_attention_needed else "All clear", delta_color="inverse" if is_attention_needed else "normal")
    st.markdown("<br>", unsafe_allow_html=True)

    # Helper Card HTML Functions
    def build_flagged_card_html(fm: dict) -> str:
        status_text = str(fm.get("status", "Abnormal")).upper()
        name_html = format_metric_name_with_tooltip(fm.get("name", "Metric"))
        val = fm.get("value", "N/A")
        ref = fm.get("reference_range", "N/A")
        expl = fm.get("explanation", "")
        return f"""
        <div class="flagged-card-soft">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                {name_html} <span class="badge-soft-amber">⚠️ {status_text}</span>
            </div>
            <div style="margin-bottom: 8px;">
                <span class="metric-value-alert">{val}</span>
                <span class="metric-ref-alert">(Standard Range: <strong>{ref}</strong>)</span>
            </div>
            <div class="plain-english-box">
                <div class="plain-english-title">💡 What this means in plain English:</div>
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
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                {name_html} <span class="badge-normal-dark">✅ NORMAL</span>
            </div>
            <div style="display: flex; gap: 20px; align-items: baseline; margin-bottom: 10px;">
                <div><span class="metric-ref-normal">Value: </span><span class="metric-value-normal">{val}</span></div>
                <div><span class="metric-ref-normal">Range: <strong>{ref}</strong></span></div>
            </div>
            <div class="metric-explanation-box">💡 <strong>Explanation:</strong> {expl}</div>
        </div>
        """

    # Section A (Flagged) & Section B (Normal) columns
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        render_html(f'<div class="section-header">Section A: Action Items for Doctor ({len(flagged_metrics)})</div>')
        if is_attention_needed:
            for fm in flagged_metrics: render_html(build_flagged_card_html(fm))
        else:
            render_html('<div class="banner-normal">✅ All Markers Normal. No out-of-range values detected.</div>')

        # Doctor Questions
        st.markdown('<div class="section-header" style="font-size: 1.15rem;">🩺 Questions to Ask Your Doctor</div>', unsafe_allow_html=True)
        for q_idx, question in enumerate(doctor_questions, start=1):
            st.checkbox(f"**Q{q_idx}:** {question}", value=True, key=f"split_q_{q_idx}")

    with col_right:
        render_html(f'<div class="section-header">Section B: Normal Results & Dictionary ({len(normal_metrics)})</div>')
        
        dictionary_html = """
        <div class="dictionary-card">
            <div class="dictionary-title">📖 Interactive Acronym Dictionary</div>
            <div class="dictionary-subtext">Hover over any medical abbreviation for a plain-English explanation:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                <span class="med-tooltip-container"><span class="dictionary-chip">CBC ℹ️</span><span class="med-tooltip-text"><strong>CBC (Complete Blood Count):</strong> A routine blood test measuring red cells, white cells, and platelets.</span></span>
                <span class="med-tooltip-container"><span class="dictionary-chip">HDL ℹ️</span><span class="med-tooltip-text"><strong>HDL (High-Density Lipoprotein):</strong> "Good" cholesterol that clears excess fats from arteries back to the liver.</span></span>
                <span class="med-tooltip-container"><span class="dictionary-chip">LDL ℹ️</span><span class="med-tooltip-text"><strong>LDL (Low-Density Lipoprotein):</strong> "Bad" cholesterol that can build plaque in arteries if high.</span></span>
                <span class="med-tooltip-container"><span class="dictionary-chip">HbA1c ℹ️</span><span class="med-tooltip-text"><strong>HbA1c (Hemoglobin A1c):</strong> Key test reflecting your 3-month average blood glucose levels.</span></span>
            </div>
        </div>
        """
        render_html(dictionary_html)

        if normal_metrics:
            for nm in normal_metrics: render_html(build_normal_card_html(nm))
        else:
            st.info("No normal markers in this panel.")

# Mandatory Disclaimer
render_html("""
<div style="background-color: transparent; border-top: 1px solid #CBD5E1; padding-top: 20px; margin-top: 40px; font-size: 0.85rem; line-height: 1.6; text-align: center;">
    🔒 <strong>Mandatory Medical Disclaimer:</strong> MedTranslate AI is an informational tool created for educational and communication assistance only. It is <strong>not</strong> a substitute for professional medical diagnosis, advice, or treatment. Always consult a qualified healthcare provider regarding laboratory test results.
</div>
""")
