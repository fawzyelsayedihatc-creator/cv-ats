import os
import re
import json
import sqlite3
import datetime
from io import BytesIO
import pdfplumber
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="CV ATS Professional Analyzer - Dr. Fawzy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS المحدث لتوضيح الخط داخل الأزرار
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
        background-color: #F8FAFC;
    }
    .stApp { background-color: #F8FAFC; }

    /* --- 🌿 تنسيق القائمة الجانبية (Sidebar) --- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #064E3B 0%, #047857 50%, #059669 100%) !important;
        padding-top: 1rem;
    }
    
    /* النصوص والتحكم في العناوين داخل السايدبار */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #FACC15 !important; /* لون ذهبي مميز للرصيد */
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #E2E8F0 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    /* --- 🔘 إجبار الكتابة داخل الأزرار على الظهور باللون الأسود وبحجم كبير --- */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 12px 15px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
        width: 100% !important;
        display: block !important;
        margin-bottom: 8px !important;
        transition: all 0.3s ease-in-out !important;
        text-align: center !important;
    }

    [data-testid="stSidebar"] .stButton > button *,
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span {
        color: #000000 !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* تأثير الهوفر للأزرار */
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #F1F5F9 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2) !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover * {
        color: #047857 !important;
        -webkit-text-fill-color: #047857 !important;
    }

    /* زر الشحن الخاص بالواتساب */
    .whatsapp-btn {
        display: block !important;
        text-align: center !important;
        background: #FFFFFF !important;
        color: #15803D !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        padding: 12px 15px !important;
        border-radius: 10px !important;
        text-decoration: none !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
        border: 1px solid #E2E8F0 !important;
        transition: all 0.3s ease-in-out !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    .whatsapp-btn:hover {
        background-color: #F1F5F9 !important;
        color: #166534 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2) !important;
    }

    /* أزرار الصفحات الرئيسية */
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3) !important;
        width: 100% !important;
    }

    /* تقارير وكروت النتائج */
    .report-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        font-size: 18px !important;
        font-weight: 700 !important;
        line-height: 1.8 !important;
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. الالتقاط التلقائي للـ IP ---
def get_user_ip():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in headers:
            return headers["X-Real-IP"]
        elif "Remote-Addr" in headers:
            return headers["Remote-Addr"]
    except Exception:
        pass
    return "غير معروف (Proxy/Cloud)"

# --- 3. الثوابت وإعدادات الأمان ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
COINS_PER_CV = 20
INITIAL_FREE_COINS = 0

RAW_PRIVATE_KEY_NEW = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyRCwwZzFTebUs
7lNOlF3jshkeaNNdBoTLufVq0Ff19Q1dg08LwJVlwMJFq83VmrKMR8Vr7eDS2/o4
8W0aVviObxi6lXvXX+/rbKuu3SQ70XcfNK/KvQ5+8ZFK9AS8TZrQKy6l9wk/aZ/L
lgnih
