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
    page_title="🩺 MedTranslate AI",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
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
            {
                "name": "हीमोग्लोबिन A1c (HbA1c)",
                "value": "5.9 %",
                "reference_range": "< 5.7 %",
                "status": "High",
                "explanation": "पिछले 3 महीनों के औसत ब्लड शुगर को दर्शाता है; सामान्य सीमा से थोड़ा ऊपर है।",
            },
            {
                "name": "कुल कोलेस्ट्रॉल",
                "value": "215 mg/dL",
                "reference_range": "< 200 mg/dL",
                "status": "High",
                "explanation": "रक्त में कुल कोलेस्ट्रॉल स्तर सामान्य से अधिक है, मुख्य रूप से एलडीएल में वृद्धि के कारण।",
            },
            {
                "name": "एलडीएल कोलेस्ट्रॉल",
                "value": "138 mg/dL",
                "reference_range": "< 100 mg/dL",
                "status": "High",
                "explanation": "'खराब कोलेस्ट्रॉल' के रूप में जाना जाता है; अधिक मात्रा धमनियों में रुकावट पैदा कर सकती है।",
            },
            {
                "name": "एचडीएल कोलेस्ट्रॉल",
                "value": "48 mg/dL",
                "reference_range": "> 40 mg/dL",
                "status": "Normal",
                "explanation": "'अच्छा कोलेस्ट्रॉल'; हृदय स्वास्थ्य की रक्षा करता है और बिल्कुल सामान्य है।",
            },
            {
                "name": "सीरम क्रिएटिनिन",
                "value": "0.9 mg/dL",
                "reference_range": "0.6 – 1.2 mg/dL",
                "status": "Normal",
                "explanation": "गुर्दे की कार्यप्रणाली का सूचक; आपकी किडनी बिल्कुल स्वस्थ और सामान्य है।",
            },
            {
                "name": "हीमोग्लोबिन",
                "value": "14.2 g/dL",
                "reference_range": "13.0 – 17.0 g/dL",
                "status": "Normal",
                "explanation": "लाल रक्त कोशिकाओं में ऑक्सीजन ले जाने वाला प्रोटीन; एनीमिया का कोई लक्षण नहीं है।",
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
            {
                "name": "हिमोग्लोबिन A1c (HbA1c)",
                "value": "5.9 %",
                "reference_range": "< 5.7 %",
                "status": "High",
                "explanation": "मागील ३ महिन्यांतील रक्तातील साखरेची सरासरी पातळी दर्शवते; सामान्य प्रमाणापेक्षा किंचित जास्त आहे.",
            },
            {
                "name": "एकूण कोलेस्ट्रॉल",
                "value": "215 mg/dL",
                "reference_range": "< 200 mg/dL",
                "status": "High",
                "explanation": "रक्तातील एकूण कोलेस्ट्रॉल थोडे जास्त आहे, प्रामुख्याने एलडीएल कोलेस्ट्रॉल वाढल्यामुळे.",
            },
            {
                "name": "एलडीएल कोलेस्ट्रॉल",
                "value": "138 mg/dL",
                "reference_range": "< 100 mg/dL",
                "status": "High",
                "explanation": "'वाईट कोलेस्ट्रॉल' म्हणून ओळखले जाते; याचे वाढलेले प्रमाण काळजीपूर्वक नियंत्रित करणे गरजेचे आहे.",
            },
            {
                "name": "एचडीएल कोलेस्ट्रॉल",
                "value": "48 mg/dL",
                "reference_range": "> 40 mg/dL",
                "status": "Normal",
                "explanation": "'चांगले कोलेस्ट्रॉल'; हृदयाचे रक्षण करते आणि योग्य प्रमाणात आहे.",
            },
            {
                "name": "सीरम क्रिएटिनिन",
                "value": "0.9 mg/dL",
                "reference_range": "0.6 – 1.2 mg/dL",
                "status": "Normal",
                "explanation": "किडनीची कार्यक्षमता मोजणारा घटक; तुमची किडनी योग्य प्रकारे काम करत आहे.",
            },
            {
                "name": "हिमोग्लोबिन",
                "value": "14.2 g/dL",
                "reference_range": "13.0 – 17.0 g/dL",
                "status": "Normal",
                "explanation": "रक्तातील प्राणवायू वाहून नेणारे प्रथिन; अॅनिमियाची कोणतीही लक्षणे नाहीत.",
            },
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
            {
                "name": "Glucosa en ayunas",
                "value": "118 mg/dL",
                "reference_range": "70 – 99 mg/dL",
                "status": "High",
                "explanation": "Nivel elevado de azúcar en sangre en ayunas, lo que puede sugerir resistencia temprana a la insulina o prediabetes.",
            },
            {
                "name": "Hemoglobina A1c (HbA1c)",
                "value": "5.9 %",
                "reference_range": "< 5.7 %",
                "status": "High",
                "explanation": "Refleja el promedio de azúcar en sangre durante los últimos 3 meses; ligeramente por encima del límite normal.",
            },
            {
                "name": "Colesterol Total",
                "value": "215 mg/dL",
                "reference_range": "< 200 mg/dL",
                "status": "High",
                "explanation": "El colesterol total en sangre está ligeramente elevado, impulsado principalmente por el colesterol LDL.",
            },
            {
                "name": "Colesterol LDL",
                "value": "138 mg/dL",
                "reference_range": "< 100 mg/dL",
                "status": "High",
                "explanation": "Conocido como colesterol 'malo'; niveles excesivos pueden acumular placa en las arterias con el tiempo.",
            },
            {
                "name": "Colesterol HDL",
                "value": "48 mg/dL",
                "reference_range": "> 40 mg/dL",
                "status": "Normal",
                "explanation": "Conocido como colesterol 'bueno'; ayuda a retirar el exceso de lípidos y se encuentra en rango saludable.",
            },
            {
                "name": "Creatinina sérica",
                "value": "0.9 mg/dL",
                "reference_range": "0.6 – 1.2 mg/dL",
                "status": "Normal",
                "explanation": "Indicador de función renal; demuestra una filtración renal saludable y óptima.",
            },
            {
                "name": "Hemoglobina",
                "value": "14.2 g/dL",
                "reference_range": "13.0 – 17.0 g/dL",
                "status": "Normal",
                "explanation": "Proteína encargada de transportar oxígeno; confirma que no hay signos de anemia.",
            },
        ],
        "doctor_questions": [
            "¿Mis niveles de glucosa y HbA1c requieren cambios en la dieta y ejercicio, o deberíamos evaluar medicación?",
            "¿Qué pautas nutricionales específicas debo seguir para reducir el colesterol LDL de manera efectiva?",
            "¿Cuándo sugiere programar análisis de sangre de seguimiento para evaluar el progreso?",
        ],
    },
}

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")

    # Demo / Offline Mode Toggle
    demo_mode = st.checkbox(
        "Demo / Offline Mode",
        value=False,
        help="Use pre-generated realistic sample medical data for testing without calling external APIs.",
    )

    # API Key Input
    api_key_input = st.text_input(
        "Gemini API Key",
        value=default_api_key,
        type="password",
        disabled=demo_mode,
        help="Enter your Google Gemini API key. Defaults to GEMINI_API_KEY from .env.",
    )

    # Language Selector Dropdown
    selected_language = st.selectbox(
        "Target Language",
        options=["English", "Hindi", "Marathi", "Spanish"],
        index=0,
        help="Select the language for the translated report explanation.",
    )

    st.divider()

    # Medical Disclaimer Box
    st.markdown("### ⚠️ Clinical Notice")
    st.info(
        "**Educational Assistance Only:** MedTranslate AI does NOT provide medical diagnosis or treatment plans. "
        "Always review laboratory results with a licensed healthcare provider."
    )

