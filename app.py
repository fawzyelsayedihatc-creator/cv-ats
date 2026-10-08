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

# CSS التنسيق الخاص بالثيم
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
        background-color: #F8FAFC;
    }
    .stApp { background-color: #F8FAFC; }

    /* --- 🌿 القائمة الجانبية (Sidebar) --- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #064E3B 0%, #047857 50%, #059669 100%) !important;
        padding-top: 1rem;
    }
    
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
        color: #FACC15 !important;
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #E2E8F0 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    /* أزرار السايدبار */
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

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #F1F5F9 !important;
        transform: translateY(-2px) !important;
    }

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

    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        font-size