# Main App Header
render_html(
    """
    <div class="medical-header-banner">
        <div class="banner-content">
            <div class="banner-left">
                <div class="banner-badge">
                    <span class="pulse-dot"></span>
                    <span>CLINICAL DIAGNOSTIC TRANSLATOR</span>
                </div>
                <h1 class="medical-banner-title">
                    <span class="med-icon">🩺</span> MedTranslate <span class="ai-gradient">AI</span>
                </h1>
                <p class="medical-banner-subtitle">
                    Clinical Lab Report Translator & Patient Guidance Dashboard
                </p>
                <div class="brand-title" style="display: none;">🩺 MedTranslate AI</div>
                <div class="brand-subtitle" style="display: none;">Clinical Lab Report Translator & Patient Guidance Dashboard</div>
            </div>
            <div class="banner-right-pills">
                <div class="clinical-pill"><span class="pill-icon">⚡</span> Sub-Second Inference</div>
                <div class="clinical-pill"><span class="pill-icon">🔒</span> In-Memory Diagnostic Engine</div>
                <div class="clinical-pill"><span class="pill-icon">🌐</span> Multilingual Interpretation</div>
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
    st.session_state.current_lang = selected_language

# File Uploader with on_change callback
uploaded_file = st.file_uploader(
    "Upload Lab Report Scan (JPG, JPEG, PNG)",
    type=["jpg", "jpeg", "png"],
    help="Upload an image scan or clear photo of your lab test results.",
    on_change=clear_analysis_state,
    key="lab_report_uploader",
)

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
    st.image(uploaded_file, caption="Image queued for analysis", use_container_width=True)

# Analyze Button
analyze_clicked = st.button("Analyze Report", type="primary", use_container_width=True)
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

    # Structured Dashboard View: Metric Cards & Tabs Container
    with st.container():
        # Top KPI Summary Metric Cards Container
        with st.container():
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Parameters", len(metrics))
            with col_stat2:
                st.metric("In Normal Range", len(normal_metrics))
            with col_stat3:
                st.metric("Flagged / Out of Range", len(flagged_metrics))

        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        # Tabbed Structured Dashboard Sections
        tab_summary, tab_metrics, tab_flagged, tab_doctor = st.tabs([
            "📋 Executive Summary",
            f"📊 Lab Metrics Breakdown ({len(metrics)})",
            f"⚠️ Flagged Findings ({len(flagged_metrics)})",
            "🩺 Doctor Consultation",
        ])

        with tab_summary:
            with st.container():
                # ================= 1. TOP SECTION: EXECUTIVE SUMMARY =================
                render_html('<div class="section-header">📋 Executive Summary</div>')
                render_html('<div class="section-subtext">High-level translation and clinical status overview</div>')

                summary_html = f"""
<div class="hero-summary-card">
    <div class="hero-summary-title">Summary & Findings</div>
    <div class="hero-summary-body">{summary_text}</div>
</div>
"""
                render_html(summary_html)

                if is_attention_needed:
                    banner_html = f"""
<div class="banner-alert">
    <span>⚠️</span>
    <span><strong>Attention Recommended:</strong> {len(flagged_metrics)} out of {len(metrics)} analyzed metric(s) fall outside standard clinical reference ranges.</span>
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

        with tab_metrics:
            with st.container():
                # ================= 2. SECOND SECTION: LAB METRICS BREAKDOWN =================
                render_html('<div class="section-header">📊 Lab Metrics Breakdown</div>')
                render_html('<div class="section-subtext">Line-by-line stacked comparison of Patient Values vs Standard Reference Ranges</div>')

                if not metrics:
                    st.info("No metrics extracted.")
                else:
                    for m in metrics:
                        status_raw = str(m.get("status", "Normal")).strip()
                        is_flagged = status_raw.capitalize() in ["High", "Low", "Abnormal"]

                        row_class = "metric-row-alert" if is_flagged else "metric-row-normal"
                        badge_class = "badge-alert-dark" if is_flagged else "badge-normal-dark"
                        val_class = "val-highlight-alert" if is_flagged else "val-highlight-normal"
                        badge_label = f"⚠️ {status_raw.upper()}" if is_flagged else "✅ NORMAL"

                        metric_row_html = f"""
<div class="{row_class}">
    <div class="metric-header-row">
        <span class="metric-title-text">{m.get('name', 'Metric')}</span>
        <span class="{badge_class}">{badge_label}</span>
    </div>
    <div class="metric-values-row">
        <div>
            <span class="ref-range-text">Patient Value: </span>
            <span class="{val_class}">{m.get('value', 'N/A')}</span>
        </div>
        <div>
            <span class="ref-range-text">Standard Reference Range: </span>
            <strong style="color: #E6EDF3;">{m.get('reference_range', 'N/A')}</strong>
        </div>
    </div>
    <div class="metric-explanation-box">
        💡 <strong>Clinical Context:</strong> {m.get('explanation', '')}
    </div>
</div>
"""
                        render_html(metric_row_html)

        with tab_flagged:
            with st.container():
                # ================= 3. THIRD SECTION: FLAGGED / OUT-OF-RANGE VALUES =================
                render_html('<div class="section-header">⚠️ Flagged / Out-of-Range Values</div>')
                render_html('<div class="section-subtext">Dedicated clinical callout of metrics requiring attention and doctor discussion</div>')

                if is_attention_needed:
                    flagged_items_html = ""
                    for fm in flagged_metrics:
                        status_text = str(fm.get("status", "Abnormal")).upper()
                        flagged_items_html += f"""
<div class="flagged-item-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <strong style="color: #FFFFFF; font-size: 1.05rem;">{fm.get('name')}</strong>
        <span class="badge-alert-dark">⚠️ {status_text}</span>
    </div>
    <div style="margin-bottom: 8px;">
        <span style="color: #FF7B72; font-weight: 700; font-size: 1.15rem;">{fm.get('value')}</span>
        <span style="color: #8B949E; font-size: 0.85rem; margin-left: 12px;">(Standard Range: {fm.get('reference_range')})</span>
    </div>
    <div style="color: #E6EDF3; font-size: 0.9rem; line-height: 1.5;">
        {fm.get('explanation')}
    </div>
</div>
"""

                    container_html = f"""
<div class="flagged-callout-container">
    <div style="color: #FF7B72; font-size: 1.1rem; font-weight: 700; margin-bottom: 8px;">
        ⚠️ Attention Required: {len(flagged_metrics)} Metric(s) Outside Standard Bounds
    </div>
    <div style="color: #E6EDF3; font-size: 0.92rem; margin-bottom: 14px;">
        The following parameters are out of normal ranges. Be sure to review these specific findings with your healthcare provider.
    </div>
    {flagged_items_html}
</div>
"""
                    render_html(container_html)
                else:
                    normal_all_html = """
<div class="normal-all-container">
    <div style="color: #3FB950; font-size: 1.1rem; font-weight: 700; margin-bottom: 6px;">
        ✅ No Flagged Parameters Detected
    </div>
    <div style="color: #E6EDF3; font-size: 0.92rem;">
        All identified tests and metrics in this report fall securely within normal clinical bounds. Continue maintaining your current healthy habits.
    </div>
</div>
"""
                    render_html(normal_all_html)

        with tab_doctor:
            with st.container():
                # ================= 4. FOURTH SECTION: DOCTOR PREP CHECKLIST =================
                render_html('<div class="section-header">🩺 Doctor Consultation Checklist</div>')
                render_html('<div class="section-subtext">Select key questions to prepare for your medical consultation</div>')

                selected_questions = []
                with st.container():
                    doc_header_html = """
<div style="background-color: #1E222B; border: 1px solid #30363D; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
    <div style="color: #00E5FF; font-weight: 700; font-size: 1rem; margin-bottom: 8px;">
        Recommended Consultation Inquiries
    </div>
    <div style="color: #8B949E; font-size: 0.88rem; margin-bottom: 12px;">
        Select the questions you would like to discuss with your physician during your next visit:
    </div>
</div>
"""
                    render_html(doc_header_html)

                    for q_idx, question in enumerate(doctor_questions, start=1):
                        checked = st.checkbox(
                            f"**Q{q_idx}:** {question}",
                            value=True,
                            key=f"dark_q_{q_idx}",
                        )
                        if checked:
                            selected_questions.append(question)

                    # Generate Checklist Text
                    checklist_lines = [
                        "==================================================================",
                        "        🩺 MedTranslate AI - Doctor Consultation Checklist       ",
                        "==================================================================",
                        f"Target Language: {lang}",
                        "",
                        "1. EXECUTIVE SUMMARY:",
                        f"   {summary_text}",
                        "",
                        "2. SELECTED QUESTIONS FOR YOUR PHYSICIAN:",
                    ]
                    if selected_questions:
                        for s_idx, sq in enumerate(selected_questions, 1):
                            checklist_lines.append(f"   [ ] Q{s_idx}: {sq}")
                    else:
                        checklist_lines.append("   (No questions selected)")

                    checklist_lines.append("")
                    checklist_lines.append("3. FLAGGED / OUT-OF-RANGE METRICS TO REVIEW:")
                    if flagged_metrics:
                        for fm in flagged_metrics:
                            checklist_lines.append(
                                f"   • {fm.get('name')}: {fm.get('value')} (Standard: {fm.get('reference_range')}) - [{fm.get('status')}]"
                            )
                            checklist_lines.append(f"     Context: {fm.get('explanation')}")
                    else:
                        checklist_lines.append("   • All analyzed parameters were within normal reference ranges.")

                    checklist_lines.extend(
                        [
                            "",
                            "==================================================================",
                            "DISCLAIMER: This checklist is intended for communication and",
                            "educational assistance only. It does not replace professional",
                            "medical diagnosis, clinical advice, or treatment.",
                            "==================================================================",
                        ]
                    )
                    checklist_content = "\n".join(checklist_lines)

                    render_html("<div style='height: 8px;'></div>")
                    st.download_button(
                        label="📥 Download Doctor Questions Checklist (.txt)",
                        data=checklist_content,
                        file_name=f"medtranslate_doctor_checklist_{lang.lower()}.txt",
                        mime="text/plain",
                        use_container_width=True,
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
